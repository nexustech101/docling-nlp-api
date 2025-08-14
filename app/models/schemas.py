from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from .enums import OutputFormat, ProcessingStatus


class DocumentUploadRequest(BaseModel):
    """Schema for document upload request."""
    dest_format: OutputFormat = Field(..., description="Desired output format")
    use_ocr: bool = Field(
        default=False, description="Enable OCR for scanned documents")

    class Config:
        schema_extra = {
            "example": {
                "dest_format": "markdown",
                "use_ocr": False
            }
        }


class URLProcessRequest(BaseModel):
    """Schema for URL processing request."""
    url: HttpUrl = Field(..., description="URL to process")
    dest_format: OutputFormat = Field(..., description="Desired output format")
    use_ocr: bool = Field(
        default=False, description="Enable OCR for scanned documents")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/document.pdf",
                "dest_format": "markdown",
                "use_ocr": False
            }
        }


class ProcessingResponse(BaseModel):
    """Schema for processing response."""
    status: ProcessingStatus
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "content": "# Document Title\n\nDocument content...",
                "metadata": {"page_count": 5, "word_count": 1250},
                "processing_time": 2.5,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = "healthy"
    version: str
    uptime: float
    docling_available: bool
