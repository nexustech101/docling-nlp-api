# from fastapi import FastAPI
# from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware
# from routes.auth_routes import auth_router
# from routes.user_routes import user_router
# from db import init_db

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     init_db()
#     yield


# app.include_router(auth_router, prefix="/auth")
# app.include_router(user_router, prefix="/users")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from .core.config.config import get_settings
from .core.exceptions import DoclingAPIException
from .api.routes import docs, health, auth, analytics
from .utils.logger import setup_logger
from .middleware.rate_limit import limiter, rate_limit_exceeded_handler
from .middleware.analytics_middleware import AnalyticsMiddleware
from .utils.db import init_db
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


settings = get_settings()
logger = setup_logger(__name__, settings.log_level)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="A production-ready API for document processing using Docling",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add analytics middleware (before rate limiting)
app.add_middleware(AnalyticsMiddleware)
logger.info("Analytics middleware enabled")

# Add rate limiting middleware
if settings.enable_rate_limiting:
    from slowapi.middleware import SlowAPIMiddleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    logger.info("Rate limiting enabled")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    init_db()
    logger.info("Database initialized")
    
    # Initialize services
    from .services.firebase_service import get_firebase_service
    from .services.api_token_service import get_api_token_service
    from .services.analytics_service import get_analytics_service
    
    firebase_service = get_firebase_service()
    api_token_service = get_api_token_service()
    analytics_service = get_analytics_service()
    
    logger.info(f"Firebase available: {firebase_service.is_available()}")
    logger.info("API token service initialized")
    logger.info(f"Analytics service available: {analytics_service.is_available()}")


# Exception handlers
@app.exception_handler(DoclingAPIException)
async def docling_exception_handler(request, exc: DoclingAPIException):
    """Handle custom Docling API exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc),
            "timestamp": time.time()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "detail": exc.detail,
            "timestamp": time.time()
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(docs.router)
app.include_router(auth.auth_router)
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "docs_url": "/docs",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
