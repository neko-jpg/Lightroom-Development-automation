"""
Simple test runner for authentication tests
認証テストの実行スクリプト
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Run authentication tests"""
    print("=" * 70)
    print("Running Authentication Unit Tests")
    print("=" * 70)
    
    try:
        # Import test modules
        import test_auth
        import test_auth_api
        
        # Try to use pytest if available
        try:
            import pytest
            print("\nUsing pytest to run tests...\n")
            
            # Run unit tests
            print("Running test_auth.py...")
            result1 = pytest.main(['-v', 'test_auth.py'])
            
            # Run API tests
            print("\nRunning test_auth_api.py...")
            result2 = pytest.main(['-v', 'test_auth_api.py'])
            
            if result1 == 0 and result2 == 0:
                print("\n" + "=" * 70)
                print("✓ All authentication tests passed!")
                print("=" * 70)
                return 0
            else:
                print("\n" + "=" * 70)
                print("✗ Some tests failed")
                print("=" * 70)
                return 1
                
        except ImportError:
            print("pytest not found. Please install: pip install pytest")
            print("\nTo run tests manually:")
            print("  pip install pytest")
            print("  pytest test_auth.py -v")
            print("  pytest test_auth_api.py -v")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
