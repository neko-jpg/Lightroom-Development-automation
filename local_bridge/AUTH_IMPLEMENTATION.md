# Authentication and Security Implementation
# 認証・セキュリティ実装

**Task 31: API認証・セキュリティの実装**  
**Requirements: 9.5**

## Overview

This document describes the authentication and security implementation for the Junmai AutoDev API, including JWT authentication, API key management, rate limiting, and CORS configuration.

## Components

### 1. Authentication Manager (`auth_manager.py`)

Core authentication and security management module.

**Features:**
- JWT token generation and verification
- API key generation, verification, and revocation
- Rate limiting per identifier (IP, user ID, API key)
- Secure secret key management
- Configuration persistence

**Key Classes:**
- `AuthManager`: Main authentication manager class
- Decorators: `@jwt_required`, `@api_key_required`, `@rate_limit()`

**Configuration:**
- Config file: `config/auth.json`
- JWT expiration: 24 hours (configurable)
- Rate limits:
  - Default: 100 requests/minute
  - Auth endpoints: 10 requests/minute
  - Upload endpoints: 20 requests/minute

### 2. Authentication API (`api_auth.py`)

REST API endpoints for authentication operations.

**Endpoints:**

#### Authentication
- `POST /api/auth/login` - User login (returns JWT token)
- `GET /api/auth/verify` - Verify JWT token
- `POST /api/auth/refresh` - Refresh JWT token

#### API Key Management
- `GET /api/auth/apikeys` - List all API keys (JWT required)
- `POST /api/auth/apikeys` - Create new API key (JWT required)
- `DELETE /api/auth/apikeys/<key>` - Revoke API key (JWT required)
- `GET /api/auth/apikeys/verify` - Verify API key

#### System Info
- `GET /api/auth/ratelimit` - Get rate limit configuration
- `GET /api/auth/info` - Get authentication system information

### 3. CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured to allow:
- Origins: `http://localhost:*`, `http://127.0.0.1:*`
- Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Headers: Content-Type, Authorization, X-API-Key
- Exposed Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

## Usage Examples

### 1. User Authentication (JWT)

```python
# Login
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

# Response
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "user_abc123",
    "username": "admin"
  }
}

# Use token in subsequent requests
GET /api/sessions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. API Key Authentication

```python
# Create API key (requires JWT)
POST /api/auth/apikeys
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Mobile App Key",
  "description": "API key for mobile application",
  "permissions": ["read", "write"]
}

# Response
{
  "api_key": "jad_abc123def456...",
  "name": "Mobile App Key",
  "warning": "This is the only time the API key will be shown..."
}

# Use API key in requests (header)
GET /api/photos
X-API-Key: jad_abc123def456...

# Or use API key in query parameter
GET /api/photos?api_key=jad_abc123def456...
```

### 3. Rate Limiting

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 60
```

When rate limit is exceeded:

```python
# Response: 429 Too Many Requests
{
  "error": "Rate limit exceeded",
  "retry_after": 45
}

# Headers
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 45
```

## Security Features

### 1. JWT Token Security
- Tokens signed with HS256 algorithm
- Secret key stored securely in config file
- Token expiration enforced (24 hours default)
- Tampering detection through signature verification

### 2. API Key Security
- Keys prefixed with `jad_` for identification
- Keys hashed (SHA-256) before storage
- Only shown once upon creation
- Usage tracking (last used, usage count)
- Revocation support

### 3. Rate Limiting
- Per-identifier tracking (IP, user ID, API key)
- Configurable limits per endpoint type
- Automatic reset after time window
- Exponential backoff for repeated violations

### 4. CORS Protection
- Restricted to localhost origins for development
- Configurable allowed origins
- Credentials support
- Preflight request handling

## Testing

### Unit Tests (`test_auth.py`)

Comprehensive unit tests for authentication manager:

**Test Coverage:**
- Secret key generation and persistence
- JWT token generation and verification
- JWT token expiration
- JWT token tampering detection
- API key generation and verification
- API key revocation
- API key usage tracking
- Rate limiting (within limit, exceeded, reset)
- Rate limiting per identifier
- Error handling and edge cases

**Run Tests:**
```bash
pytest local_bridge/test_auth.py -v
```

### Integration Tests (`test_auth_api.py`)

Integration tests for API endpoints:

**Test Coverage:**
- Login endpoint (success, failures)
- Token verification
- Token refresh
- API key creation
- API key listing
- API key verification
- API key revocation
- Rate limiting headers
- CORS headers

**Run Tests:**
```bash
pytest local_bridge/test_auth_api.py -v
```

## Configuration

### Default Configuration (`config/auth.json`)

```json
{
  "secret_key": "<auto-generated-secure-key>",
  "api_keys": {
    "<key_hash>": {
      "name": "Example Key",
      "description": "Example API key",
      "permissions": ["read", "write"],
      "created_at": "2025-11-08T12:00:00",
      "last_used": "2025-11-08T14:30:00",
      "usage_count": 42
    }
  }
}
```

### Rate Limit Configuration

Configured in `AuthManager.__init__()`:

```python
self.rate_limits = {
    'default': {'requests': 100, 'window': 60},
    'auth': {'requests': 10, 'window': 60},
    'upload': {'requests': 20, 'window': 60}
}
```

## Integration with Existing API

### Protecting Endpoints

To protect existing endpoints, add decorators:

```python
from auth_manager import jwt_required, api_key_required, rate_limit

# Require JWT authentication
@app.route("/api/sessions", methods=["GET"])
@jwt_required
@rate_limit('default')
def get_sessions():
    # Access user info from g.user_id, g.username
    pass

# Require API key authentication
@app.route("/api/photos", methods=["GET"])
@api_key_required
@rate_limit('default')
def get_photos():
    # Access API key info from g.api_key_name, g.api_key_permissions
    pass

# Allow both JWT and API key
@app.route("/api/jobs", methods=["GET"])
@rate_limit('default')
def get_jobs():
    # Optional authentication - check if g.user_id or g.api_key_name exists
    pass
```

### Optional Authentication

For endpoints that support optional authentication:

```python
from flask import g

@app.route("/api/public", methods=["GET"])
def public_endpoint():
    # Check if authenticated
    if hasattr(g, 'user_id'):
        # User is authenticated via JWT
        user_id = g.user_id
    elif hasattr(g, 'api_key_name'):
        # User is authenticated via API key
        api_key_name = g.api_key_name
    else:
        # Anonymous access
        pass
```

## Deployment Considerations

### Production Recommendations

1. **Secret Key Management**
   - Use environment variables for secret key
   - Rotate secret keys periodically
   - Never commit secret keys to version control

2. **CORS Configuration**
   - Update allowed origins for production domains
   - Remove localhost origins in production
   - Use HTTPS only

3. **Rate Limiting**
   - Consider using Redis for distributed rate limiting
   - Adjust limits based on actual usage patterns
   - Implement IP-based blocking for abuse

4. **API Key Storage**
   - Consider using a dedicated secrets management service
   - Implement key rotation policies
   - Add key expiration dates

5. **Monitoring**
   - Log authentication failures
   - Monitor rate limit violations
   - Track API key usage patterns
   - Alert on suspicious activity

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=<secure-random-key>
JWT_EXPIRATION_HOURS=24

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://app.example.com,https://mobile.example.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis://localhost:6379/0
```

## Troubleshooting

### Common Issues

1. **"Authentication not configured" error**
   - Ensure `init_auth_manager()` is called before registering blueprints
   - Check that auth_manager.py is imported correctly

2. **"Invalid token" errors**
   - Verify token hasn't expired
   - Check that secret key hasn't changed
   - Ensure token format is correct (Bearer <token>)

3. **Rate limit exceeded unexpectedly**
   - Check if multiple clients share same IP
   - Verify rate limit configuration
   - Consider increasing limits for specific endpoints

4. **CORS errors in browser**
   - Verify allowed origins include your frontend URL
   - Check that credentials are enabled if needed
   - Ensure preflight requests are handled

## Future Enhancements

Potential improvements for future versions:

1. **User Management**
   - User registration and password management
   - Role-based access control (RBAC)
   - User profile management

2. **OAuth2 Support**
   - OAuth2 authorization flows
   - Third-party authentication (Google, GitHub)
   - Refresh token rotation

3. **Advanced Rate Limiting**
   - Redis-based distributed rate limiting
   - Per-endpoint custom limits
   - Dynamic rate limit adjustment

4. **Audit Logging**
   - Detailed authentication audit logs
   - API key usage analytics
   - Security event tracking

5. **Two-Factor Authentication**
   - TOTP support
   - SMS verification
   - Backup codes

## References

- JWT: https://jwt.io/
- Flask-CORS: https://flask-cors.readthedocs.io/
- PyJWT: https://pyjwt.readthedocs.io/
- OWASP API Security: https://owasp.org/www-project-api-security/

## Completion Status

✅ **Task 31: API認証・セキュリティの実装**
- ✅ JWT認証機能を実装
- ✅ APIキー管理機能を追加
- ✅ レート制限機能を実装
- ✅ CORS設定を追加

✅ **Task 31.1: API認証の単体テストを作成**
- ✅ JWT生成・検証のテストを実装
- ✅ 認証失敗ケースのテストを追加

**Implementation Date:** 2025-11-08  
**Requirements Satisfied:** 9.5 (モバイルコンパニオンアプリ - Web UI認証とセキュリティ)
