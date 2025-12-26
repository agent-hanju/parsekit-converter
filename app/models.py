from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """표준 API 응답 래퍼"""

    code: int = 0
    message: str | None = None
    data: T | None = None

    @classmethod
    def success(cls, data: T, message: str | None = None) -> "ApiResponse[T]":
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str) -> "ApiResponse":
        return cls(code=code, message=message, data=None)


class ConvertResponse(BaseModel):
    """PDF 변환 결과"""

    filename: str
    content: str  # base64-encoded PDF
    size: int
    converted: bool  # True if conversion happened, False if passthrough


class ImagePage(BaseModel):
    """이미지 페이지"""

    page: int
    content: str  # base64-encoded image
    size: int


class ImageConvertResponse(BaseModel):
    """이미지 변환 결과"""

    format: str
    pages: list[ImagePage]
    total_pages: int
