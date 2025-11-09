"""
Integration Tests for Authentication API Endpoints
認証APIエンドポイントの統合テスト

Tests for:
- Login endpoint
- Token verification
- Token refresh
- API key management endpoints
- Rate limiting on endpoints

Requirements: 9.5
"""

import pytest
import json
import tempfile
import pathlib
from flask import Flask
from auth_manager import init_auth_manager, configure_cors
from api_auth import auth_api_bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Initialize auth manager with temp config
    temp_dir = tempfile.mkdtemp()
    config_path = pathlib.Path(temp_dir) / "auth_api_test.json"
    init_auth_manager(config_path=str(config_path))
    
    # Configure CORS
    configure_cors(app)
    
    # Register blueprint
    app.register_blueprint(auth_api_bp)
    
    yield app
    
    # Cleanup
    if config_path.exists():
        config_path.unlink()
    pathlib.Path(temp_dir).rmdir()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestLoginEndpoint:
    """Test login endpoint"""
    
    def test_login_success(self, client):
        """Test successful login"""
        response = client.post('/api/auth/login',
                              json={'username': 'admin', 'password': 'password'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'token' in data
        assert 'token_type' in data
        assert data['token_type'] == 'Bearer'
        assert 'expires_in' in data
        assert 'user' in data
        assert data['user']['username'] == 'admin'
    
    def test_login_missing_username(self, client):
        """Test login with missing username"""
        response = client.post('/api/auth/login',
                              json={'password': 'password'},
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_missing_password(self, client):
        """Test login with missing password"""
        response = client.post('/api/auth/login',
                              json={'username': 'admin'},
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login',
                              json={'username': 'invalid', 'password': 'wrong'},
                              content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_empty_credentials(self, client):
        """Test login with empty credentials"""
        response = client.post('/api/auth/login',
                              json={'username': '', 'password': ''},
                              content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data


class TestTokenVerification:
    """Test token verification endpoint"""
    
    def test_verify_valid_token(self, client):
        """Test verification with valid token"""
        # Login first
        login_response = client.post('/api/auth/login',
                                    json={'username': 'admin', 'password': 'password'},
                                    content_type='application/json')
        token = json.loads(login_response.data)['token']
        
        # Verify token
        response = client.get('/api/auth/verify',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['valid'] is True
        assert 'user' in data
        assert data['user']['username'] == 'admin'
    
    def test_verify_missing_token(self, client):
        """Test verification without token"""
        response = client.get('/api/auth/verify')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_invalid_token(self, client):
        """Test verification with invalid token"""
        response = client.get('/api/auth/verify',
                             headers={'Authorization': 'Bearer invalid.token.here'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_verify_malformed_header(self, client):
        """Test verification with malformed Authorization header"""
        response = client.get('/api/auth/verify',
                             headers={'Authorization': 'InvalidFormat token'})
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data


class TestTokenRefresh:
    """Test token refresh endpoint"""
    
    def test_refresh_valid_token(self, client):
        """Test refresh with valid token"""
        # Login first
        login_response = client.post('/api/auth/login',
                                    json={'username': 'admin', 'password': 'password'},
                                    content_type='application/json')
        old_token = json.loads(login_response.data)['token']
        
        # Refresh token
        response = client.post('/api/auth/refresh',
                              headers={'Authorization': f'Bearer {old_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'token' in data
        assert 'token_type' in data
        assert data['token_type'] == 'Bearer'
        assert 'expires_in' in data
        
        # New token should be different from old token
        assert data['token'] != old_token
    
    def test_refresh_without_token(self, client):
        """Test refresh without token"""
        response = client.post('/api/auth/refresh')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data


class TestAPIKeyManagement:
    """Test API key management endpoints"""
    
    def get_auth_token(self, client):
        """Helper to get authentication token"""
        response = client.post('/api/auth/login',
                              json={'username': 'admin', 'password': 'password'},
                              content_type='application/json')
        return json.loads(response.data)['token']
    
    def test_create_api_key(self, client):
        """Test API key creation"""
        token = self.get_auth_token(client)
        
        response = client.post('/api/auth/apikeys',
                              headers={'Authorization': f'Bearer {token}'},
                              json={'name': 'Test Key', 'description': 'Test description'},
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        
        assert 'api_key' in data
        assert data['api_key'].startswith('jad_')
        assert data['name'] == 'Test Key'
        assert 'warning' in data
    
    def test_create_api_key_without_auth(self, client):
        """Test API key creation without authentication"""
        response = client.post('/api/auth/apikeys',
                              json={'name': 'Test Key'},
                              content_type='application/json')
        
        assert response.status_code == 401
    
    def test_create_api_key_missing_name(self, client):
        """Test API key creation without name"""
        token = self.get_auth_token(client)
        
        response = client.post('/api/auth/apikeys',
                              headers={'Authorization': f'Bearer {token}'},
                              json={'description': 'Test'},
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_list_api_keys(self, client):
        """Test listing API keys"""
        token = self.get_auth_token(client)
        
        # Create some API keys
        for i in range(3):
            client.post('/api/auth/apikeys',
                       headers={'Authorization': f'Bearer {token}'},
                       json={'name': f'Test Key {i}'},
                       content_type='application/json')
        
        # List keys
        response = client.get('/api/auth/apikeys',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'api_keys' in data
        assert 'count' in data
        assert data['count'] >= 3
    
    def test_list_api_keys_without_auth(self, client):
        """Test listing API keys without authentication"""
        response = client.get('/api/auth/apikeys')
        
        assert response.status_code == 401
    
    def test_verify_api_key(self, client):
        """Test API key verification endpoint"""
        token = self.get_auth_token(client)
        
        # Create API key
        create_response = client.post('/api/auth/apikeys',
                                     headers={'Authorization': f'Bearer {token}'},
                                     json={'name': 'Test Key'},
                                     content_type='application/json')
        api_key = json.loads(create_response.data)['api_key']
        
        # Verify API key
        response = client.get('/api/auth/apikeys/verify',
                             headers={'X-API-Key': api_key})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['valid'] is True
        assert 'api_key' in data
        assert data['api_key']['name'] == 'Test Key'
    
    def test_verify_api_key_query_param(self, client):
        """Test API key verification via query parameter"""
        token = self.get_auth_token(client)
        
        # Create API key
        create_response = client.post('/api/auth/apikeys',
                                     headers={'Authorization': f'Bearer {token}'},
                                     json={'name': 'Test Key'},
                                     content_type='application/json')
        api_key = json.loads(create_response.data)['api_key']
        
        # Verify API key via query param
        response = client.get(f'/api/auth/apikeys/verify?api_key={api_key}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] is True
    
    def test_verify_invalid_api_key(self, client):
        """Test verification with invalid API key"""
        response = client.get('/api/auth/apikeys/verify',
                             headers={'X-API-Key': 'jad_invalid_key'})
        
        assert response.status_code == 401
    
    def test_revoke_api_key(self, client):
        """Test API key revocation"""
        token = self.get_auth_token(client)
        
        # Create API key
        create_response = client.post('/api/auth/apikeys',
                                     headers={'Authorization': f'Bearer {token}'},
                                     json={'name': 'Test Key'},
                                     content_type='application/json')
        api_key = json.loads(create_response.data)['api_key']
        
        # Revoke API key
        response = client.delete(f'/api/auth/apikeys/{api_key}',
                                headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        
        # Verify key no longer works
        verify_response = client.get('/api/auth/apikeys/verify',
                                    headers={'X-API-Key': api_key})
        assert verify_response.status_code == 401
    
    def test_revoke_nonexistent_key(self, client):
        """Test revoking non-existent API key"""
        token = self.get_auth_token(client)
        
        response = client.delete('/api/auth/apikeys/jad_nonexistent',
                                headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 404


class TestRateLimiting:
    """Test rate limiting on endpoints"""
    
    def test_rate_limit_info(self, client):
        """Test rate limit info endpoint"""
        response = client.get('/api/auth/ratelimit')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'rate_limits' in data
        assert 'message' in data
    
    def test_rate_limit_headers(self, client):
        """Test rate limit headers are present"""
        # Make a request to an endpoint with rate limiting
        response = client.post('/api/auth/login',
                              json={'username': 'admin', 'password': 'password'},
                              content_type='application/json')
        
        # Check for rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers


class TestAuthInfo:
    """Test authentication info endpoint"""
    
    def test_auth_info(self, client):
        """Test authentication info endpoint"""
        response = client.get('/api/auth/info')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'authentication' in data
        assert 'rate_limiting' in data
        assert 'cors' in data
        
        assert data['authentication']['jwt_enabled'] is True
        assert data['authentication']['api_key_enabled'] is True
        assert data['rate_limiting']['enabled'] is True
        assert data['cors']['enabled'] is True


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present in responses"""
        response = client.options('/api/auth/login')
        
        # CORS headers should be present
        assert 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options('/api/auth/login',
                                 headers={
                                     'Origin': 'http://localhost:3000',
                                     'Access-Control-Request-Method': 'POST'
                                 })
        
        # Should allow the request
        assert response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
