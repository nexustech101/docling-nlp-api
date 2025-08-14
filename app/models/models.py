from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime, date


class Message(BaseModel):
    message: str
    key: str
    salt: Optional[str] = None


class MessageRequest(BaseModel):
    recipient: str
    message: str
    salt: Optional[str]
    expire_in_seconds: int
    key: str


class MessageResponse(BaseModel):
    sender: str
    message: str
    salt: Optional[str]
    timestamp: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    username: str


class FirebaseUserCreate(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class FirebaseUserResponse(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    created_at: str


class APIToken(BaseModel):
    token_id: str
    user_id: str
    token_name: str
    token_hash: str
    created_at: str
    expires_at: str
    last_used: Optional[str] = None
    is_active: bool = True


class APITokenCreate(BaseModel):
    token_name: str
    expires_in_days: Optional[int] = 30


class APITokenResponse(BaseModel):
    token_id: str
    token_name: str
    api_token: str  # Only returned on creation
    created_at: str
    expires_at: str


class APITokenInfo(BaseModel):
    token_id: str
    token_name: str
    created_at: str
    expires_at: str
    last_used: Optional[str] = None
    is_active: bool


# Analytics Models

class APIUsageStats(BaseModel):
    """API usage statistics model."""
    total_calls: int = 0
    error_count: int = 0
    success_rate: float = 0.0  # Percentage
    average_response_time_ms: float = 0.0
    total_data_transfer_bytes: int = 0
    top_endpoints: Dict[str, int] = {}


class DocumentProcessingStats(BaseModel):
    """Document processing statistics model."""
    total_documents: int = 0
    success_rate: float = 0.0  # Percentage
    total_file_size_bytes: int = 0
    total_pages_processed: int = 0
    total_words_extracted: int = 0
    average_processing_time_ms: float = 0.0
    document_type_distribution: Dict[str, int] = {}
    output_format_distribution: Dict[str, int] = {}


class UsageTrend(BaseModel):
    """Usage trend data point."""
    date: date
    api_calls: int = 0
    documents_processed: int = 0
    data_transfer_bytes: int = 0


class UserAnalytics(BaseModel):
    """Comprehensive user analytics."""
    user_id: str
    date_range_start: datetime
    date_range_end: datetime
    api_usage: APIUsageStats
    document_processing: DocumentProcessingStats
    usage_trends: List[UsageTrend]
    generated_at: datetime


class AnalyticsDashboard(BaseModel):
    """Complete analytics dashboard data."""
    user_id: str
    last_7_days: UserAnalytics
    last_30_days: UserAnalytics
    last_90_days: UserAnalytics
    generated_at: datetime


class AnalyticsRequest(BaseModel):
    """Request model for analytics queries."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_trends: bool = True


class RealTimeStats(BaseModel):
    """Real-time statistics model."""
    today: Dict[str, Any]
    timestamp: str
