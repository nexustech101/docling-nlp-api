import aiofiles
import aiohttp
from pathlib import Path
from typing import BinaryIO, Optional
import tempfile
import hashlib
from ..core.config.config import get_settings
from ..core.exceptions import FileSizeError, UnsupportedFileTypeError, URLProcessingError
from ..utils.logger import setup_logger

settings = get_settings()
logger = setup_logger(__name__, settings.log_level)


async def save_upload_file(file: BinaryIO, filename: str) -> Path:
    """Save uploaded file to temporary directory."""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)

    # Generate unique filename to avoid conflicts
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    safe_filename = f"{file_hash}_{filename}"
    file_path = upload_dir / safe_filename

    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = file.read()

            # Check file size
            if len(content) > settings.max_file_size:
                raise FileSizeError(
                    f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
                )

            await f.write(content)

        logger.info(f"File saved: {file_path}")
        return file_path

    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise e


async def download_from_url(url: str) -> Path:
    """Download file from URL and save to temporary location."""
    temp_dir = Path(settings.upload_dir)
    temp_dir.mkdir(exist_ok=True)

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.url_timeout)
        ) as session:
            with session.get(url) as response:
                response.raise_for_status()

                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > settings.max_url_file_size:
                    raise FileSizeError(
                        f"URL file size exceeds maximum allowed size of {settings.max_url_file_size} bytes"
                    )

                # Determine filename from URL or content-disposition
                filename = get_filename_from_response(response, url)

                # Create temporary file
                file_path = temp_dir / \
                    f"url_download_{hashlib.md5(url.encode()).hexdigest()[:8]}_{filename}"

                async with aiofiles.open(file_path, 'wb') as f:
                    downloaded_size = 0
                    async for chunk in response.content.iter_chunked(8192):
                        downloaded_size += len(chunk)

                        # Check size during download
                        if downloaded_size > settings.max_url_file_size:
                            raise FileSizeError(
                                f"URL file size exceeds maximum allowed size during download"
                            )

                        await f.write(chunk)

                logger.info(f"File downloaded from URL: {url} -> {file_path}")
                return file_path

    except aiohttp.ClientError as e:
        raise URLProcessingError(f"Failed to download from URL: {e}")


def get_filename_from_response(response: aiohttp.ClientResponse, url: str) -> str:
    """Extract filename from response headers or URL."""
    # Try content-disposition header first
    content_disposition = response.headers.get('content-disposition', '')
    if 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[1].strip('"')
        return filename

    # Fall back to URL path
    return Path(url).name or "downloaded_file"


def validate_file_extension(filename: str) -> None:
    """Validate file extension against allowed types."""
    file_ext = Path(filename).suffix.lower()
    if file_ext not in settings.allowed_extensions:
        raise UnsupportedFileTypeError(
            f"File type {file_ext} not supported. Allowed types: {settings.allowed_extensions}"
        )


def cleanup_file(file_path: Path) -> None:
    """Safely remove file."""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")
