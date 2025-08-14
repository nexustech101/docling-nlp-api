from fastapi import APIRouter, Depends
import time
from datetime import datetime

from ...core.config.config import get_settings
from ...models.schemas import HealthResponse
from ...services.docling_service import DoclingService
from ..dependencies import get_docling_dependency

settings = get_settings()

router = APIRouter(
    prefix="/health", 
    tags=["health"]
)

# Track startup time
startup_time = time.time()


@router.get("/", response_model=HealthResponse)
async def health_check(
    docling_service: DoclingService = Depends(get_docling_dependency)
):
    """Health check endpoint."""
    uptime = time.time() - startup_time
    docling_available = docling_service.health_check()

    return HealthResponse(
        version=settings.version,
        uptime=uptime,
        docling_available=docling_available
    )
