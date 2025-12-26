import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.converter import CONVERT_EXTENSIONS, IMAGE_EXTENSIONS, PDF_EXTENSIONS, convert_to_pdf, convert_with_libreoffice


class TestConvertToPdf:
    """Tests for the convert_to_pdf function."""

    @pytest.mark.asyncio
    async def test_pdf_file_returns_unchanged(self, sample_pdf_bytes):
        """PDF files should be returned unchanged."""
        result, was_converted = await convert_to_pdf(sample_pdf_bytes, "document.pdf", "application/pdf")

        assert result == sample_pdf_bytes
        assert was_converted is False

    @pytest.mark.asyncio
    async def test_pdf_by_content_type(self, sample_pdf_bytes):
        """Should detect PDF by content type."""
        result, was_converted = await convert_to_pdf(sample_pdf_bytes, "document", "application/pdf")

        assert result == sample_pdf_bytes
        assert was_converted is False

    @pytest.mark.asyncio
    async def test_image_file_returns_unchanged(self, sample_png_bytes):
        """Image files should be returned unchanged (passthrough)."""
        result, was_converted = await convert_to_pdf(sample_png_bytes, "image.png", "image/png")

        assert result == sample_png_bytes
        assert was_converted is False

    @pytest.mark.asyncio
    async def test_docx_triggers_libreoffice_conversion(self):
        """DOCX files should trigger LibreOffice conversion."""
        docx_content = b"PK\x03\x04..."  # Fake DOCX content

        with patch("app.converter.convert_with_libreoffice") as mock_convert:
            mock_convert.return_value = (b"PDF content", True)

            result, was_converted = await convert_to_pdf(docx_content, "document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            mock_convert.assert_called_once()
            assert was_converted is True


class TestConvertWithLibreOffice:
    """Tests for LibreOffice conversion."""

    @pytest.mark.asyncio
    async def test_successful_conversion(self, tmp_path):
        """Should successfully convert document to PDF."""
        # Create a mock subprocess result
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr=b"")

            # Create temporary PDF output
            with patch("os.path.exists", return_value=True), patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b"PDF content"

                result, was_converted = await convert_with_libreoffice(b"Document content", "test.docx")

                assert was_converted is True

    @pytest.mark.asyncio
    async def test_conversion_failure(self):
        """Should raise error when LibreOffice fails."""
        from app.exceptions import ConversionError

        with patch("app.converter.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr=b"LibreOffice error")

            with pytest.raises(ConversionError, match="LibreOffice conversion failed"):
                await convert_with_libreoffice(b"Content", "test.docx")

    @pytest.mark.asyncio
    async def test_conversion_timeout(self):
        """Should raise error on timeout."""
        from app.exceptions import ConversionTimeoutError

        with patch("app.converter.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="libreoffice", timeout=120)

            with pytest.raises(ConversionTimeoutError, match="timed out"):
                await convert_with_libreoffice(b"Content", "test.docx")


class TestFileExtensions:
    """Tests for file extension constants."""

    def test_convert_extensions_includes_office_formats(self):
        """Should include common office formats."""
        assert ".docx" in CONVERT_EXTENSIONS
        assert ".doc" in CONVERT_EXTENSIONS
        assert ".pptx" in CONVERT_EXTENSIONS
        assert ".ppt" in CONVERT_EXTENSIONS
        assert ".xlsx" in CONVERT_EXTENSIONS
        assert ".xls" in CONVERT_EXTENSIONS

    def test_convert_extensions_includes_hwp(self):
        """Should include Korean document formats."""
        assert ".hwp" in CONVERT_EXTENSIONS
        assert ".hwpx" in CONVERT_EXTENSIONS

    def test_pdf_extensions(self):
        """Should include PDF extension."""
        assert ".pdf" in PDF_EXTENSIONS

    def test_image_extensions(self):
        """Should include common image formats."""
        assert ".png" in IMAGE_EXTENSIONS
        assert ".jpg" in IMAGE_EXTENSIONS
        assert ".jpeg" in IMAGE_EXTENSIONS
        assert ".gif" in IMAGE_EXTENSIONS
        assert ".bmp" in IMAGE_EXTENSIONS
        assert ".tiff" in IMAGE_EXTENSIONS
        assert ".webp" in IMAGE_EXTENSIONS
