"""
Unit Tests for Authentication and Security
認証・セキュリティのテスト

Tests for:
- JWT token generation and verification
- API key management
- Rate limiting
- Authentication decorators

Requirements: 9.5
"""

import pytest
import jwt
import time
import tempfile
import pathlib
from datetime import datetime, timedelta
from auth_manager import AuthManager, init_auth_manager, get_auth_manager


class TestAuthManager:
    """Test AuthManager class"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = pathlib.Path(self.temp_dir) / "auth_test.json"
        
        # Initialize auth manager with test config
        self.auth_manager = AuthManager(config_path=str(self.config_path))
    
    def teardown_method(self):
        """Cleanup test environment"""
        # Clean up temp files
        if self.config_path.exists():
            self.config_path.unlink()
        pathlib.Path(self.temp_dir).rmdir()
    
    def test_secret_key_generation(self):
        """Test secret key generation"""
        secret_key = self.auth_manager._generate_secret_key()
        
        assert secret_key is not None
        assert len(secret_key) > 20
        assert isinstance(secret_key, str)
    
    def test_secret_key_persistence(self):
        """Test secret key is saved and loaded correctly"""
        original_key = self.auth_manager.secret_key
        
        # Create new auth manager with same config path
        new_auth_manager = AuthManager(config_path=str(self.config_path))
        
        # Should load the same secret key
        assert new_auth_manager.secret_key == original_key
    
    def test_jwt_token_generation(self):
        """Test JWT token generation"""
        user_id = "test_user_123"
        username = "testuser"
        
        token = self.auth_manager.generate_jwt_token(user_id, username)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_jwt_token_verification_valid(self):
        """Test JWT token verification with valid token"""
        user_id = "test_user_123"
        username = "testuser"
        
        token = self.auth_manager.generate_jwt_token(user_id, username)
        
        is_valid, payload, error = self.auth_manager.verify_jwt_token(token)
        
        assert is_valid is True
        assert payload is not None
        assert payload['user_id'] == user_id
        assert payload['username'] == username
        assert error is None
    
    def test_jwt_token_verification_invalid(self):
        """Test JWT token verification with invalid token"""
        invalid_token = "invalid.token.here"
        
        is_valid, payload, error = self.auth_manager.verify_jwt_token(invalid_token)
        
        assert is_valid is False
        assert payload is None
        assert error is not None
        assert "Invalid token" in error
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        user_id = "test_user_123"
        username = "testuser"
        
        # Generate token that expires in 1 second
        token = self.auth_manager.generate_jwt_token(user_id, username, expires_in_hours=1/3600)
        
        # Wait for token to expire
        time.sleep(2)
        
        is_valid, payload, error = self.auth_manager.verify_jwt_token(token)
        
        assert is_valid is False
        assert payload is None
        assert error is not None
        assert "expired" in error.lower()
    
    def test_api_key_generation(self):
        """Test API key generation"""
        name = "Test API Key"
        description = "Test description"
        permissions = ["read", "write"]
        
        api_key = self.auth_manager.generate_api_key(name, description, permissions)
        
        assert api_key is not None
        assert isinstance(api_key, str)
        assert api_key.startswith("jad_")
        assert len(api_key) > 40
    
    def test_api_key_verification_valid(self):
        """Test API key verification with valid key"""
        name = "Test API Key"
        description = "Test description"
        permissions = ["read", "write"]
        
        api_key = self.auth_manager.generate_api_key(name, description, permissions)
        
        is_valid, metadata, error = self.auth_manager.verify_api_key(api_key)
        
        assert is_valid is True
        assert metadata is not None
        assert metadata['name'] == name
        assert metadata['description'] == description
        assert metadata['permissions'] == permissions
        assert error is None
    
    def test_api_key_verification_invalid(self):
        """Test API key verification with invalid key"""
        invalid_key = "jad_invalid_key_12345"
        
        is_valid, metadata, error = self.auth_manager.verify_api_key(invalid_key)
        
        assert is_valid is False
        assert metadata is None
        assert error is not None
        assert "not found" in error.lower()
    
    def test_api_key_verification_wrong_format(self):
        """Test API key verification with wrong format"""
        wrong_format_key = "wrong_format_key"
        
        is_valid, metadata, error = self.auth_manager.verify_api_key(wrong_format_key)
        
        assert is_valid is False
        assert metadata is None
        assert error is not None
        assert "Invalid" in error
    
    def test_api_key_usage_tracking(self):
        """Test API key usage tracking"""
        name = "Test API Key"
        api_key = self.auth_manager.generate_api_key(name, "Test")
        
        # Verify key multiple times
        for i in range(3):
            is_valid, metadata, error = self.auth_manager.verify_api_key(api_key)
            assert is_valid is True
        
        # Check usage count
        is_valid, metadata, error = self.auth_manager.verify_api_key(api_key)
        assert metadata['usage_count'] == 4  # 3 + 1 = 4
        assert metadata['last_used'] is not None
    
    def test_api_key_revocation(self):
        """Test API key revocation"""
        name = "Test API Key"
        api_key = self.auth_manager.generate_api_key(name, "Test")
        
        # Verify key works
        is_valid, metadata, error = self.auth_manager.verify_api_key(api_key)
        assert is_valid is True
        
        # Revoke key
        success = self.auth_manager.revoke_api_key(api_key)
        assert success is True
        
        # Verify key no longer works
        is_valid, metadata, error = self.auth_manager.verify_api_key(api_key)
        assert is_valid is False
    
    def test_list_api_keys(self):
        """Test listing API keys"""
        # Generate multiple API keys
        keys = []
        for i in range(3):
            name = f"Test Key {i}"
            api_key = self.auth_manager.generate_api_key(name, f"Description {i}")
            keys.append(name)
        
        # List keys
        key_list = self.auth_manager.list_api_keys()
        
        assert len(key_list) == 3
        assert all(key['name'] in keys for key in key_list)
        
        # Verify actual keys are not exposed
        for key_info in key_list:
            assert 'key_hash' in key_info
            assert key_info['key_hash'].endswith('...')
    
    def test_rate_limit_within_limit(self):
        """Test rate limiting within allowed limit"""
        identifier = "test_user_1"
        
        # Make requests within limit
        for i in range(5):
            is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier, 'default')
            assert is_allowed is True
            assert limit_info['allowed'] is True
            assert limit_info['remaining'] >= 0
    
    def test_rate_limit_exceeded(self):
        """Test rate limiting when limit is exceeded"""
        identifier = "test_user_2"
        limit_type = 'auth'  # 10 requests per minute
        
        # Make requests up to limit
        for i in range(10):
            is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier, limit_type)
            assert is_allowed is True
        
        # Next request should be blocked
        is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier, limit_type)
        assert is_allowed is False
        assert limit_info['allowed'] is False
        assert limit_info['remaining'] == 0
        assert 'retry_after' in limit_info
    
    def test_rate_limit_reset(self):
        """Test rate limit reset after window expires"""
        identifier = "test_user_3"
        
        # Configure short window for testing
        self.auth_manager.rate_limits['test'] = {'requests': 2, 'window': 1}
        
        # Make requests up to limit
        for i in range(2):
            is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier, 'test')
            assert is_allowed is True
        
        # Next request should be blocked
        is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier, 'test')
        assert is_allowed is False
        
        # Wait for window to expire
        time.sleep(2)
        
        # Should be allowed again
        is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier, 'test')
        assert is_allowed is True
    
    def test_rate_limit_different_identifiers(self):
        """Test rate limiting is per identifier"""
        identifier1 = "test_user_4"
        identifier2 = "test_user_5"
        
        # Configure limit
        self.auth_manager.rate_limits['test'] = {'requests': 2, 'window': 60}
        
        # Make requests for identifier1
        for i in range(2):
            is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier1, 'test')
            assert is_allowed is True
        
        # identifier1 should be blocked
        is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier1, 'test')
        assert is_allowed is False
        
        # identifier2 should still be allowed
        is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier2, 'test')
        assert is_allowed is True


class TestAuthenticationFailureCases:
    """Test authentication failure scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = pathlib.Path(self.temp_dir) / "auth_test.json"
        self.auth_manager = AuthManager(config_path=str(self.config_path))
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.config_path.exists():
            self.config_path.unlink()
        pathlib.Path(self.temp_dir).rmdir()
    
    def test_jwt_token_tampering(self):
        """Test JWT token tampering detection"""
        user_id = "test_user_123"
        username = "testuser"
        
        token = self.auth_manager.generate_jwt_token(user_id, username)
        
        # Tamper with token
        tampered_token = token[:-10] + "tampered123"
        
        is_valid, payload, error = self.auth_manager.verify_jwt_token(tampered_token)
        
        assert is_valid is False
        assert payload is None
        assert error is not None
    
    def test_jwt_token_wrong_secret(self):
        """Test JWT token verification with wrong secret"""
        user_id = "test_user_123"
        username = "testuser"
        
        # Generate token with different secret
        wrong_secret = "wrong_secret_key_12345"
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, wrong_secret, algorithm="HS256")
        
        # Try to verify with correct auth manager
        is_valid, payload, error = self.auth_manager.verify_jwt_token(token)
        
        assert is_valid is False
        assert payload is None
        assert error is not None
    
    def test_empty_api_key(self):
        """Test verification with empty API key"""
        is_valid, metadata, error = self.auth_manager.verify_api_key("")
        
        assert is_valid is False
        assert metadata is None
        assert error is not None
    
    def test_none_api_key(self):
        """Test verification with None API key"""
        is_valid, metadata, error = self.auth_manager.verify_api_key(None)
        
        assert is_valid is False
        assert metadata is None
        assert error is not None
    
    def test_revoke_nonexistent_key(self):
        """Test revoking a non-existent API key"""
        fake_key = "jad_nonexistent_key_12345"
        
        success = self.auth_manager.revoke_api_key(fake_key)
        
        assert success is False
    
    def test_rate_limit_negative_values(self):
        """Test rate limiting handles edge cases"""
        identifier = "test_user_edge"
        
        # Should not crash with edge cases
        is_allowed, limit_info = self.auth_manager.check_rate_limit(identifier, 'nonexistent_type')
        
        # Should fall back to default
        assert is_allowed is True
        assert limit_info['limit'] == 100  # default limit


class TestGlobalAuthManager:
    """Test global auth manager initialization"""
    
    def test_init_and_get_auth_manager(self):
        """Test global auth manager initialization"""
        temp_dir = tempfile.mkdtemp()
        config_path = pathlib.Path(temp_dir) / "auth_global_test.json"
        
        try:
            # Initialize global auth manager
            auth_manager = init_auth_manager(config_path=str(config_path))
            
            assert auth_manager is not None
            assert isinstance(auth_manager, AuthManager)
            
            # Get global auth manager
            retrieved_manager = get_auth_manager()
            
            assert retrieved_manager is auth_manager
            
        finally:
            # Cleanup
            if config_path.exists():
                config_path.unlink()
            pathlib.Path(temp_dir).rmdir()


def test_jwt_token_payload_structure():
    """Test JWT token contains required fields"""
    temp_dir = tempfile.mkdtemp()
    config_path = pathlib.Path(temp_dir) / "auth_payload_test.json"
    
    try:
        auth_manager = AuthManager(config_path=str(config_path))
        
        user_id = "test_user_123"
        username = "testuser"
        
        token = auth_manager.generate_jwt_token(user_id, username)
        is_valid, payload, error = auth_manager.verify_jwt_token(token)
        
        assert is_valid is True
        assert 'user_id' in payload
        assert 'username' in payload
        assert 'exp' in payload
        assert 'iat' in payload
        
        # Verify expiration is in the future
        exp_timestamp = payload['exp']
        assert exp_timestamp > datetime.utcnow().timestamp()
        
    finally:
        if config_path.exists():
            config_path.unlink()
        pathlib.Path(temp_dir).rmdir()


def test_api_key_format():
    """Test API key format is consistent"""
    temp_dir = tempfile.mkdtemp()
    config_path = pathlib.Path(temp_dir) / "auth_format_test.json"
    
    try:
        auth_manager = AuthManager(config_path=str(config_path))
        
        # Generate multiple keys
        keys = []
        for i in range(5):
            key = auth_manager.generate_api_key(f"Key {i}", "Test")
            keys.append(key)
        
        # All keys should have consistent format
        for key in keys:
            assert key.startswith("jad_")
            assert len(key) > 40
            assert "_" in key
            
        # All keys should be unique
        assert len(set(keys)) == 5
        
    finally:
        if config_path.exists():
            config_path.unlink()
        pathlib.Path(temp_dir).rmdir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
