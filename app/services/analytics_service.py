"""Analytics Service with Firebase Firestore for CRM Dashboard."""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from collections import defaultdict

import firebase_admin
from firebase_admin import firestore
from firebase_admin.exceptions import FirebaseError

from ..core.config.config import get_settings
from ..models.models import (
    UserAnalytics, 
    APIUsageStats, 
    DocumentProcessingStats,
    UsageTrend,
    AnalyticsDashboard
)

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsService:
    """Analytics service for user data tracking and CRM dashboard."""
    
    def __init__(self):
        self._db = None
        self._initialize_firestore()
    
    def _initialize_firestore(self):
        """Initialize Firestore database connection."""
        try:
            # Use the same Firebase app instance from firebase_service
            if firebase_admin._apps:
                app = firebase_admin.get_app()
                self._db = firestore.client(app)
                logger.info("Firestore client initialized successfully")
            else:
                logger.warning("Firebase app not initialized. Analytics will not work.")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {str(e)}")
            self._db = None
    
    def is_available(self) -> bool:
        """Check if Firestore is properly initialized."""
        return self._db is not None
    
    async def track_api_usage(
        self, 
        user_id: str, 
        endpoint: str, 
        method: str,
        status_code: int,
        response_time_ms: float,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """Track API usage for analytics."""
        if not self.is_available():
            logger.warning("Firestore not available, skipping analytics tracking")
            return
        
        try:
            usage_data = {
                'user_id': user_id,
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'response_time_ms': response_time_ms,
                'request_size_bytes': request_size_bytes,
                'response_size_bytes': response_size_bytes,
                'error_message': error_message,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'date': datetime.utcnow().date().isoformat(),
                'hour': datetime.utcnow().hour
            }
            
            # Add to api_usage collection
            self._db.collection('api_usage').add(usage_data)
            
            # Update user's daily stats
            await self._update_daily_stats(user_id, usage_data)
            
        except Exception as e:
            logger.error(f"Failed to track API usage: {str(e)}")
    
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
        error_message: Optional[str] = None
    ) -> None:
        """Track document processing for analytics."""
        if not self.is_available():
            logger.warning("Firestore not available, skipping document processing tracking")
            return
        
        try:
            doc_data = {
                'user_id': user_id,
                'document_type': document_type,
                'file_size_bytes': file_size_bytes,
                'processing_time_ms': processing_time_ms,
                'output_format': output_format,
                'success': success,
                'pages_processed': pages_processed,
                'words_extracted': words_extracted,
                'error_message': error_message,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'date': datetime.utcnow().date().isoformat(),
                'hour': datetime.utcnow().hour
            }
            
            # Add to document_processing collection
            self._db.collection('document_processing').add(doc_data)
            
            # Update user's document processing stats
            await self._update_document_stats(user_id, doc_data)
            
        except Exception as e:
            logger.error(f"Failed to track document processing: {str(e)}")
    
    async def _update_daily_stats(self, user_id: str, usage_data: Dict[str, Any]) -> None:
        """Update user's daily statistics."""
        try:
            date_str = usage_data['date']
            daily_stats_ref = self._db.collection('daily_stats').document(f"{user_id}_{date_str}")
            
            # Get existing stats or create new
            doc = daily_stats_ref.get()
            if doc.exists:
                stats = doc.to_dict()
            else:
                stats = {
                    'user_id': user_id,
                    'date': date_str,
                    'api_calls': 0,
                    'total_response_time_ms': 0,
                    'total_request_bytes': 0,
                    'total_response_bytes': 0,
                    'error_count': 0,
                    'endpoints': {},
                    'created_at': firestore.SERVER_TIMESTAMP
                }
            
            # Update stats
            stats['api_calls'] += 1
            stats['total_response_time_ms'] += usage_data['response_time_ms']
            stats['total_request_bytes'] += usage_data['request_size_bytes']
            stats['total_response_bytes'] += usage_data['response_size_bytes']
            
            if usage_data['status_code'] >= 400:
                stats['error_count'] += 1
            
            # Track endpoint usage
            endpoint = usage_data['endpoint']
            if endpoint not in stats['endpoints']:
                stats['endpoints'][endpoint] = 0
            stats['endpoints'][endpoint] += 1
            
            stats['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Save updated stats
            daily_stats_ref.set(stats)
            
        except Exception as e:
            logger.error(f"Failed to update daily stats: {str(e)}")
    
    async def _update_document_stats(self, user_id: str, doc_data: Dict[str, Any]) -> None:
        """Update user's document processing statistics."""
        try:
            date_str = doc_data['date']
            doc_stats_ref = self._db.collection('document_stats').document(f"{user_id}_{date_str}")
            
            # Get existing stats or create new
            doc = doc_stats_ref.get()
            if doc.exists:
                stats = doc.to_dict()
            else:
                stats = {
                    'user_id': user_id,
                    'date': date_str,
                    'documents_processed': 0,
                    'total_file_size_bytes': 0,
                    'total_processing_time_ms': 0,
                    'total_pages_processed': 0,
                    'total_words_extracted': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'document_types': {},
                    'output_formats': {},
                    'created_at': firestore.SERVER_TIMESTAMP
                }
            
            # Update stats
            stats['documents_processed'] += 1
            stats['total_file_size_bytes'] += doc_data['file_size_bytes']
            stats['total_processing_time_ms'] += doc_data['processing_time_ms']
            stats['total_pages_processed'] += doc_data['pages_processed']
            stats['total_words_extracted'] += doc_data['words_extracted']
            
            if doc_data['success']:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            # Track document types
            doc_type = doc_data['document_type']
            if doc_type not in stats['document_types']:
                stats['document_types'][doc_type] = 0
            stats['document_types'][doc_type] += 1
            
            # Track output formats
            output_format = doc_data['output_format']
            if output_format not in stats['output_formats']:
                stats['output_formats'][output_format] = 0
            stats['output_formats'][output_format] += 1
            
            stats['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Save updated stats
            doc_stats_ref.set(stats)
            
        except Exception as e:
            logger.error(f"Failed to update document stats: {str(e)}")
    
    async def get_user_analytics(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> UserAnalytics:
        """Get comprehensive analytics for a user."""
        if not self.is_available():
            raise FirebaseError("Analytics service not available")
        
        try:
            # Default to last 30 days if no date range specified
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get API usage stats
            api_stats = await self._get_api_usage_stats(user_id, start_date, end_date)
            
            # Get document processing stats
            doc_stats = await self._get_document_processing_stats(user_id, start_date, end_date)
            
            # Get usage trends
            usage_trends = await self._get_usage_trends(user_id, start_date, end_date)
            
            return UserAnalytics(
                user_id=user_id,
                date_range_start=start_date,
                date_range_end=end_date,
                api_usage=api_stats,
                document_processing=doc_stats,
                usage_trends=usage_trends,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            raise
    
    async def _get_api_usage_stats(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> APIUsageStats:
        """Get API usage statistics for a user."""
        try:
            start_date_str = start_date.date().isoformat()
            end_date_str = end_date.date().isoformat()
            
            # Query daily stats
            daily_stats = []
            query = self._db.collection('daily_stats').where(
                'user_id', '==', user_id
            ).where(
                'date', '>=', start_date_str
            ).where(
                'date', '<=', end_date_str
            )
            
            docs = query.stream()
            for doc in docs:
                daily_stats.append(doc.to_dict())
            
            # Aggregate stats
            total_calls = sum(stat.get('api_calls', 0) for stat in daily_stats)
            total_response_time = sum(stat.get('total_response_time_ms', 0) for stat in daily_stats)
            total_errors = sum(stat.get('error_count', 0) for stat in daily_stats)
            total_data_transfer = sum(
                stat.get('total_request_bytes', 0) + stat.get('total_response_bytes', 0)
                for stat in daily_stats
            )
            
            # Calculate average response time
            avg_response_time = (total_response_time / total_calls) if total_calls > 0 else 0
            
            # Get most used endpoints
            endpoint_usage = defaultdict(int)
            for stat in daily_stats:
                endpoints = stat.get('endpoints', {})
                for endpoint, count in endpoints.items():
                    endpoint_usage[endpoint] += count
            
            # Sort endpoints by usage
            top_endpoints = sorted(
                endpoint_usage.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return APIUsageStats(
                total_calls=total_calls,
                error_count=total_errors,
                success_rate=(total_calls - total_errors) / total_calls * 100 if total_calls > 0 else 0,
                average_response_time_ms=avg_response_time,
                total_data_transfer_bytes=total_data_transfer,
                top_endpoints=dict(top_endpoints)
            )
            
        except Exception as e:
            logger.error(f"Failed to get API usage stats: {str(e)}")
            raise
    
    async def _get_document_processing_stats(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> DocumentProcessingStats:
        """Get document processing statistics for a user."""
        try:
            start_date_str = start_date.date().isoformat()
            end_date_str = end_date.date().isoformat()
            
            # Query document stats
            doc_stats = []
            query = self._db.collection('document_stats').where(
                'user_id', '==', user_id
            ).where(
                'date', '>=', start_date_str
            ).where(
                'date', '<=', end_date_str
            )
            
            docs = query.stream()
            for doc in docs:
                doc_stats.append(doc.to_dict())
            
            # Aggregate stats
            total_documents = sum(stat.get('documents_processed', 0) for stat in doc_stats)
            total_file_size = sum(stat.get('total_file_size_bytes', 0) for stat in doc_stats)
            total_pages = sum(stat.get('total_pages_processed', 0) for stat in doc_stats)
            total_words = sum(stat.get('total_words_extracted', 0) for stat in doc_stats)
            success_count = sum(stat.get('success_count', 0) for stat in doc_stats)
            total_processing_time = sum(stat.get('total_processing_time_ms', 0) for stat in doc_stats)
            
            # Calculate success rate
            success_rate = (success_count / total_documents * 100) if total_documents > 0 else 0
            
            # Calculate average processing time
            avg_processing_time = (total_processing_time / total_documents) if total_documents > 0 else 0
            
            # Get document type distribution
            doc_type_distribution = defaultdict(int)
            for stat in doc_stats:
                doc_types = stat.get('document_types', {})
                for doc_type, count in doc_types.items():
                    doc_type_distribution[doc_type] += count
            
            # Get output format distribution
            format_distribution = defaultdict(int)
            for stat in doc_stats:
                formats = stat.get('output_formats', {})
                for format_type, count in formats.items():
                    format_distribution[format_type] += count
            
            return DocumentProcessingStats(
                total_documents=total_documents,
                success_rate=success_rate,
                total_file_size_bytes=total_file_size,
                total_pages_processed=total_pages,
                total_words_extracted=total_words,
                average_processing_time_ms=avg_processing_time,
                document_type_distribution=dict(doc_type_distribution),
                output_format_distribution=dict(format_distribution)
            )
            
        except Exception as e:
            logger.error(f"Failed to get document processing stats: {str(e)}")
            raise
    
    async def _get_usage_trends(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UsageTrend]:
        """Get usage trends over time for a user."""
        try:
            trends = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_str = current_date.isoformat()
                
                # Get daily API stats
                api_doc = self._db.collection('daily_stats').document(f"{user_id}_{date_str}").get()
                api_calls = 0
                if api_doc.exists:
                    api_calls = api_doc.to_dict().get('api_calls', 0)
                
                # Get daily document stats
                doc_doc = self._db.collection('document_stats').document(f"{user_id}_{date_str}").get()
                documents_processed = 0
                if doc_doc.exists:
                    documents_processed = doc_doc.to_dict().get('documents_processed', 0)
                
                trend = UsageTrend(
                    date=current_date,
                    api_calls=api_calls,
                    documents_processed=documents_processed,
                    data_transfer_bytes=0  # Can be added if needed
                )
                trends.append(trend)
                
                current_date += timedelta(days=1)
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get usage trends: {str(e)}")
            raise
    
    async def get_analytics_dashboard(self, user_id: str) -> AnalyticsDashboard:
        """Get comprehensive analytics dashboard data."""
        if not self.is_available():
            raise FirebaseError("Analytics service not available")
        
        try:
            # Get analytics for different time periods
            now = datetime.utcnow()
            
            # Last 7 days
            week_analytics = await self.get_user_analytics(
                user_id, 
                start_date=now - timedelta(days=7),
                end_date=now
            )
            
            # Last 30 days
            month_analytics = await self.get_user_analytics(
                user_id,
                start_date=now - timedelta(days=30),
                end_date=now
            )
            
            # Last 90 days
            quarter_analytics = await self.get_user_analytics(
                user_id,
                start_date=now - timedelta(days=90),
                end_date=now
            )
            
            return AnalyticsDashboard(
                user_id=user_id,
                last_7_days=week_analytics,
                last_30_days=month_analytics,
                last_90_days=quarter_analytics,
                generated_at=now
            )
            
        except Exception as e:
            logger.error(f"Failed to get analytics dashboard: {str(e)}")
            raise
    
    async def get_real_time_stats(self, user_id: str) -> Dict[str, Any]:
        """Get real-time statistics for today."""
        if not self.is_available():
            return {}
        
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Get today's API stats
            api_doc = self._db.collection('daily_stats').document(f"{user_id}_{today}").get()
            api_stats = api_doc.to_dict() if api_doc.exists else {}
            
            # Get today's document stats
            doc_doc = self._db.collection('document_stats').document(f"{user_id}_{today}").get()
            doc_stats = doc_doc.to_dict() if doc_doc.exists else {}
            
            return {
                'today': {
                    'api_calls': api_stats.get('api_calls', 0),
                    'documents_processed': doc_stats.get('documents_processed', 0),
                    'errors': api_stats.get('error_count', 0) + doc_stats.get('error_count', 0),
                    'data_transfer_mb': (
                        api_stats.get('total_request_bytes', 0) + 
                        api_stats.get('total_response_bytes', 0)
                    ) / (1024 * 1024)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time stats: {str(e)}")
            return {}


# Global instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get Analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
