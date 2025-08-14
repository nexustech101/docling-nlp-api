from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timezone, timedelta
from typing import List
import jwt
from jwt.exceptions import PyJWTError
from firebase_admin.exceptions import FirebaseError

from ...models.models import (
    Token, FirebaseUserCreate, FirebaseUserResponse, 
    APITokenCreate, APITokenResponse, APITokenInfo
)
from ...services.firebase_service import get_firebase_service
from ...services.api_token_service import get_api_token_service
from ...utils.db import register_user, authenticate_user
from ..dependencies import (
    get_current_user_firebase, get_current_user_api_token, 
    get_current_user_any, get_firebase_dependency, get_api_token_dependency
)
from ...middleware.rate_limit import limiter, RateLimitConfig
from ...core.config.config import get_settings

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Legacy endpoints (keep for backward compatibility)
@auth_router.post("/register")
@limiter.limit(RateLimitConfig.ANONYMOUS_PER_MINUTE)
async def register(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Legacy user registration endpoint."""
    if not register_user(form_data.username, form_data.password):
        raise HTTPException(status_code=400, detail="Username already taken")
    return {"message": "User registered"}


@auth_router.post("/login", response_model=Token)
@limiter.limit(RateLimitConfig.ANONYMOUS_PER_MINUTE)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Legacy user login endpoint."""
    user_id = authenticate_user(form_data.username, form_data.password)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "sub": form_data.username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(token_data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return {"access_token": token, "token_type": "bearer"}


# Firebase Authentication Endpoints
@auth_router.post("/firebase/register", response_model=FirebaseUserResponse)
@limiter.limit(RateLimitConfig.ANONYMOUS_PER_MINUTE)
async def firebase_register(
    request: Request,
    user_data: FirebaseUserCreate,
    firebase_service = Depends(get_firebase_dependency)
):
    """Register a new user with Firebase."""
    if not firebase_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Firebase authentication is not configured"
        )
    
    try:
        user = await firebase_service.create_user(user_data)
        return user
    except FirebaseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.get("/firebase/me", response_model=FirebaseUserResponse)
async def firebase_get_current_user(
    current_user = Depends(get_current_user_firebase),
    firebase_service = Depends(get_firebase_dependency)
):
    """Get current Firebase user information."""
    user = await firebase_service.get_user(current_user["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@auth_router.delete("/firebase/me")
async def firebase_delete_account(
    current_user = Depends(get_current_user_firebase),
    firebase_service = Depends(get_firebase_dependency)
):
    """Delete current Firebase user account."""
    try:
        await firebase_service.delete_user(current_user["uid"])
        return {"message": "Account deleted successfully"}
    except FirebaseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.post("/firebase/revoke-tokens")
async def firebase_revoke_tokens(
    current_user = Depends(get_current_user_firebase),
    firebase_service = Depends(get_firebase_dependency)
):
    """Revoke all refresh tokens for the current user."""
    try:
        await firebase_service.revoke_refresh_tokens(current_user["uid"])
        return {"message": "All refresh tokens revoked"}
    except FirebaseError as e:
        raise HTTPException(status_code=400, detail=str(e))


# API Token Management Endpoints
@auth_router.post("/tokens", response_model=APITokenResponse)
async def create_api_token(
    token_data: APITokenCreate,
    current_user = Depends(get_current_user_any),
    token_service = Depends(get_api_token_dependency)
):
    """Create a new API token for the authenticated user."""
    try:
        token = await token_service.create_token(current_user["user_id"], token_data)
        return token
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.get("/tokens", response_model=List[APITokenInfo])
async def list_api_tokens(
    current_user = Depends(get_current_user_any),
    token_service = Depends(get_api_token_dependency)
):
    """List all API tokens for the authenticated user."""
    tokens = await token_service.get_user_tokens(current_user["user_id"])
    return tokens


@auth_router.delete("/tokens/{token_id}")
async def revoke_api_token(
    token_id: str,
    current_user = Depends(get_current_user_any),
    token_service = Depends(get_api_token_dependency)
):
    """Revoke a specific API token."""
    success = await token_service.revoke_token(current_user["user_id"], token_id)
    if not success:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"message": "Token revoked successfully"}


@auth_router.delete("/tokens")
async def revoke_all_api_tokens(
    current_user = Depends(get_current_user_any),
    token_service = Depends(get_api_token_dependency)
):
    """Revoke all API tokens for the authenticated user."""
    count = await token_service.revoke_all_tokens(current_user["user_id"])
    return {"message": f"{count} tokens revoked successfully"}


# Utility endpoint to verify tokens
@auth_router.get("/verify")
async def verify_token(
    current_user = Depends(get_current_user_any)
):
    """Verify the provided authentication token."""
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "auth_type": current_user["auth_type"]
    }


# Legacy function for backward compatibility
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Legacy function for getting current user from JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=401, detail="Invalid token payload"
            )
        return sub
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
