"""
Verification script for authentication tests
認証テストの検証スクリプト
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_tests():
    """Verify authentication test modules can be imported"""
    print("=" * 70)
    print("Verifying Authentication Test Modules")
    print("=" * 70)
    
    errors = []
    
    # Check test_auth.py
    print("\n1. Checking test_auth.py...")
    try:
        import test_auth
        print("   ✓ test_auth.py imported successfully")
        
        # Count test classes and methods
        test_classes = [
            'TestAuthManager',
            'TestAuthenticationFailureCases',
            'TestGlobalAuthManager'
        ]
        
        for cls_name in test_classes:
            if hasattr(test_auth, cls_name):
                print(f"   ✓ Found test class: {cls_name}")
            else:
                errors.append(f"Missing test class: {cls_name}")
                
    except Exception as e:
        errors.append(f"Failed to import test_auth.py: {e}")
        print(f"   ✗ Error: {e}")
    
    # Check test_auth_api.py
    print("\n2. Checking test_auth_api.py...")
    try:
        import test_auth_api
        print("   ✓ test_auth_api.py imported successfully")
        
        # Count test classes
        test_classes = [
            'TestLoginEndpoint',
            'TestTokenVerification',
            'TestTokenRefresh',
            'TestAPIKeyManagement',
            'TestRateLimiting',
            'TestAuthInfo',
            'TestCORSHeaders'
        ]
        
        for cls_name in test_classes:
            if hasattr(test_auth_api, cls_name):
                print(f"   ✓ Found test class: {cls_name}")
            else:
                errors.append(f"Missing test class: {cls_name}")
                
    except Exception as e:
        errors.append(f"Failed to import test_auth_api.py: {e}")
        print(f"   ✗ Error: {e}")
    
    # Check dependencies
    print("\n3. Checking dependencies...")
    dependencies = [
        ('pytest', 'Testing framework'),
        ('jwt', 'JWT token handling (PyJWT)'),
        ('flask', 'Flask web framework'),
        ('auth_manager', 'Authentication manager module'),
        ('api_auth', 'Authentication API module')
    ]
    
    for module_name, description in dependencies:
        try:
            if module_name == 'jwt':
                import jwt
            elif module_name == 'pytest':
                import pytest
            elif module_name == 'flask':
                import flask
            elif module_name == 'auth_manager':
                import auth_manager
            elif module_name == 'api_auth':
                import api_auth
            print(f"   ✓ {description}: {module_name}")
        except ImportError:
            errors.append(f"Missing dependency: {module_name} ({description})")
            print(f"   ✗ Missing: {module_name} ({description})")
    
    # Summary
    print("\n" + "=" * 70)
    if errors:
        print("✗ Verification failed with errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nTo fix:")
        print("  pip install -r requirements.txt")
        print("=" * 70)
        return 1
    else:
        print("✓ All authentication test modules verified successfully!")
        print("\nTest Coverage:")
        print("  - JWT token generation and verification")
        print("  - API key management")
        print("  - Rate limiting")
        print("  - Authentication failure cases")
        print("  - API endpoint integration tests")
        print("\nTo run tests:")
        print("  pytest test_auth.py -v")
        print("  pytest test_auth_api.py -v")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(verify_tests())
