"""
Example Usage of Authentication System
認証システムの使用例

This script demonstrates how to use the authentication system
for the Junmai AutoDev API.

Requirements: 9.5
"""

import requests
import json
from typing import Optional


class JunmaiAuthClient:
    """
    Example client for Junmai AutoDev API with authentication
    """
    
    def __init__(self, base_url: str = "http://localhost:5100"):
        """
        Initialize client
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url
        self.token: Optional[str] = None
        self.api_key: Optional[str] = None
    
    def login(self, username: str, password: str) -> dict:
        """
        Login and get JWT token
        
        Args:
            username: Username
            password: Password
        
        Returns:
            Login response with token
        """
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            print(f"✓ Logged in as {data['user']['username']}")
            print(f"  Token expires in: {data['expires_in']} seconds")
            return data
        else:
            print(f"✗ Login failed: {response.json()}")
            return {}
    
    def verify_token(self) -> bool:
        """
        Verify current JWT token
        
        Returns:
            True if token is valid
        """
        if not self.token:
            print("✗ No token available")
            return False
        
        response = requests.get(
            f"{self.base_url}/api/auth/verify",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Token is valid for user: {data['user']['username']}")
            return True
        else:
            print(f"✗ Token verification failed: {response.json()}")
            return False
    
    def refresh_token(self) -> bool:
        """
        Refresh JWT token
        
        Returns:
            True if refresh successful
        """
        if not self.token:
            print("✗ No token to refresh")
            return False
        
        response = requests.post(
            f"{self.base_url}/api/auth/refresh",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            print(f"✓ Token refreshed successfully")
            return True
        else:
            print(f"✗ Token refresh failed: {response.json()}")
            return False
    
    def create_api_key(self, name: str, description: str = "") -> Optional[str]:
        """
        Create a new API key
        
        Args:
            name: API key name
            description: API key description
        
        Returns:
            API key string or None
        """
        if not self.token:
            print("✗ Login required to create API key")
            return None
        
        response = requests.post(
            f"{self.base_url}/api/auth/apikeys",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"name": name, "description": description}
        )
        
        if response.status_code == 201:
            data = response.json()
            self.api_key = data['api_key']
            print(f"✓ API key created: {name}")
            print(f"  Key: {self.api_key}")
            print(f"  ⚠ Save this key - it won't be shown again!")
            return self.api_key
        else:
            print(f"✗ API key creation failed: {response.json()}")
            return None
    
    def list_api_keys(self) -> list:
        """
        List all API keys
        
        Returns:
            List of API keys
        """
        if not self.token:
            print("✗ Login required to list API keys")
            return []
        
        response = requests.get(
            f"{self.base_url}/api/auth/apikeys",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data['count']} API keys:")
            for key in data['api_keys']:
                print(f"  - {key['name']}: {key['key_hash']}")
                print(f"    Created: {key['created_at']}")
                print(f"    Usage: {key['usage_count']} times")
            return data['api_keys']
        else:
            print(f"✗ Failed to list API keys: {response.json()}")
            return []
    
    def verify_api_key(self, api_key: Optional[str] = None) -> bool:
        """
        Verify API key
        
        Args:
            api_key: API key to verify (uses self.api_key if not provided)
        
        Returns:
            True if API key is valid
        """
        key = api_key or self.api_key
        if not key:
            print("✗ No API key available")
            return False
        
        response = requests.get(
            f"{self.base_url}/api/auth/apikeys/verify",
            headers={"X-API-Key": key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API key is valid: {data['api_key']['name']}")
            print(f"  Permissions: {', '.join(data['api_key']['permissions'])}")
            return True
        else:
            print(f"✗ API key verification failed: {response.json()}")
            return False
    
    def get_sessions_with_jwt(self) -> list:
        """
        Get sessions using JWT authentication
        
        Returns:
            List of sessions
        """
        if not self.token:
            print("✗ Login required")
            return []
        
        response = requests.get(
            f"{self.base_url}/api/sessions",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {data['count']} sessions using JWT")
            return data['sessions']
        else:
            print(f"✗ Failed to get sessions: {response.json()}")
            return []
    
    def get_photos_with_api_key(self) -> list:
        """
        Get photos using API key authentication
        
        Returns:
            List of photos
        """
        if not self.api_key:
            print("✗ API key required")
            return []
        
        response = requests.get(
            f"{self.base_url}/api/photos",
            headers={"X-API-Key": self.api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {data['count']} photos using API key")
            return data['photos']
        else:
            print(f"✗ Failed to get photos: {response.json()}")
            return []
    
    def get_auth_info(self) -> dict:
        """
        Get authentication system information
        
        Returns:
            Authentication info
        """
        response = requests.get(f"{self.base_url}/api/auth/info")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Authentication System Info:")
            print(f"  JWT Enabled: {data['authentication']['jwt_enabled']}")
            print(f"  API Key Enabled: {data['authentication']['api_key_enabled']}")
            print(f"  Rate Limiting: {data['rate_limiting']['enabled']}")
            print(f"  CORS: {data['cors']['enabled']}")
            return data
        else:
            print(f"✗ Failed to get auth info: {response.json()}")
            return {}
    
    def demonstrate_rate_limiting(self):
        """
        Demonstrate rate limiting by making multiple requests
        """
        print("\n--- Demonstrating Rate Limiting ---")
        print("Making 12 rapid requests to auth endpoint (limit: 10/min)...")
        
        for i in range(12):
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "test", "password": "test"}
            )
            
            if response.status_code == 429:
                print(f"✓ Request {i+1}: Rate limit exceeded (as expected)")
                print(f"  Retry after: {response.json()['retry_after']} seconds")
                break
            else:
                remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
                print(f"  Request {i+1}: OK (Remaining: {remaining})")


def main():
    """
    Main demonstration function
    """
    print("=" * 60)
    print("Junmai AutoDev Authentication System Demo")
    print("=" * 60)
    
    # Initialize client
    client = JunmaiAuthClient()
    
    # 1. Get system info
    print("\n1. Getting Authentication System Info")
    print("-" * 60)
    client.get_auth_info()
    
    # 2. Login with JWT
    print("\n2. Login with JWT")
    print("-" * 60)
    client.login("admin", "password")
    
    # 3. Verify token
    print("\n3. Verify JWT Token")
    print("-" * 60)
    client.verify_token()
    
    # 4. Create API key
    print("\n4. Create API Key")
    print("-" * 60)
    client.create_api_key("Demo API Key", "Created by example script")
    
    # 5. List API keys
    print("\n5. List API Keys")
    print("-" * 60)
    client.list_api_keys()
    
    # 6. Verify API key
    print("\n6. Verify API Key")
    print("-" * 60)
    client.verify_api_key()
    
    # 7. Use JWT to access API
    print("\n7. Access API with JWT")
    print("-" * 60)
    client.get_sessions_with_jwt()
    
    # 8. Use API key to access API
    print("\n8. Access API with API Key")
    print("-" * 60)
    client.get_photos_with_api_key()
    
    # 9. Refresh token
    print("\n9. Refresh JWT Token")
    print("-" * 60)
    client.refresh_token()
    
    # 10. Demonstrate rate limiting
    print("\n10. Rate Limiting Demo")
    print("-" * 60)
    client.demonstrate_rate_limiting()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("- JWT tokens are used for user authentication")
    print("- API keys are used for programmatic access")
    print("- Rate limiting prevents abuse")
    print("- Both authentication methods work seamlessly")
    print("\nFor more information, see:")
    print("- AUTH_IMPLEMENTATION.md (detailed documentation)")
    print("- AUTH_QUICK_START.md (quick reference)")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server")
        print("  Make sure the server is running: python local_bridge/app.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")
