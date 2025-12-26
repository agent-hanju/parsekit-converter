import io
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

from pdf2image import convert_from_bytes, convert_from_path, pdfinfo_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError

from .exceptions import (
    ConversionError,
    ConversionOutputNotFoundError,
    ConversionTimeoutError,
    ImageConversionError,
    LibreOfficeNotFoundError,
    PopplerNotFoundError,
)

logger = logging.getLogger(__name__)

# File extensions that need conversion to PDF
CONVERT_EXTENSIONS = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".hwp", ".hwpx", ".odt", ".odp", ".ods"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}


async def convert_to_pdf(content: bytes, filename: str, content_type: str) -> tuple[bytes, bool]:
    """
    Convert document to PDF if needed.
    Returns (pdf_bytes, was_converted).
    """
    ext = Path(filename).suffix.lower()

    # Already PDF
    if ext in PDF_EXTENSIONS or content_type == "application/pdf":
        logger.debug(f"File is already PDF: {filename}")
        return content, False

    # Image files - return as-is for VLM processing
    if ext in IMAGE_EXTENSIONS or content_type.startswith("image/"):
        logger.debug(f"Image file, no conversion needed: {filename}")
        return content, False

    # Office files (including HWP) - use LibreOffice
    if ext in CONVERT_EXTENSIONS:
        return await convert_with_libreoffice(content, filename)

    # Unknown format - try LibreOffice anyway
    logger.warning(f"Unknown format, attempting LibreOffice conversion: {filename}")
    return await convert_with_libreoffice(content, filename)


async def convert_with_libreoffice(content: bytes, filename: str) -> tuple[bytes, bool]:
    """Convert document to PDF using LibreOffice headless."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, filename)
        with open(input_path, "wb") as f:
            f.write(content)

        try:
            result = subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", tmpdir, input_path], capture_output=True, timeout=120)
        except FileNotFoundError:
            logger.error("LibreOffice is not installed")
            raise LibreOfficeNotFoundError("LibreOffice is not installed")
        except subprocess.TimeoutExpired:
            logger.error(f"LibreOffice conversion timed out: {filename}")
            raise ConversionTimeoutError("LibreOffice conversion timed out")

        if result.returncode != 0:
            error_msg = result.stderr.decode()
            logger.error(f"LibreOffice conversion failed: {error_msg}")
            raise ConversionError(f"LibreOffice conversion failed: {error_msg}")

        # Find the output PDF
        pdf_filename = Path(filename).stem + ".pdf"
        pdf_path = os.path.join(tmpdir, pdf_filename)

        if not os.path.exists(pdf_path):
            logger.error(f"PDF output not found: {pdf_path}")
            raise ConversionOutputNotFoundError(f"Conversion completed but output file not found: {pdf_path}")

        with open(pdf_path, "rb") as f:
            pdf_content = f.read()

        logger.info(f"Converted {filename} to PDF ({len(pdf_content)} bytes)")
        return pdf_content, True


def convert_pdf_to_images_generator(
    pdf_path: str,
    format: str = "png",
    dpi: int = 150,
) -> Generator[tuple[int, bytes, int], None, None]:
    """
    Convert PDF to images using generator (memory efficient).
    Yields (page_number, image_bytes, total_pages) tuples one at a time.
    """
    pil_format = format.upper()
    if pil_format == "JPG":
        pil_format = "JPEG"

    try:
        info = pdfinfo_from_path(pdf_path)
        total_pages = info["Pages"]
    except PDFInfoNotInstalledError:
        logger.error("Poppler is not installed")
        raise PopplerNotFoundError("Poppler is not installed")
    except Exception as e:
        logger.error(f"Failed to get PDF info: {e}")
        raise ImageConversionError(f"Failed to get PDF info: {e}")

    try:
        for page_num in range(1, total_pages + 1):
            # Convert one page at a time
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=page_num,
                last_page=page_num,
            )

            if images:
                buffer = io.BytesIO()
                images[0].save(buffer, format=pil_format)
                image_bytes = buffer.getvalue()
                buffer.close()
                images[0].close()

                logger.debug(f"Converted page {page_num}/{total_pages} to {format}")
                yield page_num, image_bytes, total_pages

    except PDFPageCountError as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise ImageConversionError(f"Failed to convert PDF to images: {e}")
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise ImageConversionError(f"Failed to convert PDF to images: {e}")


async def convert_pdf_to_images(
    pdf_bytes: bytes,
    format: str = "png",
    dpi: int = 150,
) -> list[bytes]:
    """
    Convert PDF to images.
    Returns list of image bytes (one per page).

    Note: For memory efficiency with large PDFs, use convert_pdf_to_images_generator instead.
    """
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
    except PDFInfoNotInstalledError:
        logger.error("Poppler is not installed")
        raise PopplerNotFoundError("Poppler is not installed")
    except PDFPageCountError as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise ImageConversionError(f"Failed to convert PDF to images: {e}")
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise ImageConversionError(f"Failed to convert PDF to images: {e}")

    result = []
    pil_format = format.upper()
    if pil_format == "JPG":
        pil_format = "JPEG"

    for i, image in enumerate(images):
        buffer = io.BytesIO()
        image.save(buffer, format=pil_format)
        result.append(buffer.getvalue())
        logger.debug(f"Converted page {i + 1} to {format}")

    logger.info(f"Converted PDF to {len(result)} {format} images")
    return result
