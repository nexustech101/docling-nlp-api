from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
from pathlib import Path
from functools import lru_cache
from enum import Enum
import json
import shutil
import logging
from docling.document_converter import DocumentConverter

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Docling PDF API")

# Temporary upload folder
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Enum for document types
class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MD = "md"
    MARKDOWN = "markdown"
    TXT = "txt"
    TEXT = "text"
    JSON = "json"
    DOCTAGS = "doctags"
    DOC = "doc"


class DocumentConversionError(Exception):
    """Custom exception for document conversion errors."""
    pass


# Cache Docling model
@lru_cache(maxsize=1)
def get_converter() -> DocumentConverter:
    logger.info("Loading DocumentConverter model into memory...")
    return DocumentConverter()


def process_document(file_path: Path, use_ocr: bool = False):
    """Return DoclingDocument object"""
    if not file_path.exists():
        raise DocumentConversionError(f"File does not exist: {file_path}")

    converter = get_converter()
    try:
        # OCR can be added if supported
        result = converter.convert(str(file_path))
    except TypeError:
        result = converter.convert_single(str(file_path))
    return result.document


def convert_to_type(doc, dest_type: DocumentType) -> str:
    """Convert DoclingDocument to desired output type"""
    if dest_type in (DocumentType.MD, DocumentType.MARKDOWN):
        return doc.export_to_markdown()
    elif dest_type == DocumentType.HTML:
        return doc.export_to_html()
    elif dest_type in (DocumentType.TXT, DocumentType.TEXT):
        return doc.export_to_text()
    elif dest_type == DocumentType.DOCTAGS:
        return doc.export_to_doctags()
    elif dest_type == DocumentType.JSON:
        return json.dumps(doc.export_to_dict(), indent=2)
    else:
        raise DocumentConversionError(
            f"Unsupported destination type: {dest_type}")
        

def convert_from_url(url: str):
    pass


@app.post("/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    dest_type: DocumentType = Form(...),
    use_ocr: bool = Form(False)
):
    """
    Upload a document and return it in the requested format.
    :param file: Uploaded file
    :param dest_type: Desired output format
    :param use_ocr: Enable OCR for scanned documents
    """
    temp_file_path = UPLOAD_DIR / file.filename
    try:
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Process document
        doc = process_document(temp_file_path, use_ocr)

        # Convert to requested format
        content = convert_to_type(doc, dest_type)

        # Return proper response type
        if dest_type == DocumentType.HTML:
            return HTMLResponse(content=content)
        elif dest_type in (DocumentType.TXT, DocumentType.TEXT, DocumentType.MD, DocumentType.MARKDOWN, DocumentType.DOCTAGS):
            return PlainTextResponse(content=content)
        elif dest_type == DocumentType.JSON:
            return JSONResponse(content=json.loads(content))
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported destination type")

    except DocumentConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        # Cleanup temp file
        if temp_file_path.exists():
            temp_file_path.unlink()


@app.post("/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    dest_type: DocumentType = Form(...),
    use_ocr: bool = Form(False)
):
    """
    Upload a document and return it in the requested format.
    :param file: Uploaded file
    :param dest_type: Desired output format
    :param use_ocr: Enable OCR for scanned documents
    """
    temp_file_path = UPLOAD_DIR / file.filename
    try:
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Process document
        doc = process_document(temp_file_path, use_ocr)

        # Convert to requested format
        content = convert_to_type(doc, dest_type)

        # Return proper response type
        if dest_type == DocumentType.HTML:
            return HTMLResponse(content=content)
        elif dest_type in (DocumentType.TXT, DocumentType.TEXT, DocumentType.MD, DocumentType.MARKDOWN, DocumentType.DOCTAGS):
            return PlainTextResponse(content=content)
        elif dest_type == DocumentType.JSON:
            return JSONResponse(content=json.loads(content))
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported destination type")

    except DocumentConversionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        # Cleanup temp file
        if temp_file_path.exists():
            temp_file_path.unlink()
