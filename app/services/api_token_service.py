"""API Token Management Service."""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from jwt.exceptions import PyJWTError

from ..core.config.config import get_settings
from ..models.models import APIToken, APITokenCreate, APITokenResponse, APITokenInfo
from ..utils.db import get_connection

logger = logging.getLogger(__name__)
settings = get_settings()


class APITokenService:
    """Service for managing API tokens."""
    
    def __init__(self):
        self._init_token_tables()
    
    def _init_token_tables(self):
        """Initialize API token database tables."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_name TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    last_used DATETIME,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            conn.commit()
    
    def _generate_token(self) -> tuple:
        """Generate a new API token and its hash."""
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        # Create hash for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash
    
    def _generate_token_id(self) -> str:
        """Generate a unique token ID."""
        return secrets.token_urlsafe(16)
    
    async def create_token(self, user_id: str, token_data: APITokenCreate) -> APITokenResponse:
        """Create a new API token for a user."""
        # Check if user has reached token limit
        existing_tokens = await self.get_user_tokens(user_id)
        active_tokens = [t for t in existing_tokens if t.is_active]
        
        if len(active_tokens) >= settings.max_api_tokens_per_user:
            raise ValueError(f"Maximum number of API tokens ({settings.max_api_tokens_per_user}) reached")
        
        # Generate token and metadata
        token_id = self._generate_token_id()
        api_token, token_hash = self._generate_token()
        
        expires_in_days = token_data.expires_in_days or settings.api_token_expiry_days
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(days=expires_in_days)
        
        # Store in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_tokens 
                (token_id, user_id, token_name, token_hash, created_at, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                token_id,
                user_id,
                token_data.token_name,
                token_hash,
                created_at.isoformat(),
                expires_at.isoformat(),
                True
            ))
            conn.commit()
        
        return APITokenResponse(
            token_id=token_id,
            token_name=token_data.token_name,
            api_token=api_token,
            created_at=created_at.isoformat(),
            expires_at=expires_at.isoformat()
        )
    
    async def verify_token(self, token: str) -> Optional[str]:
        """Verify an API token and return the associated user ID."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, expires_at, is_active, token_id
                FROM api_tokens 
                WHERE token_hash = ?
            """, (token_hash,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            user_id, expires_at_str, is_active, token_id = row
            
            # Check if token is active
            if not is_active:
                return None
            
            # Check if token is expired
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            except ValueError:
                expires_at = datetime.fromisoformat(expires_at_str).replace(tzinfo=timezone.utc)
            
            if datetime.now(timezone.utc) > expires_at:
                # Mark token as inactive
                cursor.execute("""
                    UPDATE api_tokens 
                    SET is_active = 0 
                    WHERE token_id = ?
                """, (token_id,))
                conn.commit()
                return None
            
            # Update last used timestamp
            cursor.execute("""
                UPDATE api_tokens 
                SET last_used = ? 
                WHERE token_id = ?
            """, (datetime.now(timezone.utc).isoformat(), token_id))
            conn.commit()
            
            return user_id
    
    async def get_user_tokens(self, user_id: str) -> List[APITokenInfo]:
        """Get all tokens for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT token_id, token_name, created_at, expires_at, last_used, is_active
                FROM api_tokens 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            tokens = []
            for row in cursor.fetchall():
                token_id, token_name, created_at, expires_at, last_used, is_active = row
                tokens.append(APITokenInfo(
                    token_id=token_id,
                    token_name=token_name,
                    created_at=created_at,
                    expires_at=expires_at,
                    last_used=last_used,
                    is_active=bool(is_active)
                ))
            
            return tokens
    
    async def revoke_token(self, user_id: str, token_id: str) -> bool:
        """Revoke a specific token."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE api_tokens 
                SET is_active = 0 
                WHERE token_id = ? AND user_id = ?
            """, (token_id, user_id))
            conn.commit()
            
            return cursor.rowcount > 0
    
    async def revoke_all_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE api_tokens 
                SET is_active = 0 
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            
            return cursor.rowcount
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens from the database."""
        current_time = datetime.now(timezone.utc).isoformat()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM api_tokens 
                WHERE expires_at < ? AND is_active = 0
            """, (current_time,))
            conn.commit()
            
            return cursor.rowcount


# Global instance
_api_token_service: Optional[APITokenService] = None


def get_api_token_service() -> APITokenService:
    """Get API token service instance."""
    global _api_token_service
    if _api_token_service is None:
        _api_token_service = APITokenService()
    return _api_token_service
