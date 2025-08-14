from pathlib import Path
from typing import Optional
from functools import lru_cache

from ..utils.file_utils import download_from_url, validate_file_extension, cleanup_file
from ..core.exceptions import URLProcessingError
from ..models.enums import OutputFormat
from ..models.schemas import ProcessingResponse
from .docling_service import get_docling_service
from ..utils.logger import setup_logger
from ..core.config.config import get_settings

settings = get_settings()
logger = setup_logger(__name__, settings.log_level)


class URLService:
    """Service for processing documents from URLs."""

    def __init__(self):
        self.docling_service = get_docling_service()

    async def process_url(
        self,
        url: str,
        output_format: OutputFormat,
        use_ocr: bool = False
    ) -> ProcessingResponse:
        """Download and process document from URL."""
        temp_file: Optional[Path] = None

        try:
            logger.info(f"Processing document from URL: {url}")

            # Download file from URL
            temp_file = await download_from_url(url)

            # Validate file type
            validate_file_extension(temp_file.name)

            # Process with DoclingService
            result = await self.docling_service.process_document(
                temp_file, output_format, use_ocr
            )

            # Add URL to metadata
            if result.metadata:
                result.metadata["source_url"] = url
            else:
                result.metadata = {"source_url": url}

            return result

        except Exception as e:
            logger.error(f"URL processing failed for {url}: {str(e)}")
            raise URLProcessingError(f"Failed to process URL: {str(e)}")

        finally:
            # Cleanup downloaded file
            if temp_file:
                cleanup_file(temp_file)


@lru_cache(maxsize=1)
def get_url_service() -> URLService:
    """Get cached URLService instance."""
    return URLService()
