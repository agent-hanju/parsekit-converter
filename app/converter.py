import logging
import os
import subprocess
import tempfile
from pathlib import Path

from .exceptions import (
    ConversionError,
    ConversionOutputNotFoundError,
    ConversionTimeoutError,
    LibreOfficeNotFoundError,
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
