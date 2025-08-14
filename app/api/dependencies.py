from fastapi import Depends, HTTPException, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, Union
from firebase_admin.exceptions import FirebaseError

from ..core.config.config import get_settings
from ..services.docling_service import get_docling_service
from ..services.url_service import get_url_service
from ..services.firebase_service import get_firebase_service
from ..services.api_token_service import get_api_token_service
from ..utils.file_utils import validate_file_extension
from ..core.exceptions import UnsupportedFileTypeError, FileSizeError

settings = get_settings()


async def validate_upload_file(file: UploadFile = File(...)) -> UploadFile:
    """Validate uploaded file."""
    try:
        # Validate file extension
        validate_file_extension(file.filename)

        # Reset file pointer
        file.file.seek(0)

        return file

    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"File validation failed: {str(e)}")


def get_docling_dependency():
    """Dependency to get DoclingService."""
    return get_docling_service()


def get_url_dependency():
    """Dependency to get URLService."""
    return get_url_service()


# Authentication dependencies
security = HTTPBearer()


async def get_current_user_firebase(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from Firebase ID token."""
    firebase_service = get_firebase_service()
    
    if not firebase_service.is_available():
        raise HTTPException(
            status_code=503, 
            detail="Firebase authentication not available"
        )
    
    try:
        decoded_token = await firebase_service.verify_id_token(credentials.credentials)
        return decoded_token
    except FirebaseError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication token: {str(e)}"
        )


async def get_current_user_api_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from API token."""
    api_token_service = get_api_token_service()
    
    user_id = await api_token_service.verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API token"
        )
    
    return user_id


async def get_current_user_any(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from either Firebase ID token or API token."""
    # Try API token first (faster)
    api_token_service = get_api_token_service()
    user_id = await api_token_service.verify_token(credentials.credentials)
    
    if user_id:
        return {
            "user_id": user_id,
            "auth_type": "api_token"
        }
    
    # Try Firebase ID token
    firebase_service = get_firebase_service()
    if firebase_service.is_available():
        try:
            decoded_token = await firebase_service.verify_id_token(credentials.credentials)
            return {
                "user_id": decoded_token["uid"],
                "auth_type": "firebase",
                "firebase_token": decoded_token
            }
        except FirebaseError:
            pass
    
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication token"
    )


async def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise return None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ", 1)[1]
    
    # Try API token first
    api_token_service = get_api_token_service()
    user_id = await api_token_service.verify_token(token)
    
    if user_id:
        return {
            "user_id": user_id,
            "auth_type": "api_token"
        }
    
    # Try Firebase ID token
    firebase_service = get_firebase_service()
    if firebase_service.is_available():
        try:
            decoded_token = await firebase_service.verify_id_token(token)
            return {
                "user_id": decoded_token["uid"],
                "auth_type": "firebase",
                "firebase_token": decoded_token
            }
        except FirebaseError:
            pass
    
    return None


def get_firebase_dependency():
    """Dependency to get FirebaseService."""
    return get_firebase_service()


def get_api_token_dependency():
    """Dependency to get APITokenService."""
    return get_api_token_service()
