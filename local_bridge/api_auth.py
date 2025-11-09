"""
Authentication API Endpoints for Junmai AutoDev
認証APIエンドポイント

This module provides REST API endpoints for:
- User authentication (JWT)
- API key management
- Token refresh

Requirements: 9.5
"""

from flask import Blueprint, jsonify, request
from auth_manager import get_auth_manager, jwt_required, api_key_required, rate_limit
from logging_system import get_logging_system
import secrets

auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')
logging_system = get_logging_system()


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_api_bp.route("/login", methods=["POST"])
@rate_limit('auth')
def login():
    """
    User login endpoint
    
    Request body:
    - username: Username (required)
    - password: Password (required)
    
    Returns:
        JWT token
    
    Note: This is a simplified implementation. In production, you would
    verify credentials against a user database with hashed passwords.
    """
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"error": "username and password are required"}), 400
        
        username = data['username']
        password = data['password']
        
        # TODO: In production, verify against user database
        # For now, accept any credentials for local development
        # This should be replaced with proper user authentication
        
        # Simple validation
        if not username or not password:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # For local development, accept "admin" user
        if username != "admin":
            return jsonify({"error": "Invalid credentials"}), 401
        
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        # Generate user ID (in production, this would come from database)
        user_id = f"user_{secrets.token_hex(8)}"
        
        # Generate JWT token
        token = auth_manager.generate_jwt_token(user_id, username)
        
        logging_system.log("INFO", "User logged in", username=username, user_id=user_id)
        
        return jsonify({
            "token": token,
            "token_type": "Bearer",
            "expires_in": 86400,  # 24 hours in seconds
            "user": {
                "id": user_id,
                "username": username
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Login failed", exception=e)
        return jsonify({"error": f"Login failed: {e}"}), 500


@auth_api_bp.route("/verify", methods=["GET"])
@jwt_required
def verify_token():
    """
    Verify JWT token
    
    Headers:
    - Authorization: Bearer <token>
    
    Returns:
        Token validity and user information
    """
    try:
        from flask import g
        
        return jsonify({
            "valid": True,
            "user": {
                "id": g.user_id,
                "username": g.username
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Token verification failed", exception=e)
        return jsonify({"error": f"Verification failed: {e}"}), 500


@auth_api_bp.route("/refresh", methods=["POST"])
@jwt_required
def refresh_token():
    """
    Refresh JWT token
    
    Headers:
    - Authorization: Bearer <token>
    
    Returns:
        New JWT token
    """
    try:
        from flask import g
        
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        # Generate new token
        new_token = auth_manager.generate_jwt_token(g.user_id, g.username)
        
        logging_system.log("INFO", "Token refreshed", user_id=g.user_id)
        
        return jsonify({
            "token": new_token,
            "token_type": "Bearer",
            "expires_in": 86400
        }), 200
        
    except Exception as e:
        logging_system.log_error("Token refresh failed", exception=e)
        return jsonify({"error": f"Token refresh failed: {e}"}), 500


# ============================================================================
# API KEY MANAGEMENT ENDPOINTS
# ============================================================================

@auth_api_bp.route("/apikeys", methods=["GET"])
@jwt_required
def list_api_keys():
    """
    List all API keys
    
    Headers:
    - Authorization: Bearer <token>
    
    Returns:
        List of API keys (without revealing actual keys)
    """
    try:
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        keys = auth_manager.list_api_keys()
        
        logging_system.log("INFO", "API keys listed", count=len(keys))
        
        return jsonify({
            "api_keys": keys,
            "count": len(keys)
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to list API keys", exception=e)
        return jsonify({"error": f"Failed to list API keys: {e}"}), 500


@auth_api_bp.route("/apikeys", methods=["POST"])
@jwt_required
def create_api_key():
    """
    Create a new API key
    
    Headers:
    - Authorization: Bearer <token>
    
    Request body:
    - name: API key name (required)
    - description: API key description (optional)
    - permissions: List of permissions (optional)
    
    Returns:
        New API key (only shown once)
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({"error": "name is required"}), 400
        
        name = data['name']
        description = data.get('description', '')
        permissions = data.get('permissions', ['read', 'write'])
        
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        # Generate API key
        api_key = auth_manager.generate_api_key(name, description, permissions)
        
        logging_system.log("INFO", "API key created", name=name)
        
        return jsonify({
            "message": "API key created successfully",
            "api_key": api_key,
            "name": name,
            "description": description,
            "permissions": permissions,
            "warning": "This is the only time the API key will be shown. Please save it securely."
        }), 201
        
    except Exception as e:
        logging_system.log_error("Failed to create API key", exception=e)
        return jsonify({"error": f"Failed to create API key: {e}"}), 500


@auth_api_bp.route("/apikeys/<string:key_identifier>", methods=["DELETE"])
@jwt_required
def revoke_api_key(key_identifier: str):
    """
    Revoke an API key
    
    Headers:
    - Authorization: Bearer <token>
    
    Path parameters:
    - key_identifier: API key or key hash
    
    Returns:
        Success message
    """
    try:
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        # Try to revoke the key
        success = auth_manager.revoke_api_key(key_identifier)
        
        if success:
            logging_system.log("INFO", "API key revoked", key_identifier=key_identifier[:16])
            return jsonify({
                "message": "API key revoked successfully"
            }), 200
        else:
            return jsonify({"error": "API key not found"}), 404
        
    except Exception as e:
        logging_system.log_error("Failed to revoke API key", exception=e)
        return jsonify({"error": f"Failed to revoke API key: {e}"}), 500


@auth_api_bp.route("/apikeys/verify", methods=["GET"])
@api_key_required
def verify_api_key():
    """
    Verify API key
    
    Headers:
    - X-API-Key: <api_key>
    
    Or query parameter:
    - api_key: <api_key>
    
    Returns:
        API key validity and metadata
    """
    try:
        from flask import g
        
        return jsonify({
            "valid": True,
            "api_key": {
                "name": g.api_key_name,
                "permissions": g.api_key_permissions
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("API key verification failed", exception=e)
        return jsonify({"error": f"Verification failed: {e}"}), 500


# ============================================================================
# RATE LIMIT INFO ENDPOINT
# ============================================================================

@auth_api_bp.route("/ratelimit", methods=["GET"])
def get_rate_limit_info():
    """
    Get rate limit information
    
    Returns:
        Rate limit configuration
    """
    try:
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        return jsonify({
            "rate_limits": auth_manager.rate_limits,
            "message": "Rate limits are applied per IP address, user ID, or API key"
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get rate limit info", exception=e)
        return jsonify({"error": f"Failed to get rate limit info: {e}"}), 500


# ============================================================================
# SECURITY INFO ENDPOINT
# ============================================================================

@auth_api_bp.route("/info", methods=["GET"])
def get_auth_info():
    """
    Get authentication system information
    
    Returns:
        Authentication configuration info (public information only)
    """
    try:
        auth_manager = get_auth_manager()
        if not auth_manager:
            return jsonify({"error": "Authentication not configured"}), 500
        
        return jsonify({
            "authentication": {
                "jwt_enabled": True,
                "api_key_enabled": True,
                "jwt_expiration_hours": 24,
                "supported_algorithms": ["HS256"]
            },
            "rate_limiting": {
                "enabled": True,
                "limits": {
                    "default": "100 requests per minute",
                    "auth": "10 requests per minute",
                    "upload": "20 requests per minute"
                }
            },
            "cors": {
                "enabled": True,
                "allowed_origins": ["http://localhost:*", "http://127.0.0.1:*"]
            }
        }), 200
        
    except Exception as e:
        logging_system.log_error("Failed to get auth info", exception=e)
        return jsonify({"error": f"Failed to get auth info: {e}"}), 500
