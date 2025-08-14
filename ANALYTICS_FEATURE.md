# Analytics Feature Documentation

## Overview

The Docling NLP API now includes a comprehensive analytics system that tracks user activity, API usage, and document processing statistics. This feature provides valuable insights for CRM dashboards and usage monitoring.

## Features

### 1. Automatic API Usage Tracking
- **Request/Response Metrics**: Tracks all API calls with response times, status codes, and data transfer sizes
- **Endpoint Analytics**: Monitors which endpoints are most frequently used
- **Error Tracking**: Captures and categorizes API errors for debugging
- **Authentication**: Only tracks authenticated requests (requires Firebase token)

### 2. Document Processing Analytics
- **Processing Metrics**: Tracks document processing times, file sizes, and success rates
- **Document Types**: Monitors which document types are processed most frequently
- **Output Formats**: Tracks popular output format preferences
- **Content Analysis**: Records page counts, word counts, and document features

### 3. Real-time Dashboard Data
- **Live Statistics**: Current day API calls, documents processed, and errors
- **Historical Trends**: Usage patterns over 7, 30, and 90-day periods
- **Performance Metrics**: Average response times and success rates

## Architecture

### Components

1. **AnalyticsService** (`app/services/analytics_service.py`)
   - Manages Firestore integration
   - Aggregates daily statistics
   - Provides dashboard data

2. **AnalyticsMiddleware** (`app/middleware/analytics_middleware.py`)
   - Automatically tracks all API requests
   - Extracts user information from JWT tokens
   - Non-blocking async analytics recording

3. **DocumentProcessingTracker** 
   - Tracks document processing events
   - Integrates with DoclingService
   - Records processing metadata

4. **Analytics API Routes** (`app/api/routes/analytics.py`)
   - REST endpoints for retrieving analytics
   - JWT-based authentication
   - Rate limiting and validation

## Data Models

### Firestore Collections

#### `api_usage`
```json
{
  "user_id": "firebase_uid",
  "endpoint": "/api/documents/process",
  "method": "POST",
  "status_code": 200,
  "response_time_ms": 1250.5,
  "request_size_bytes": 1024,
  "response_size_bytes": 4096,
  "timestamp": "2024-01-15T10:30:00Z",
  "date": "2024-01-15",
  "hour": 10
}
```

#### `document_processing`
```json
{
  "user_id": "firebase_uid",
  "document_type": "pdf",
  "file_size_bytes": 2048000,
  "processing_time_ms": 3500.2,
  "output_format": "json",
  "success": true,
  "pages_processed": 12,
  "words_extracted": 5420,
  "timestamp": "2024-01-15T10:30:00Z",
  "date": "2024-01-15"
}
```

#### `daily_stats`
```json
{
  "user_id": "firebase_uid",
  "date": "2024-01-15",
  "api_calls": 45,
  "total_response_time_ms": 56250,
  "error_count": 2,
  "endpoints": {
    "/api/documents/process": 32,
    "/api/analytics/dashboard": 8,
    "/api/auth/verify": 5
  }
}
```

#### `document_stats`
```json
{
  "user_id": "firebase_uid",
  "date": "2024-01-15",
  "documents_processed": 15,
  "success_count": 14,
  "total_file_size_bytes": 30720000,
  "total_pages_processed": 180,
  "document_types": {
    "pdf": 10,
    "docx": 3,
    "txt": 2
  },
  "output_formats": {
    "json": 8,
    "markdown": 4,
    "text": 3
  }
}
```

## API Endpoints

### Authentication Required
All analytics endpoints require Firebase JWT authentication via `Authorization: Bearer <token>` header.

### Available Endpoints

#### 1. Analytics Dashboard
```
GET /api/analytics/dashboard
```
Returns comprehensive analytics for 7, 30, and 90-day periods.

**Response:**
```json
{
  "user_id": "firebase_uid",
  "last_7_days": { ... },
  "last_30_days": { ... },
  "last_90_days": { ... },
  "generated_at": "2024-01-15T10:30:00Z"
}
```

#### 2. Analytics Summary
```
GET /api/analytics/summary?start_date=2024-01-01&end_date=2024-01-31
```
Returns analytics for a specific date range.

**Query Parameters:**
- `start_date` (optional): ISO format datetime
- `end_date` (optional): ISO format datetime

#### 3. Real-time Statistics
```
GET /api/analytics/real-time
```
Returns today's real-time statistics.

**Response:**
```json
{
  "today": {
    "api_calls": 23,
    "documents_processed": 8,
    "errors": 1,
    "data_transfer_mb": 45.2
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 4. Usage Trends
```
GET /api/analytics/trends?days=30
```
Returns usage trends for specified number of days (1-90).

#### 5. Health Check
```
GET /api/analytics/health
```
Returns analytics service health status (no authentication required).

## Integration

### Automatic Tracking

Analytics tracking is automatically enabled when:
1. The request is authenticated with a valid Firebase token
2. The endpoint is not in the exclusion list
3. Firestore is properly configured

### Manual Document Tracking

For document processing routes, use the analytics-enabled method:

```python
from app.services.docling_service import get_docling_service

docling_service = get_docling_service()
result = await docling_service.process_document_with_analytics(
    file_path=uploaded_file_path,
    output_format=OutputFormat.JSON,
    user_id=current_user["uid"],
    use_ocr=False
)
```

### Configuration

#### Environment Variables
```bash
# Firebase configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
FIREBASE_CLIENT_EMAIL=service-account@project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
```

#### Excluded Paths
The following paths are excluded from analytics tracking:
- `/docs`
- `/redoc`
- `/openapi.json`
- `/health`
- `/favicon.ico`
- `/analytics/health`

## Performance Considerations

### Async Processing
- Analytics tracking is non-blocking
- Uses fire-and-forget async tasks
- Won't affect API response times

### Firestore Optimization
- Daily aggregation reduces query load
- Efficient document structure
- Indexed fields for fast queries

### Error Handling
- Analytics failures don't affect main API functionality
- Graceful degradation when Firestore is unavailable
- Comprehensive logging for debugging

## Security

### Authentication
- All analytics endpoints require valid Firebase JWT tokens
- Users can only access their own analytics data
- Rate limiting applies to analytics endpoints

### Data Privacy
- Only aggregated statistics are stored
- No sensitive request/response content is logged
- User IDs are Firebase UIDs (not email addresses)

### Access Control
- Admin endpoints are reserved for future implementation
- User-level access controls via Firebase rules

## Monitoring

### Health Checks
```bash
curl -X GET "https://your-api.com/api/analytics/health"
```

### Logs
Analytics service logs are available at these levels:
- `INFO`: Successful operations and service status
- `WARNING`: Non-critical failures (e.g., tracking failures)
- `ERROR`: Critical failures affecting service availability

### Metrics
Key metrics to monitor:
- Analytics service availability
- Firestore connection health
- Daily statistics generation
- Error rates in analytics processing

## Troubleshooting

### Common Issues

1. **Analytics Not Working**
   - Verify Firebase configuration
   - Check service account permissions
   - Ensure Firestore API is enabled

2. **Missing Data**
   - Confirm user authentication
   - Check excluded paths configuration
   - Verify date ranges in queries

3. **Performance Issues**
   - Monitor Firestore quotas
   - Check query complexity
   - Review aggregation efficiency

### Debug Mode
Enable debug logging by setting `LOG_LEVEL=DEBUG` in environment variables.

## Future Enhancements

### Planned Features
1. **Admin Dashboard**: Cross-user analytics for administrators
2. **Custom Alerts**: Usage threshold notifications
3. **Export Functionality**: CSV/PDF report generation
4. **Advanced Analytics**: Machine learning insights
5. **API Rate Analysis**: Automatic rate limit optimization

### Integration Opportunities
1. **Prometheus Metrics**: Export metrics for monitoring systems
2. **Grafana Dashboards**: Visual analytics dashboards
3. **Slack/Email Notifications**: Usage alerts and reports
4. **Billing Integration**: Usage-based pricing calculations

This analytics system provides comprehensive insights into API usage patterns and document processing statistics, enabling data-driven decisions for service optimization and user experience improvements.
