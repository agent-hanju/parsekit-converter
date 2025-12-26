import logging
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from .converter import CONVERT_EXTENSIONS, IMAGE_EXTENSIONS, PDF_EXTENSIONS, convert_pdf_to_images, convert_to_pdf
from .exceptions import AppException, EmptyFileError, ErrorCode
from .models import ApiResponse, ConvertResponse, ImageConvertResponse, ImagePage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ParseKit Converter",
    description="LibreOffice-based document to PDF conversion API",
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle all application exceptions."""
    return JSONResponse(status_code=200, content=ApiResponse.error(exc.code, exc.message).model_dump())


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(status_code=200, content=ApiResponse.error(ErrorCode.INTERNAL_ERROR, "Internal server error").model_dump())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/supported-formats")
async def supported_formats():
    """Return list of supported file formats."""
    return {
        "convertible": sorted(CONVERT_EXTENSIONS),
        "passthrough": sorted(PDF_EXTENSIONS | IMAGE_EXTENSIONS),
    }


@app.post("/convert", response_model=ApiResponse[ConvertResponse])
async def convert_document(file: UploadFile = File(...)):
    """
    Convert document to PDF using LibreOffice.

    Supports: DOC, DOCX, PPT, PPTX, XLS, XLSX, HWP, HWPX, ODT, ODP, ODS.
    PDF and image files are returned as-is.

    Returns JSON with base64-encoded PDF content.
    """
    logger.info(f"Converting document: {file.filename}")

    content = await file.read()
    if not content:
        raise EmptyFileError("Empty file uploaded")

    filename = file.filename or "document"
    content_type = file.content_type or "application/octet-stream"

    pdf_bytes, was_converted = await convert_to_pdf(content, filename, content_type)

    import base64

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    output_filename = Path(filename).stem + ".pdf" if was_converted else filename

    result = ConvertResponse(
        filename=output_filename,
        content=pdf_base64,
        size=len(pdf_bytes),
        converted=was_converted,
    )

    logger.info(f"Converted {filename} -> {output_filename} ({len(pdf_bytes)} bytes, converted={was_converted})")
    return ApiResponse.success(data=result)


@app.post("/convert/raw")
async def convert_document_raw(file: UploadFile = File(...)):
    """
    Convert document to PDF and return raw PDF bytes.

    Same as /convert but returns binary PDF directly instead of JSON.
    """
    logger.info(f"Converting document (raw): {file.filename}")

    content = await file.read()
    if not content:
        raise EmptyFileError("Empty file uploaded")

    filename = file.filename or "document"
    content_type = file.content_type or "application/octet-stream"

    pdf_bytes, was_converted = await convert_to_pdf(content, filename, content_type)
    output_filename = Path(filename).stem + ".pdf" if was_converted else filename

    logger.info(f"Converted {filename} -> {output_filename} ({len(pdf_bytes)} bytes)")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{output_filename}"'},
    )


@app.post("/convert/images", response_model=ApiResponse[ImageConvertResponse])
async def convert_document_to_images(
    file: UploadFile = File(...),
    format: str = "png",
    dpi: int = 150,
):
    """
    Convert document to images (one per page).

    Supports: DOC, DOCX, PPT, PPTX, XLS, XLSX, HWP, HWPX, ODT, ODP, ODS, PDF, and images.
    Image files are returned as-is (single page).

    Parameters:
    - format: Output image format (png, jpg, webp). Default: png
    - dpi: Resolution in DPI. Default: 150

    Returns JSON with base64-encoded images for each page.
    """
    logger.info(f"Converting document to images: {file.filename}, format={format}, dpi={dpi}")

    content = await file.read()
    if not content:
        raise EmptyFileError("Empty file uploaded")

    filename = file.filename or "document"
    content_type = file.content_type or "application/octet-stream"
    ext = Path(filename).suffix.lower()

    import base64

    # Image files - return as-is (single page)
    if ext in IMAGE_EXTENSIONS or content_type.startswith("image/"):
        logger.info(f"Image file, returning as-is: {filename}")
        pages = [
            ImagePage(
                page=1,
                content=base64.b64encode(content).decode("utf-8"),
                size=len(content),
            )
        ]
        # Detect format from extension
        detected_format = ext.lstrip(".") if ext else "png"
        if detected_format == "jpeg":
            detected_format = "jpg"

        result = ImageConvertResponse(
            format=detected_format,
            pages=pages,
            total_pages=1,
        )
        return ApiResponse.success(data=result)

    # Convert to PDF first if needed
    pdf_bytes, _ = await convert_to_pdf(content, filename, content_type)

    # Then convert PDF to images
    image_bytes_list = await convert_pdf_to_images(pdf_bytes, format=format, dpi=dpi)

    pages = [
        ImagePage(
            page=i + 1,
            content=base64.b64encode(img_bytes).decode("utf-8"),
            size=len(img_bytes),
        )
        for i, img_bytes in enumerate(image_bytes_list)
    ]

    result = ImageConvertResponse(
        format=format,
        pages=pages,
        total_pages=len(pages),
    )

    logger.info(f"Converted {filename} to {len(pages)} {format} images")
    return ApiResponse.success(data=result)


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
