from fastapi import APIRouter, Depends, UploadFile, HTTPException, Form
from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
import json
from pathlib import Path

from ...models.enums import OutputFormat
from ...models.schemas import ProcessingResponse, URLProcessRequest, ErrorResponse
from ...services.docling_service import DoclingService
from ...services.url_service import URLService
from ...utils.file_utils import save_upload_file, cleanup_file
from ..dependencies import validate_upload_file, get_docling_dependency, get_url_dependency
from ...core.exceptions import DoclingAPIException, create_http_exception
from ...utils.logger import setup_logger
from ...core.config.config import get_settings

settings = get_settings()
logger = setup_logger(__name__, settings.log_level)

router = APIRouter(
    prefix="/documents", 
    tags=["documents"]
)


@router.post("/upload", response_model=ProcessingResponse)
async def upload_document(
    file: UploadFile = Depends(validate_upload_file),
    dest_format: OutputFormat = Form(...),
    use_ocr: bool = Form(False),
    docling_service: DoclingService = Depends(get_docling_dependency)
):
    """
    Upload and process a document.
    
    - **file**: Document file to process
    - **dest_format**: Desired output format (markdown, html, text, json, doctags)
    - **use_ocr**: Enable OCR for scanned documents
    """
    temp_file: Path = None

    try:
        # Save uploaded file
        temp_file = await save_upload_file(file.file, file.filename)

        # Process document
        result = await docling_service.process_document(
            temp_file, dest_format, use_ocr
        )

        # Return appropriate response format
        match dest_format:
            case OutputFormat.HTML:
                return HTMLResponse(content=result.content)
            case [OutputFormat.TEXT, OutputFormat.MARKDOWN, OutputFormat.DOCTAGS]:
                return PlainTextResponse(content=result.content)
            case OutputFormat.JSON:
                return JSONResponse(content=json.loads(result.content))
            case _:
                return result

    except DoclingAPIException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        # Cleanup
        if temp_file:
            cleanup_file(temp_file)


@router.post("/process-url", response_model=ProcessingResponse)
async def process_url(
    request: URLProcessRequest,
    url_service: URLService = Depends(get_url_dependency)
):
    """
    Process a document from URL.
    
    - **url**: URL of the document to process
    - **dest_format**: Desired output format
    - **use_ocr**: Enable OCR for scanned documents
    """
    try:
        result = await url_service.process_url(
            str(request.url), request.dest_format, request.use_ocr
        )

        # Return appropriate response format
        match request.dest_format:
            case OutputFormat.HTML:
                return HTMLResponse(content=result.content)
            case [OutputFormat.TEXT, OutputFormat.MARKDOWN, OutputFormat.DOCTAGS]:
                return PlainTextResponse(content=result.content)
            case OutputFormat.JSON:
                return JSONResponse(content=json.loads(result.content))
            case _:
                return result

    except DoclingAPIException as e:
        raise create_http_exception(e)
    except Exception as e:
        logger.error(f"Unexpected error processing URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
