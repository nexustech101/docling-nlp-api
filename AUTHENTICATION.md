# Authentication and Rate Limiting

This document describes the authentication system, API token management, and rate limiting features implemented in the Docling NLP API.

## Overview

The API supports multiple authentication methods:

1. **Firebase Authentication** - For user-facing applications
2. **API Tokens** - For programmatic access
3. **Legacy JWT** - For backward compatibility

Additionally, the API implements comprehensive rate limiting with different tiers based on authentication status.

## Firebase Authentication

### Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication in the Firebase console
3. Generate a service account key:
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file securely

4. Configure environment variables:
   ```bash
   FIREBASE_PROJECT_ID="your-project-id"
   FIREBASE_CREDENTIALS_PATH="path/to/serviceAccountKey.json"
   # OR
   FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
   ```

### Endpoints

#### Register User
```http
POST /auth/firebase/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password",
  "display_name": "User Name"
}
```

#### Get Current User
```http
GET /auth/firebase/me
Authorization: Bearer <firebase-id-token>
```

#### Delete Account
```http
DELETE /auth/firebase/me
Authorization: Bearer <firebase-id-token>
```

#### Revoke Tokens
```http
POST /auth/firebase/revoke-tokens
Authorization: Bearer <firebase-id-token>
```

### Client-Side Usage

Use the Firebase SDK to authenticate users and obtain ID tokens:

```javascript
import { getAuth, signInWithEmailAndPassword, getIdToken } from 'firebase/auth';

const auth = getAuth();
await signInWithEmailAndPassword(auth, email, password);
const idToken = await getIdToken(auth.currentUser);

// Use idToken in Authorization header
fetch('/api/protected-endpoint', {
  headers: {
    'Authorization': `Bearer ${idToken}`
  }
});
```

## API Token Management

API tokens provide a secure way for applications to access the API without requiring user interaction.

### Features

- **Secure Generation**: Tokens are cryptographically secure
- **Expiration**: Configurable expiration (default 30 days)
- **Naming**: Descriptive names for easy management
- **Usage Tracking**: Last used timestamps
- **Limits**: Maximum tokens per user (default 5)

### Endpoints

#### Create Token
```http
POST /auth/tokens
Authorization: Bearer <firebase-id-token|api-token>
Content-Type: application/json

{
  "token_name": "My Application",
  "expires_in_days": 30
}
```

Response:
```json
{
  "token_id": "abc123",
  "token_name": "My Application",
  "api_token": "secure-api-token-here",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-31T00:00:00Z"
}
```

**⚠️ Important**: Save the `api_token` immediately - it's only returned once!

#### List Tokens
```http
GET /auth/tokens
Authorization: Bearer <firebase-id-token|api-token>
```

#### Revoke Token
```http
DELETE /auth/tokens/{token_id}
Authorization: Bearer <firebase-id-token|api-token>
```

#### Revoke All Tokens
```http
DELETE /auth/tokens
Authorization: Bearer <firebase-id-token|api-token>
```

### Usage

Use API tokens in the Authorization header:

```http
GET /api/documents/process
Authorization: Bearer <api-token>
```

## Rate Limiting

The API implements tiered rate limiting based on authentication status:

### Rate Limits

| User Type | Per Minute | Per Hour | Per Day |
|-----------|------------|----------|---------|
| Anonymous (IP-based) | 30 | 500 | 2,000 |
| Authenticated (Firebase) | 60 | 1,000 | 10,000 |
| API Token | 120 | 2,000 | 20,000 |

### Configuration

Rate limits are configurable via environment variables:

```bash
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
REDIS_URL="redis://localhost:6379"
ENABLE_RATE_LIMITING=true
```

### Redis Backend

For production deployments, use Redis for distributed rate limiting:

```bash
# Install Redis
docker run -d -p 6379:6379 redis:alpine

# Or use cloud Redis (AWS ElastiCache, Google Cloud Memorystore, etc.)
REDIS_URL="redis://your-redis-host:6379"
```

### Rate Limit Headers

The API includes rate limit information in response headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded

When rate limits are exceeded, the API returns a 429 status:

```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests. Limit: 60/minute",
  "retry_after": 30,
  "message": "Sign in for higher rate limits"
}
```

## Authentication Methods

### 1. Firebase ID Token
```http
Authorization: Bearer <firebase-id-token>
```

### 2. API Token
```http
Authorization: Bearer <api-token>
```

### 3. Legacy JWT (backward compatibility)
```http
Authorization: Bearer <legacy-jwt>
```

## Verification Endpoint

Test authentication with the verification endpoint:

```http
GET /auth/verify
Authorization: Bearer <token>
```

Response:
```json
{
  "valid": true,
  "user_id": "user-123",
  "auth_type": "firebase|api_token|legacy"
}
```

## Security Best Practices

### For Firebase Authentication

1. **Secure Token Storage**: Store ID tokens securely on the client
2. **Token Refresh**: Implement automatic token refresh
3. **HTTPS Only**: Always use HTTPS in production
4. **Validate Tokens**: Server-side token validation is mandatory

### For API Tokens

1. **Secure Storage**: Store API tokens securely (environment variables, secret managers)
2. **Least Privilege**: Create tokens with minimal necessary permissions
3. **Regular Rotation**: Rotate tokens regularly
4. **Monitor Usage**: Track token usage and revoke unused tokens
5. **Environment Separation**: Use different tokens for different environments

### General Security

1. **Rate Limiting**: Implement and monitor rate limits
2. **Logging**: Log authentication attempts and failures
3. **Monitoring**: Set up alerts for suspicious activity
4. **Regular Audits**: Regularly audit active tokens and users

## Troubleshooting

### Firebase Issues

1. **"Firebase not initialized"**: Check environment variables and service account key
2. **"Invalid ID token"**: Ensure client is using the correct Firebase project
3. **"Expired ID token"**: Implement token refresh on the client

### API Token Issues

1. **"Invalid or expired API token"**: Check token expiration and validity
2. **"Maximum number of tokens reached"**: Revoke unused tokens
3. **Token not working**: Ensure correct Authorization header format

### Rate Limiting Issues

1. **Redis connection failed**: Check Redis URL and connectivity
2. **Rate limits too strict**: Adjust limits in environment variables
3. **Inconsistent limits**: Ensure Redis is properly configured for distributed setups

## Environment Variables Reference

```bash
# Firebase
FIREBASE_PROJECT_ID="your-firebase-project-id"
FIREBASE_CREDENTIALS_PATH="path/to/firebase-credentials.json"
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000
REDIS_URL="redis://localhost:6379"
ENABLE_RATE_LIMITING=true

# API Tokens
API_TOKEN_EXPIRY_DAYS=30
MAX_API_TOKENS_PER_USER=5
JWT_SECRET_KEY="your-super-secret-jwt-key"
JWT_ALGORITHM="HS256"
```
