from functools import lru_cache
from pathlib import Path
from re import match
from typing import Optional, Dict, Any
import time
import json
import os
from docling.document_converter import DocumentConverter

from ..core.config.config import get_settings
from ..core.exceptions import DocumentProcessingError, DocumentConversionError
from ..models.enums import OutputFormat
from ..models.schemas import ProcessingResponse, ProcessingStatus
from ..utils.logger import setup_logger
from ..middleware.analytics_middleware import get_document_tracker

settings = get_settings()
logger = setup_logger(__name__, settings.log_level)


class DoclingService:
    """Service class for handling Docling operations."""

    def __init__(self):
        self._converter: Optional[DocumentConverter] = None

    @property
    def converter(self) -> DocumentConverter:
        """Lazy-loaded DocumentConverter instance."""
        if self._converter is None:
            logger.info("Initializing DocumentConverter...")
            self._converter = DocumentConverter()
            logger.info("DocumentConverter initialized successfully")
        return self._converter

    async def process_document(
        self,
        file_path: Path,
        output_format: OutputFormat,
        use_ocr: bool = False
    ) -> ProcessingResponse:
        """Process document and return in requested format."""
        start_time = time.time()

        try:
            if not file_path.exists():
                raise DocumentProcessingError(
                    f"File does not exist: {file_path}")

            logger.info(f"Processing document: {file_path}")

            # Convert document
            try:
                result = self.converter.convert(str(file_path))
                doc = result.document
            except TypeError:
                # Fallback for older versions
                result = self.converter.convert_single(str(file_path))
                doc = result.document
            except Exception as e:
                raise DocumentProcessingError(
                    f"Failed to convert document: {str(e)}")

            # Convert to requested format
            content = self._convert_to_format(doc, output_format)

            # Extract metadata
            metadata = self._extract_metadata(doc)

            processing_time = time.time() - start_time

            logger.info(
                f"Document processed successfully in {processing_time:.2f}s")

            return ProcessingResponse(
                status=ProcessingStatus.COMPLETED,
                content=content,
                metadata=metadata,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Document processing failed after {processing_time:.2f}s: {str(e)}")

            return ProcessingResponse(
                status=ProcessingStatus.FAILED,
                metadata={"error": str(e)},
                processing_time=processing_time
            )

    async def process_document_with_analytics(
        self,
        file_path: Path,
        output_format: OutputFormat,
        user_id: str,
        use_ocr: bool = False
    ) -> ProcessingResponse:
        """Process document with analytics tracking."""
        start_time = time.time()
        file_size = 0
        document_type = "unknown"
        success = False
        pages_processed = 0
        words_extracted = 0
        error_message = None

        try:
            # Get file information
            if file_path.exists():
                file_size = os.path.getsize(file_path)
                document_type = file_path.suffix.lower().lstrip('.')

            # Process the document
            response = await self.process_document(file_path, output_format, use_ocr)
            
            # Extract analytics data from response
            if response.status == ProcessingStatus.COMPLETED:
                success = True
                if response.metadata:
                    pages_processed = response.metadata.get('page_count', 0)
                    words_extracted = response.metadata.get('word_count', 0)
            else:
                error_message = response.metadata.get('error', 'Unknown error') if response.metadata else 'Unknown error'

            processing_time_ms = (time.time() - start_time) * 1000

            # Track analytics asynchronously
            doc_tracker = get_document_tracker()
            await doc_tracker.track_document_processing(
                user_id=user_id,
                document_type=document_type,
                file_size_bytes=file_size,
                processing_time_ms=processing_time_ms,
                output_format=output_format.value,
                success=success,
                pages_processed=pages_processed,
                words_extracted=words_extracted,
                error_message=error_message
            )

            return response

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            error_message = str(e)
            
            # Track failed processing
            try:
                doc_tracker = get_document_tracker()
                await doc_tracker.track_document_processing(
                    user_id=user_id,
                    document_type=document_type,
                    file_size_bytes=file_size,
                    processing_time_ms=processing_time_ms,
                    output_format=output_format.value,
                    success=False,
                    pages_processed=0,
                    words_extracted=0,
                    error_message=error_message
                )
            except Exception as analytics_error:
                logger.warning(f"Failed to track analytics: {analytics_error}")
            
            # Re-raise the original exception
            raise

    def _convert_to_format(self, doc, output_format: OutputFormat) -> str:
        """Convert DoclingDocument to desired output format."""
        try:
            match output_format:
                case OutputFormat.MARKDOWN:
                    return doc.export_to_markdown()
                case OutputFormat.HTML:
                    return doc.export_to_html()
                case OutputFormat.TEXT:
                    return doc.export_to_text()
                case OutputFormat.DOCTAGS:
                    return doc.export_to_doctags()
                case OutputFormat.JSON:
                    return json.dumps(self._create_nlp_structured_json(doc), indent=2)
                case _:
                    raise DocumentConversionError(
                        f"Unsupported output format: {output_format}")

        except Exception as e:
            raise DocumentConversionError(
                f"Failed to convert to {output_format}: {str(e)}")

    def _extract_metadata(self, doc) -> Dict[str, Any]:
        """Extract metadata from document."""
        try:
            doc_dict = doc.export_to_dict()

            # Count pages if available
            page_count = len(doc_dict.get('pages', []))

            # Estimate word count from text
            text_content = doc.export_to_text()
            word_count = len(text_content.split()) if text_content else 0

            # Extract other metadata
            metadata = {
                "page_count": page_count,
                "word_count": word_count,
                "has_images": bool(doc_dict.get('pictures', [])),
                "has_tables": bool(doc_dict.get('tables', [])),
            }

            # Add document-level metadata if available
            if hasattr(doc, 'metadata') and doc.metadata:
                metadata.update(doc.metadata)

            return metadata

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return {}

    def _create_nlp_structured_json(self, doc) -> Dict[str, Any]:
        """Create a structured JSON format optimized for NLP tasks."""
        try:
            doc_dict = doc.export_to_dict()
            text_content = doc.export_to_text()
            
            # Extract structured data for NLP processing
            structured_data = {
                "document_info": {
                    "total_pages": len(doc_dict.get('pages', [])),
                    "total_words": len(text_content.split()) if text_content else 0,
                    "total_characters": len(text_content) if text_content else 0,
                    "has_tables": bool(doc_dict.get('tables', [])),
                    "has_images": bool(doc_dict.get('pictures', [])),
                    "language": "en"  # Default, could be detected
                },
                "content": {
                    "full_text": text_content,
                    "paragraphs": [],
                    "sentences": [],
                    "entities": [],
                    "keywords": []
                },
                "structure": {
                    "headings": [],
                    "tables": [],
                    "lists": [],
                    "images": []
                },
                "pages": []
            }
            
            # Process pages
            pages = doc_dict.get('pages', [])
            for i, page in enumerate(pages):
                page_data = {
                    "page_number": i + 1,
                    "text": "",
                    "elements": [],
                    "bounding_boxes": []
                }
                
                # Extract text elements from page
                if hasattr(page, 'texts') or 'texts' in page:
                    texts = page.get('texts', []) if isinstance(page, dict) else getattr(page, 'texts', [])
                    for text_elem in texts:
                        if isinstance(text_elem, dict):
                            text_content = text_elem.get('text', '')
                        else:
                            text_content = str(text_elem)
                        
                        page_data["text"] += text_content + " "
                        page_data["elements"].append({
                            "type": "text",
                            "content": text_content,
                            "bbox": text_elem.get('bbox', []) if isinstance(text_elem, dict) else []
                        })
                
                structured_data["pages"].append(page_data)
            
            # Extract paragraphs by splitting on double newlines
            if text_content:
                paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
                structured_data["content"]["paragraphs"] = [
                    {
                        "id": i,
                        "text": para,
                        "word_count": len(para.split()),
                        "char_count": len(para)
                    } for i, para in enumerate(paragraphs)
                ]
                
                # Extract sentences (simple split on sentence endings)
                sentences = []
                for para in paragraphs:
                    import re
                    sent_list = re.split(r'[.!?]+', para)
                    sentences.extend([s.strip() for s in sent_list if s.strip()])
                
                structured_data["content"]["sentences"] = [
                    {
                        "id": i,
                        "text": sent,
                        "word_count": len(sent.split()),
                        "char_count": len(sent)
                    } for i, sent in enumerate(sentences)
                ]
            
            # Extract tables
            tables = doc_dict.get('tables', [])
            for i, table in enumerate(tables):
                table_data = {
                    "id": i,
                    "rows": [],
                    "columns": [],
                    "cell_count": 0
                }
                
                if isinstance(table, dict):
                    # Process table structure if available
                    table_data["raw_data"] = table
                
                structured_data["structure"]["tables"].append(table_data)
            
            # Extract images/pictures metadata
            pictures = doc_dict.get('pictures', [])
            for i, picture in enumerate(pictures):
                image_data = {
                    "id": i,
                    "type": "image",
                    "metadata": picture if isinstance(picture, dict) else {}
                }
                structured_data["structure"]["images"].append(image_data)
            
            # Basic keyword extraction (simple frequency-based)
            if text_content:
                import re
                from collections import Counter
                
                # Simple keyword extraction
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text_content.lower())
                word_freq = Counter(words)
                
                # Filter out common stop words
                stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'under', 'over', 'within', 'without', 'along', 'following', 'across', 'throughout', 'upon', 'around', 'beyond', 'near', 'since', 'until', 'toward', 'towards', 'via', 'against', 'concerning', 'regarding', 'according', 'including', 'excluding', 'except', 'besides', 'unlike', 'despite', 'throughout', 'within'}
                
                keywords = [
                    {"word": word, "frequency": freq, "score": freq / len(words)}
                    for word, freq in word_freq.most_common(20)
                    if word not in stop_words and len(word) > 3
                ]
                
                structured_data["content"]["keywords"] = keywords
            
            return structured_data
            
        except Exception as e:
            logger.warning(f"Failed to create structured JSON: {e}")
            # Fallback to basic structure
            return {
                "document_info": {
                    "total_pages": 0,
                    "total_words": 0,
                    "error": str(e)
                },
                "content": {
                    "full_text": doc.export_to_text() if hasattr(doc, 'export_to_text') else "",
                    "paragraphs": [],
                    "sentences": []
                },
                "structure": {
                    "raw_docling_export": doc.export_to_dict() if hasattr(doc, 'export_to_dict') else {}
                }
            }
    
    def health_check(self) -> bool:
        """Check if DoclingService is healthy."""
        try:
            # Try to access the converter
            _ = self.converter
            return True
        except Exception as e:
            logger.error(f"DoclingService health check failed: {e}")
            return False


# Create singleton instance
@lru_cache(maxsize=1)
def get_docling_service() -> DoclingService:
    """Get cached DoclingService instance."""
    return DoclingService()
