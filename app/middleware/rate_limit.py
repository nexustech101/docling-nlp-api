"""Rate limiting middleware."""

import logging
from typing import Callable, Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ..core.config.config import get_settings
from ..services.firebase_service import get_firebase_service
from ..services.api_token_service import get_api_token_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize the limiter with Redis backend if available, otherwise use in-memory
try:
    import redis
    redis_client = redis.from_url(settings.redis_url)
    redis_client.ping()  # Test connection
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.redis_url
    )
    logger.info("Rate limiting initialized with Redis backend")
except Exception as e:
    logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
    limiter = Limiter(key_func=get_remote_address)


def get_user_identifier(request: Request) -> str:
    """
    Get user identifier for rate limiting.
    Priority: API Token > Firebase UID > IP Address
    """
    # Try to get user from API token first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        
        # Check if it's an API token
        api_token_service = get_api_token_service()
        user_id = None
        try:
            # This is a synchronous call - we might need to make it async later
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            user_id = loop.run_until_complete(api_token_service.verify_token(token))
        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
        
        if user_id:
            return f"api_token:{user_id}"
        
        # Check if it's a Firebase ID token
        firebase_service = get_firebase_service()
        if firebase_service.is_available():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                decoded_token = loop.run_until_complete(firebase_service.verify_id_token(token))
                if decoded_token:
                    return f"firebase:{decoded_token['uid']}"
            except Exception as e:
                logger.debug(f"Firebase token verification failed: {e}")
    
    # Fall back to IP address
    return get_remote_address(request)


def get_user_identifier_async():
    """Get user identifier function for async rate limiting."""
    async def _get_user_id(request: Request) -> str:
        """Async version of get_user_identifier."""
        # Try to get user from API token first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            
            # Check if it's an API token
            api_token_service = get_api_token_service()
            user_id = await api_token_service.verify_token(token)
            if user_id:
                return f"api_token:{user_id}"
            
            # Check if it's a Firebase ID token
            firebase_service = get_firebase_service()
            if firebase_service.is_available():
                try:
                    decoded_token = await firebase_service.verify_id_token(token)
                    if decoded_token:
                        return f"firebase:{decoded_token['uid']}"
                except Exception as e:
                    logger.debug(f"Firebase token verification failed: {e}")
        
        # Fall back to IP address
        return get_remote_address(request)
    
    return _get_user_id


# Create limiter with user-aware rate limiting
user_limiter = Limiter(
    key_func=get_user_identifier_async(),
    storage_uri=settings.redis_url if settings.redis_url != "redis://localhost:6379" else None
)


class RateLimitConfig:
    """Rate limiting configuration for different user types."""
    
    # Anonymous users (IP-based)
    ANONYMOUS_PER_MINUTE = "30/minute"
    ANONYMOUS_PER_HOUR = "500/hour"
    ANONYMOUS_PER_DAY = "2000/day"
    
    # Authenticated users (higher limits)
    AUTHENTICATED_PER_MINUTE = f"{settings.rate_limit_per_minute}/minute"
    AUTHENTICATED_PER_HOUR = f"{settings.rate_limit_per_hour}/hour"
    AUTHENTICATED_PER_DAY = f"{settings.rate_limit_per_day}/day"
    
    # API token users (highest limits)
    API_TOKEN_PER_MINUTE = f"{settings.rate_limit_per_minute * 2}/minute"
    API_TOKEN_PER_HOUR = f"{settings.rate_limit_per_hour * 2}/hour"
    API_TOKEN_PER_DAY = f"{settings.rate_limit_per_day * 2}/day"


def get_rate_limit_for_user(request: Request) -> str:
    """Get appropriate rate limit based on user type."""
    user_id = get_user_identifier(request)
    
    if user_id.startswith("api_token:"):
        return RateLimitConfig.API_TOKEN_PER_MINUTE
    elif user_id.startswith("firebase:"):
        return RateLimitConfig.AUTHENTICATED_PER_MINUTE
    else:
        return RateLimitConfig.ANONYMOUS_PER_MINUTE


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler."""
    response = {
        "error": "Rate limit exceeded",
        "detail": f"Too many requests. Limit: {exc.detail}",
        "retry_after": exc.retry_after
    }
    
    # Add user-specific messaging
    user_id = get_user_identifier(request)
    if user_id.startswith("api_token:") or user_id.startswith("firebase:"):
        response["message"] = "Consider upgrading your plan for higher rate limits"
    else:
        response["message"] = "Sign in for higher rate limits"
    
    return HTTPException(status_code=429, detail=response)


# Export the limiter and middleware
__all__ = ["limiter", "user_limiter", "RateLimitConfig", "get_user_identifier", "rate_limit_exceeded_handler"]
