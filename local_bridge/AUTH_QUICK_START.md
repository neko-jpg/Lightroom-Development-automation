# Authentication Quick Start Guide
# 認証クイックスタートガイド

Quick guide to using the authentication system in Junmai AutoDev.

## Installation

1. Install required dependencies:
```bash
pip install PyJWT flask-cors psutil
```

2. The authentication system is automatically initialized when the app starts.

## Quick Examples

### 1. Login and Get Token

```bash
# Login
curl -X POST http://localhost:5100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

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
```

### 2. Use JWT Token

```bash
# Use token in API requests
curl -X GET http://localhost:5100/api/sessions \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3. Create API Key

```bash
# Create API key (requires JWT token)
curl -X POST http://localhost:5100/api/auth/apikeys \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "description": "For testing"}'

# Response
{
  "api_key": "jad_abc123def456...",
  "name": "My API Key",
  "warning": "This is the only time the API key will be shown..."
}
```

### 4. Use API Key

```bash
# Method 1: Header
curl -X GET http://localhost:5100/api/photos \
  -H "X-API-Key: jad_abc123def456..."

# Method 2: Query parameter
curl -X GET "http://localhost:5100/api/photos?api_key=jad_abc123def456..."
```

## Python Client Example

```python
import requests

# 1. Login
response = requests.post('http://localhost:5100/api/auth/login', json={
    'username': 'admin',
    'password': 'password'
})
token = response.json()['token']

# 2. Use token
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:5100/api/sessions', headers=headers)
sessions = response.json()

# 3. Create API key
response = requests.post('http://localhost:5100/api/auth/apikeys',
    headers=headers,
    json={'name': 'Python Client', 'description': 'API key for Python client'}
)
api_key = response.json()['api_key']

# 4. Use API key
headers = {'X-API-Key': api_key}
response = requests.get('http://localhost:5100/api/photos', headers=headers)
photos = response.json()
```

## JavaScript/React Example

```javascript
// 1. Login
const loginResponse = await fetch('http://localhost:5100/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'password' })
});
const { token } = await loginResponse.json();

// 2. Use token
const sessionsResponse = await fetch('http://localhost:5100/api/sessions', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const sessions = await sessionsResponse.json();

// 3. Create API key
const apiKeyResponse = await fetch('http://localhost:5100/api/auth/apikeys', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'React App',
    description: 'API key for React application'
  })
});
const { api_key } = await apiKeyResponse.json();

// 4. Use API key
const photosResponse = await fetch('http://localhost:5100/api/photos', {
  headers: { 'X-API-Key': api_key }
});
const photos = await photosResponse.json();
```

## Rate Limiting

Rate limits are automatically applied:

- **Default endpoints**: 100 requests/minute
- **Auth endpoints**: 10 requests/minute
- **Upload endpoints**: 20 requests/minute

Check rate limit status in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 60
```

When rate limit is exceeded (429 response):
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 45
}
```

## Common Operations

### List API Keys
```bash
curl -X GET http://localhost:5100/api/auth/apikeys \
  -H "Authorization: Bearer <token>"
```

### Verify Token
```bash
curl -X GET http://localhost:5100/api/auth/verify \
  -H "Authorization: Bearer <token>"
```

### Refresh Token
```bash
curl -X POST http://localhost:5100/api/auth/refresh \
  -H "Authorization: Bearer <token>"
```

### Revoke API Key
```bash
curl -X DELETE http://localhost:5100/api/auth/apikeys/<api_key> \
  -H "Authorization: Bearer <token>"
```

### Get Auth Info
```bash
curl -X GET http://localhost:5100/api/auth/info
```

## Testing

Run authentication tests:
```bash
# Unit tests
pytest local_bridge/test_auth.py -v

# Integration tests
pytest local_bridge/test_auth_api.py -v

# All auth tests
pytest local_bridge/test_auth*.py -v
```

## Troubleshooting

### Token Expired
If you get "Token has expired" error:
1. Login again to get a new token
2. Or use the refresh endpoint to get a new token

### Invalid Token
If you get "Invalid token" error:
1. Check token format: `Bearer <token>`
2. Verify token hasn't been tampered with
3. Ensure secret key hasn't changed

### Rate Limit Exceeded
If you get 429 error:
1. Wait for the time specified in `retry_after`
2. Check `X-RateLimit-Reset` header
3. Consider using API key for higher limits

### CORS Errors
If you get CORS errors in browser:
1. Verify your origin is in allowed list
2. Check that you're using correct headers
3. Ensure credentials are enabled if needed

## Configuration

Authentication configuration is stored in `config/auth.json`:

```json
{
  "secret_key": "<auto-generated>",
  "api_keys": {
    "<key_hash>": {
      "name": "Example Key",
      "description": "Example",
      "permissions": ["read", "write"],
      "created_at": "2025-11-08T12:00:00",
      "last_used": null,
      "usage_count": 0
    }
  }
}
```

**Note:** Never share or commit the `auth.json` file as it contains sensitive keys!

## Security Best Practices

1. **Store tokens securely**
   - Use secure storage (e.g., httpOnly cookies, secure localStorage)
   - Never log tokens
   - Clear tokens on logout

2. **Rotate API keys regularly**
   - Create new keys periodically
   - Revoke old keys
   - Monitor key usage

3. **Use HTTPS in production**
   - Never send tokens over HTTP
   - Enable secure cookies
   - Use HSTS headers

4. **Monitor authentication**
   - Log failed login attempts
   - Track API key usage
   - Alert on suspicious activity

## Next Steps

- Read [AUTH_IMPLEMENTATION.md](AUTH_IMPLEMENTATION.md) for detailed documentation
- Protect your API endpoints with `@jwt_required` or `@api_key_required`
- Implement user management for production use
- Configure CORS for your production domains

## Support

For issues or questions:
1. Check [AUTH_IMPLEMENTATION.md](AUTH_IMPLEMENTATION.md)
2. Review test files for examples
3. Check application logs in `logs/main.log`
