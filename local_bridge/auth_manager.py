"""
Authentication and Security Manager for Junmai AutoDev
認証・セキュリティ管理

This module provides:
- JWT authentication
- API key management
- Rate limiting
- CORS configuration

Requirements: 9.5
"""

import jwt
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from typing import Dict, Optional, Tuple, List
import json
import pathlib
from logging_system import get_logging_system

logging_system = get_logging_system()

# JWT Configuration
JWT_SECRET_KEY = None  # Will be initialized from config
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Rate limiting storage (in-memory for simplicity, could use Redis for production)
rate_limit_storage = {}


class AuthManager:
    """
    Authentication and security manager
    """
    
    def __init__(self, secret_key: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize authentication manager
        
        Args:
            secret_key: JWT secret key (generated if not provided)
            config_path: Path to auth configuration file
        """
        self.config_path = pathlib.Path(config_path) if config_path else pathlib.Path(__file__).parent / "config" / "auth.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or generate secret key
        if secret_key:
            self.secret_key = secret_key
        else:
            self.secret_key = self._load_or_generate_secret_key()
        
        # Load API keys
        self.api_keys = self._load_api_keys()
        
        # Rate limiting configuration
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 10, 'window': 60},      # 10 auth requests per minute
            'upload': {'requests': 20, 'window': 60}     # 20 upload requests per minute
        }
        
        logging_system.log("INFO", "AuthManager initialized", api_key_count=len(self.api_keys))
    
    def _load_or_generate_secret_key(self) -> str:
        """
        Load existing secret key or generate a new one
        
        Returns:
            Secret key string
        """
        config_file = self.config_path
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('secret_key', self._generate_secret_key())
            except Exception as e:
                logging_system.log_error("Failed to load secret key, generating new one", exception=e)
        
        # Generate new secret key
        secret_key = self._generate_secret_key()
        self._save_config({'secret_key': secret_key, 'api_keys': {}})
        return secret_key
    
    def _generate_secret_key(self) -> str:
        """
        Generate a secure random secret key
        
        Returns:
            Secret key string
        """
        return secrets.token_urlsafe(32)
    
    def _load_api_keys(self) -> Dict[str, Dict]:
        """
        Load API keys from configuration
        
        Returns:
            Dictionary of API keys with metadata
        """
        config_file = self.config_path
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('api_keys', {})
            except Exception as e:
                logging_system.log_error("Failed to load API keys", exception=e)
        
        return {}
    
    def _save_config(self, config: Dict):
        """
        Save configuration to file
        
        Args:
            config: Configuration dictionary
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logging_system.log("INFO", "Auth configuration saved")
        except Exception as e:
            logging_system.log_error("Failed to save auth configuration", exception=e)
    
    def generate_jwt_token(self, user_id: str, username: str, expires_in_hours: int = JWT_EXPIRATION_HOURS) -> str:
        """
        Generate JWT token
        
        Args:
            user_id: User ID
            username: Username
            expires_in_hours: Token expiration time in hours
        
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=JWT_ALGORITHM)
        
        logging_system.log("INFO", "JWT token generated", user_id=user_id, username=username)
        
        return token
    
    def verify_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            Tuple of (is_valid, payload, error_message)
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[JWT_ALGORITHM])
            return True, payload, None
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
    
    def generate_api_key(self, name: str, description: str = "", permissions: List[str] = None) -> str:
        """
        Generate a new API key
        
        Args:
            name: API key name
            description: API key description
            permissions: List of permissions (optional)
        
        Returns:
            API key string
        """
        # Generate secure random API key
        api_key = f"jad_{secrets.token_urlsafe(32)}"
        
        # Hash the API key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store API key metadata
        self.api_keys[key_hash] = {
            'name': name,
            'description': description,
            'permissions': permissions or ['read', 'write'],
            'created_at': datetime.utcnow().isoformat(),
            'last_used': None,
            'usage_count': 0
        }
        
        # Save to config
        config = {
            'secret_key': self.secret_key,
            'api_keys': self.api_keys
        }
        self._save_config(config)
        
        logging_system.log("INFO", "API key generated", name=name, key_hash=key_hash[:16])
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify API key
        
        Args:
            api_key: API key string
        
        Returns:
            Tuple of (is_valid, metadata, error_message)
        """
        if not api_key or not api_key.startswith('jad_'):
            return False, None, "Invalid API key format"
        
        # Hash the provided API key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Check if key exists
        if key_hash not in self.api_keys:
            return False, None, "API key not found"
        
        # Update usage statistics
        self.api_keys[key_hash]['last_used'] = datetime.utcnow().isoformat()
        self.api_keys[key_hash]['usage_count'] += 1
        
        # Save updated config (async in production)
        config = {
            'secret_key': self.secret_key,
            'api_keys': self.api_keys
        }
        self._save_config(config)
        
        return True, self.api_keys[key_hash], None
    
    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key
        
        Args:
            api_key: API key string
        
        Returns:
            True if revoked successfully
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash in self.api_keys:
            del self.api_keys[key_hash]
            
            # Save updated config
            config = {
                'secret_key': self.secret_key,
                'api_keys': self.api_keys
            }
            self._save_config(config)
            
            logging_system.log("INFO", "API key revoked", key_hash=key_hash[:16])
            return True
        
        return False
    
    def list_api_keys(self) -> List[Dict]:
        """
        List all API keys (without revealing the actual keys)
        
        Returns:
            List of API key metadata
        """
        keys_list = []
        for key_hash, metadata in self.api_keys.items():
            keys_list.append({
                'key_hash': key_hash[:16] + '...',  # Show only first 16 chars
                'name': metadata['name'],
                'description': metadata['description'],
                'permissions': metadata['permissions'],
                'created_at': metadata['created_at'],
                'last_used': metadata['last_used'],
                'usage_count': metadata['usage_count']
            })
        
        return keys_list
    
    def check_rate_limit(self, identifier: str, limit_type: str = 'default') -> Tuple[bool, Dict]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (IP address, user ID, API key hash)
            limit_type: Type of rate limit to apply
        
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        current_time = time.time()
        limit_config = self.rate_limits.get(limit_type, self.rate_limits['default'])
        
        window = limit_config['window']
        max_requests = limit_config['requests']
        
        # Get or create rate limit entry
        if identifier not in rate_limit_storage:
            rate_limit_storage[identifier] = {
                'requests': [],
                'blocked_until': None
            }
        
        entry = rate_limit_storage[identifier]
        
        # Check if currently blocked
        if entry['blocked_until'] and current_time < entry['blocked_until']:
            remaining_time = int(entry['blocked_until'] - current_time)
            return False, {
                'allowed': False,
                'limit': max_requests,
                'remaining': 0,
                'reset_in': remaining_time,
                'retry_after': remaining_time
            }
        
        # Clean up old requests outside the window
        entry['requests'] = [req_time for req_time in entry['requests'] if current_time - req_time < window]
        
        # Check if limit exceeded
        if len(entry['requests']) >= max_requests:
            # Block for the remainder of the window
            entry['blocked_until'] = current_time + window
            return False, {
                'allowed': False,
                'limit': max_requests,
                'remaining': 0,
                'reset_in': window,
                'retry_after': window
            }
        
        # Add current request
        entry['requests'].append(current_time)
        
        return True, {
            'allowed': True,
            'limit': max_requests,
            'remaining': max_requests - len(entry['requests']),
            'reset_in': window
        }


# Global auth manager instance
_auth_manager = None


def init_auth_manager(secret_key: Optional[str] = None, config_path: Optional[str] = None) -> AuthManager:
    """
    Initialize global auth manager
    
    Args:
        secret_key: JWT secret key
        config_path: Path to auth configuration file
    
    Returns:
        AuthManager instance
    """
    global _auth_manager
    _auth_manager = AuthManager(secret_key=secret_key, config_path=config_path)
    return _auth_manager


def get_auth_manager() -> Optional[AuthManager]:
    """
    Get global auth manager instance
    
    Returns:
        AuthManager instance or None
    """
    return _auth_manager


# Flask decorators for authentication

def jwt_required(f):
    """
    Decorator to require JWT authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        
        # Extract token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid Authorization header format. Expected: Bearer <token>"}), 401
        
        token = parts[1]
        
        # Verify token
        is_valid, payload, error = auth_manager.verify_jwt_token(token)
        if not is_valid:
            return jsonify({"error": f"Authentication failed: {error}"}), 401
        
        # Store user info in request context
        g.user_id = payload['user_id']
        g.username = payload['username']
        
        return f(*args, **kwargs)
    
    return decorated_function


def api_key_required(f):
    """
    Decorator to require API key authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key:
            return jsonify({"error": "Missing API key"}), 401
        
        # Verify API key
        is_valid, metadata, error = auth_manager.verify_api_key(api_key)
        if not is_valid:
            return jsonify({"error": f"Authentication failed: {error}"}), 401
        
        # Store API key info in request context
        g.api_key_name = metadata['name']
        g.api_key_permissions = metadata['permissions']
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(limit_type: str = 'default'):
    """
    Decorator to apply rate limiting
    
    Args:
        limit_type: Type of rate limit to apply
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_manager = get_auth_manager()
            if not auth_manager:
                # If auth not configured, skip rate limiting
                return f(*args, **kwargs)
            
            # Get identifier (IP address, user ID, or API key)
            identifier = request.remote_addr
            if hasattr(g, 'user_id'):
                identifier = g.user_id
            elif hasattr(g, 'api_key_name'):
                identifier = g.api_key_name
            
            # Check rate limit
            is_allowed, limit_info = auth_manager.check_rate_limit(identifier, limit_type)
            
            # Add rate limit headers
            response_headers = {
                'X-RateLimit-Limit': str(limit_info['limit']),
                'X-RateLimit-Remaining': str(limit_info['remaining']),
                'X-RateLimit-Reset': str(limit_info['reset_in'])
            }
            
            if not is_allowed:
                response = jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": limit_info['retry_after']
                })
                response.headers.update(response_headers)
                response.headers['Retry-After'] = str(limit_info['retry_after'])
                return response, 429
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Add rate limit headers to response
            if isinstance(result, tuple):
                response, status_code = result
                if hasattr(response, 'headers'):
                    response.headers.update(response_headers)
                return response, status_code
            else:
                if hasattr(result, 'headers'):
                    result.headers.update(response_headers)
                return result
        
        return decorated_function
    
    return decorator


def configure_cors(app):
    """
    Configure CORS for Flask app
    
    Args:
        app: Flask application instance
    """
    from flask_cors import CORS
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:*", "http://127.0.0.1:*"],  # Allow local development
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
            "expose_headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    logging_system.log("INFO", "CORS configured for API endpoints")
