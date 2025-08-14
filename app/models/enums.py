from enum import Enum


class DocumentType(str, Enum):
    """Supported document input types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    HTML = "html"
    TXT = "txt"
    MD = "md"


class OutputFormat(str, Enum):
    """Supported output formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    JSON = "json"
    DOCTAGS = "doctags"


class ProcessingStatus(str, Enum):
    """Processing status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
