"""Analytics API routes for user data tracking and CRM dashboard."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer

from ..services.analytics_service import get_analytics_service
from ..services.firebase_service import get_firebase_service
from ..models.models import (
    UserAnalytics, 
    AnalyticsDashboard,
    RealTimeStats,
    AnalyticsRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


async def get_current_user(token: str = Depends(security)):
    """Get current authenticated user from Firebase token."""
    firebase_service = get_firebase_service()
    try:
        user = await firebase_service.verify_token(token.credentials)
        return user
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/analytics/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive analytics dashboard for the authenticated user."""
    analytics_service = get_analytics_service()
    
    if not analytics_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service is not available"
        )
    
    try:
        user_id = current_user.get("uid")
        dashboard_data = await analytics_service.get_analytics_dashboard(user_id)
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics dashboard"
        )


@router.get("/analytics/summary", response_model=UserAnalytics)
async def get_analytics_summary(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics (ISO format)"),
    current_user: dict = Depends(get_current_user)
):
    """Get analytics summary for a specific date range."""
    analytics_service = get_analytics_service()
    
    if not analytics_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service is not available"
        )
    
    try:
        user_id = current_user.get("uid")
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Validate date range
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        # Limit to maximum 1 year range
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 365 days"
            )
        
        analytics_data = await analytics_service.get_user_analytics(
            user_id, start_date, end_date
        )
        return analytics_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics summary"
        )


@router.get("/analytics/real-time", response_model=RealTimeStats)
async def get_real_time_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get real-time statistics for today."""
    analytics_service = get_analytics_service()
    
    if not analytics_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service is not available"
        )
    
    try:
        user_id = current_user.get("uid")
        real_time_stats = await analytics_service.get_real_time_stats(user_id)
        
        return RealTimeStats(**real_time_stats)
    
    except Exception as e:
        logger.error(f"Failed to get real-time stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve real-time statistics"
        )


@router.get("/analytics/trends")
async def get_usage_trends(
    days: int = Query(30, ge=1, le=90, description="Number of days to get trends for"),
    current_user: dict = Depends(get_current_user)
):
    """Get usage trends for the specified number of days."""
    analytics_service = get_analytics_service()
    
    if not analytics_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service is not available"
        )
    
    try:
        user_id = current_user.get("uid")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        analytics_data = await analytics_service.get_user_analytics(
            user_id, start_date, end_date
        )
        
        # Return only the trends data
        return {
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "trends": analytics_data.usage_trends
        }
    
    except Exception as e:
        logger.error(f"Failed to get usage trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage trends"
        )


@router.get("/analytics/health")
async def get_analytics_health():
    """Check analytics service health."""
    analytics_service = get_analytics_service()
    
    return {
        "status": "healthy" if analytics_service.is_available() else "unavailable",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "analytics"
    }


# Admin routes (if needed later)
@router.get("/analytics/admin/users")
async def get_all_users_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get aggregated analytics for all users (admin only)."""
    # This would require admin role checking
    # For now, just return unauthorized
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required"
    )
