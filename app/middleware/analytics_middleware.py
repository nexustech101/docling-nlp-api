"""Analytics middleware to automatically track API usage and document processing."""

import time
import logging
import asyncio
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ..services.analytics_service import get_analytics_service

logger = logging.getLogger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage for analytics."""
    
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/favicon.ico",
            "/analytics/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track analytics."""
        start_time = time.time()
        
        # Skip tracking for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get request size
        request_size = 0
        if hasattr(request, "body"):
            try:
                body = await request.body()
                request_size = len(body) if body else 0
            except Exception:
                request_size = 0
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Get response size (estimate)
        response_size = 0
        if hasattr(response, "body"):
            try:
                response_size = len(response.body) if response.body else 0
            except Exception:
                response_size = 0
        
        # Track analytics asynchronously (fire and forget)
        asyncio.create_task(
            self._track_analytics(
                request=request,
                response=response,
                processing_time_ms=processing_time_ms,
                request_size=request_size,
                response_size=response_size
            )
        )
        
        return response
    
    async def _track_analytics(
        self,
        request: Request,
        response: Response,
        processing_time_ms: float,
        request_size: int,
        response_size: int
    ):
        """Track analytics data asynchronously."""
        try:
            analytics_service = get_analytics_service()
            
            if not analytics_service.is_available():
                return
            
            # Extract user ID from request
            user_id = await self._extract_user_id(request)
            
            if not user_id:
                # Skip tracking for unauthenticated requests
                return
            
            # Determine error message if applicable
            error_message = None
            if response.status_code >= 400:
                error_message = f"HTTP {response.status_code}"
            
            # Track API usage
            await analytics_service.track_api_usage(
                user_id=user_id,
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=processing_time_ms,
                request_size_bytes=request_size,
                response_size_bytes=response_size,
                error_message=error_message
            )
            
        except Exception as e:
            # Log error but don't affect the main request
            logger.warning(f"Failed to track analytics: {str(e)}")
    
    async def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request authorization header."""
        try:
            # Check for Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            # Extract token
            token = auth_header.replace("Bearer ", "")
            
            # Use Firebase service to verify token and get user ID
            from ..services.firebase_service import get_firebase_service
            firebase_service = get_firebase_service()
            
            try:
                user_info = await firebase_service.verify_token(token)
                return user_info.get("uid")
            except Exception:
                # Invalid or expired token
                return None
                
        except Exception as e:
            logger.debug(f"Failed to extract user ID: {str(e)}")
            return None


class DocumentProcessingTracker:
    """Helper class to track document processing analytics."""
    
    def __init__(self):
        self.analytics_service = get_analytics_service()
    
    async def track_document_processing(
        self,
        user_id: str,
        document_type: str,
        file_size_bytes: int,
        processing_time_ms: float,
        output_format: str,
        success: bool,
        pages_processed: int = 0,
        words_extracted: int = 0,
        error_message: str = None
    ):
        """Track document processing for analytics."""
        if not self.analytics_service.is_available():
            return
        
        try:
            await self.analytics_service.track_document_processing(
                user_id=user_id,
                document_type=document_type,
                file_size_bytes=file_size_bytes,
                processing_time_ms=processing_time_ms,
                output_format=output_format,
                success=success,
                pages_processed=pages_processed,
                words_extracted=words_extracted,
                error_message=error_message
            )
        except Exception as e:
            logger.warning(f"Failed to track document processing: {str(e)}")


# Global instance for document processing tracking
_doc_tracker = None

def get_document_tracker() -> DocumentProcessingTracker:
    """Get document processing tracker instance."""
    global _doc_tracker
    if _doc_tracker is None:
        _doc_tracker = DocumentProcessingTracker()
    return _doc_tracker
