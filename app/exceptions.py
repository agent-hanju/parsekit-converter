"""Custom exceptions and error codes for parsekit-converter."""


class ErrorCode:
    """Error code definitions."""

    # 1xx: 입력 검증
    EMPTY_FILE = 101

    # 2xx: 파일 변환 (LibreOffice)
    CONVERSION_FAILED = 201
    CONVERSION_OUTPUT_NOT_FOUND = 202
    CONVERSION_TIMEOUT = 203
    LIBREOFFICE_NOT_FOUND = 204

    # 3xx: 이미지 변환 (Poppler)
    IMAGE_CONVERSION_FAILED = 301
    POPPLER_NOT_FOUND = 302

    # 5xx: 시스템
    INTERNAL_ERROR = 501


# Base exception
class AppException(Exception):
    """Base exception for application errors."""

    code: int = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# 1xx: 입력 검증
class EmptyFileError(AppException):
    code = ErrorCode.EMPTY_FILE


# 2xx: 파일 변환
class ConversionError(AppException):
    """Base class for conversion errors."""

    code = ErrorCode.CONVERSION_FAILED


class ConversionOutputNotFoundError(ConversionError):
    code = ErrorCode.CONVERSION_OUTPUT_NOT_FOUND


class ConversionTimeoutError(ConversionError):
    code = ErrorCode.CONVERSION_TIMEOUT


class LibreOfficeNotFoundError(ConversionError):
    code = ErrorCode.LIBREOFFICE_NOT_FOUND


# 3xx: 이미지 변환
class ImageConversionError(AppException):
    """Base class for image conversion errors."""

    code = ErrorCode.IMAGE_CONVERSION_FAILED


class PopplerNotFoundError(ImageConversionError):
    code = ErrorCode.POPPLER_NOT_FOUND
