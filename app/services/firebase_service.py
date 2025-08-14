"""Firebase Authentication Service."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

from ..core.config.config import get_settings
from ..models.models import FirebaseUserCreate, FirebaseUserResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class FirebaseService:
    """Firebase Authentication Service."""
    
    def __init__(self):
        self._app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                cred = None
                
                # Try to load from service account key (JSON string)
                if settings.firebase_service_account_key:
                    try:
                        service_account_info = json.loads(settings.firebase_service_account_key)
                        cred = credentials.Certificate(service_account_info)
                    except json.JSONDecodeError:
                        logger.error("Invalid Firebase service account key format")
                        
                # Try to load from file path
                elif settings.firebase_credentials_path:
                    cred = credentials.Certificate(settings.firebase_credentials_path)
                
                # Initialize with credentials if available
                if cred:
                    self._app = firebase_admin.initialize_app(cred, {
                        'projectId': settings.firebase_project_id,
                    })
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    logger.warning("No Firebase credentials provided. Firebase auth will not work.")
            else:
                self._app = firebase_admin.get_app()
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            self._app = None
    
    def is_available(self) -> bool:
        """Check if Firebase is properly initialized."""
        return self._app is not None
    
    async def create_user(self, user_data: FirebaseUserCreate) -> FirebaseUserResponse:
        """Create a new Firebase user."""
        if not self.is_available():
            raise FirebaseError("Firebase not initialized")
            
        try:
            user_record = auth.create_user(
                email=user_data.email,
                password=user_data.password,
                display_name=user_data.display_name
            )
            
            return FirebaseUserResponse(
                uid=user_record.uid,
                email=user_record.email,
                display_name=user_record.display_name,
                created_at=datetime.utcnow().isoformat()
            )
            
        except FirebaseError as e:
            logger.error(f"Failed to create Firebase user: {str(e)}")
            raise
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user info."""
        if not self.is_available():
            raise FirebaseError("Firebase not initialized")
            
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
            
        except auth.InvalidIdTokenError:
            raise FirebaseError("Invalid ID token")
        except auth.ExpiredIdTokenError:
            raise FirebaseError("Expired ID token")
        except FirebaseError as e:
            logger.error(f"Failed to verify ID token: {str(e)}")
            raise
    
    async def get_user(self, uid: str) -> Optional[FirebaseUserResponse]:
        """Get user by UID."""
        if not self.is_available():
            raise FirebaseError("Firebase not initialized")
            
        try:
            user_record = auth.get_user(uid)
            
            return FirebaseUserResponse(
                uid=user_record.uid,
                email=user_record.email,
                display_name=user_record.display_name,
                created_at=user_record.user_metadata.creation_timestamp.isoformat()
            )
            
        except auth.UserNotFoundError:
            return None
        except FirebaseError as e:
            logger.error(f"Failed to get user: {str(e)}")
            raise
    
    async def update_user(self, uid: str, **kwargs) -> FirebaseUserResponse:
        """Update Firebase user."""
        if not self.is_available():
            raise FirebaseError("Firebase not initialized")
            
        try:
            user_record = auth.update_user(uid, **kwargs)
            
            return FirebaseUserResponse(
                uid=user_record.uid,
                email=user_record.email,
                display_name=user_record.display_name,
                created_at=user_record.user_metadata.creation_timestamp.isoformat()
            )
            
        except FirebaseError as e:
            logger.error(f"Failed to update user: {str(e)}")
            raise
    
    async def delete_user(self, uid: str) -> bool:
        """Delete Firebase user."""
        if not self.is_available():
            raise FirebaseError("Firebase not initialized")
            
        try:
            auth.delete_user(uid)
            return True
            
        except FirebaseError as e:
            logger.error(f"Failed to delete user: {str(e)}")
            raise
    
    async def revoke_refresh_tokens(self, uid: str) -> None:
        """Revoke all refresh tokens for a user."""
        if not self.is_available():
            raise FirebaseError("Firebase not initialized")
            
        try:
            auth.revoke_refresh_tokens(uid)
            
        except FirebaseError as e:
            logger.error(f"Failed to revoke tokens: {str(e)}")
            raise


# Global instance
_firebase_service: Optional[FirebaseService] = None


def get_firebase_service() -> FirebaseService:
    """Get Firebase service instance."""
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseService()
    return _firebase_service
