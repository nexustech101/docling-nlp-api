from fastapi import HTTPException


class DoclingAPIException(Exception):
    """Base exception for Docling API."""
    pass


class DocumentProcessingError(DoclingAPIException):
    """Exception raised during document processing."""
    pass


class DocumentConversionError(DoclingAPIException):
    """Exception raised during document conversion."""
    pass


class URLProcessingError(DoclingAPIException):
    """Exception raised during URL processing."""
    pass


class FileSizeError(DoclingAPIException):
    """Exception raised when file size exceeds limits."""
    pass


class UnsupportedFileTypeError(DoclingAPIException):
    """Exception raised for unsupported file types."""
    pass


def create_http_exception(exc: DoclingAPIException, status_code: int = 400) -> HTTPException:
    """Convert custom exception to HTTP exception."""
    return HTTPException(status_code=status_code, detail=str(exc))
