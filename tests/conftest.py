import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_pdf_bytes():
    """Return minimal PDF bytes for testing."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""


@pytest.fixture
def sample_png_bytes():
    """Return minimal PNG bytes for testing."""
    return bytes(
        [
            0x89,
            0x50,
            0x4E,
            0x47,
            0x0D,
            0x0A,
            0x1A,
            0x0A,  # PNG signature
            0x00,
            0x00,
            0x00,
            0x0D,  # IHDR chunk length
            0x49,
            0x48,
            0x44,
            0x52,  # IHDR
            0x00,
            0x00,
            0x00,
            0x01,  # width: 1
            0x00,
            0x00,
            0x00,
            0x01,  # height: 1
            0x08,
            0x06,  # bit depth, color type
            0x00,
            0x00,
            0x00,  # compression, filter, interlace
            0x1F,
            0x15,
            0xC4,
            0x89,  # CRC
            0x00,
            0x00,
            0x00,
            0x0A,  # IDAT chunk length
            0x49,
            0x44,
            0x41,
            0x54,  # IDAT
            0x78,
            0x9C,
            0x63,
            0x00,
            0x01,
            0x00,
            0x00,
            0x05,
            0x00,
            0x01,  # data
            0x0D,
            0x0A,
            0x2D,
            0xB4,  # CRC
            0x00,
            0x00,
            0x00,
            0x00,  # IEND chunk length
            0x49,
            0x45,
            0x4E,
            0x44,  # IEND
            0xAE,
            0x42,
            0x60,
            0x82,  # CRC
        ]
    )
