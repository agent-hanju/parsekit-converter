from unittest.mock import patch

from app.exceptions import ErrorCode


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_ok(self, client):
        """Health endpoint should return status ok."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSupportedFormatsEndpoint:
    """Tests for the /supported-formats endpoint."""

    def test_returns_format_lists(self, client):
        """Should return convertible and passthrough format lists."""
        response = client.get("/supported-formats")

        assert response.status_code == 200
        data = response.json()
        assert "convertible" in data
        assert "passthrough" in data
        assert ".docx" in data["convertible"]
        assert ".pdf" in data["passthrough"]


class TestConvertEndpoint:
    """Tests for the /convert endpoint."""

    def test_convert_empty_file_returns_error(self, client):
        """Converting empty file should return error code."""
        response = client.post(
            "/convert",
            files={"file": ("test.docx", b"", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == ErrorCode.EMPTY_FILE
        assert "Empty file" in data["message"]

    def test_convert_pdf_returns_passthrough(self, client, sample_pdf_bytes):
        """PDF files should be returned unchanged."""
        response = client.post(
            "/convert",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["converted"] is False
        assert data["data"]["filename"] == "test.pdf"

    def test_convert_image_returns_passthrough(self, client, sample_png_bytes):
        """Image files should be returned unchanged."""
        response = client.post(
            "/convert",
            files={"file": ("image.png", sample_png_bytes, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["converted"] is False

    def test_convert_docx_triggers_libreoffice(self, client):
        """DOCX files should trigger LibreOffice conversion."""
        docx_content = b"PK\x03\x04..."  # Fake DOCX

        with patch("app.converter.convert_with_libreoffice") as mock_convert:
            mock_convert.return_value = (b"PDF content", True)

            response = client.post(
                "/convert",
                files={"file": ("doc.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["converted"] is True
            assert data["data"]["filename"] == "doc.pdf"


class TestConvertRawEndpoint:
    """Tests for the /convert/raw endpoint."""

    def test_convert_raw_returns_pdf_bytes(self, client, sample_pdf_bytes):
        """Should return raw PDF bytes."""
        response = client.post(
            "/convert/raw",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]

    def test_convert_raw_empty_file_returns_error(self, client):
        """Converting empty file should return error."""
        response = client.post(
            "/convert/raw",
            files={"file": ("test.pdf", b"", "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == ErrorCode.EMPTY_FILE


class TestConvertImagesEndpoint:
    """Tests for the /convert/images endpoint (NDJSON streaming)."""

    def test_convert_images_empty_file_returns_error(self, client):
        """Converting empty file should return error."""
        response = client.post(
            "/convert/images",
            files={"file": ("test.pdf", b"", "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == ErrorCode.EMPTY_FILE

    def test_convert_images_with_format_param(self, client, sample_pdf_bytes):
        """Should accept format parameter and return NDJSON stream."""
        import json

        with patch("app.main.convert_pdf_to_images_generator") as mock_convert:
            # Generator yields (page_num, image_bytes, total_pages)
            mock_convert.return_value = iter([(1, b"fake image data", 1)])

            response = client.post(
                "/convert/images?format=jpg&dpi=300",
                files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"

            # Parse NDJSON response
            lines = response.text.strip().split("\n")
            assert len(lines) == 1
            page_data = json.loads(lines[0])
            assert page_data["page"] == 1
            assert page_data["total_pages"] == 1

    def test_convert_images_passthrough_image(self, client, sample_png_bytes):
        """Image files should be returned as-is in NDJSON format."""
        import json

        response = client.post(
            "/convert/images",
            files={"file": ("test.png", sample_png_bytes, "image/png")},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-ndjson"

        # Parse NDJSON response
        lines = response.text.strip().split("\n")
        assert len(lines) == 1
        page_data = json.loads(lines[0])
        assert page_data["page"] == 1
        assert page_data["total_pages"] == 1
