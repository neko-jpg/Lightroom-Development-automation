"""
Integration Test Runner
統合テスト実行スクリプト

Runs all integration tests for the Junmai AutoDev system
Requirements: 全要件
"""

import sys
import pytest
import logging
from pathlib import Path
from datetime import datetime


def setup_logging():
    """Setup logging for test execution"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'integration_tests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_e2e_tests(logger):
    """Run End-to-End integration tests"""
    print_header("End-to-End Integration Tests")
    logger.info("Starting E2E integration tests")
    
    result = pytest.main([
        'test_integration_e2e.py',
        '-v',
        '--tb=short',
        '--color=yes',
        '--junit-xml=test_results_e2e.xml'
    ])
    
    logger.info(f"E2E tests completed with result: {result}")
    return result


def run_api_tests(logger):
    """Run API integration tests"""
    print_header("API Integration Tests")
    logger.info("Starting API integration tests")
    
    result = pytest.main([
        'test_integration_api.py',
        '-v',
        '--tb=short',
        '--color=yes',
        '--junit-xml=test_results_api.xml'
    ])
    
    logger.info(f"API tests completed with result: {result}")
    return result


def run_websocket_tests(logger):
    """Run WebSocket integration tests"""
    print_header("WebSocket Integration Tests")
    logger.info("Starting WebSocket integration tests")
    
    result = pytest.main([
        'test_integration_websocket.py',
        '-v',
        '--tb=short',
        '--color=yes',
        '--junit-xml=test_results_websocket.xml'
    ])
    
    logger.info(f"WebSocket tests completed with result: {result}")
    return result


def run_all_integration_tests(logger):
    """Run all integration tests"""
    print_header("Running All Integration Tests")
    logger.info("Starting all integration tests")
    
    result = pytest.main([
        'test_integration_e2e.py',
        'test_integration_api.py',
        'test_integration_websocket.py',
        '-v',
        '--tb=short',
        '--color=yes',
        '--junit-xml=test_results_all.xml',
        '--html=test_report.html',
        '--self-contained-html'
    ])
    
    logger.info(f"All integration tests completed with result: {result}")
    return result


def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    test_names = ['E2E Tests', 'API Tests', 'WebSocket Tests']
    
    for name, result in zip(test_names, results):
        status = "✓ PASSED" if result == 0 else "✗ FAILED"
        print(f"{name:30} {status}")
    
    print("\n" + "=" * 70)
    
    all_passed = all(r == 0 for r in results)
    if all_passed:
        print("  ✓ ALL INTEGRATION TESTS PASSED")
    else:
        print("  ✗ SOME INTEGRATION TESTS FAILED")
    print("=" * 70 + "\n")
    
    return all_passed


def main():
    """Main test runner"""
    logger = setup_logging()
    
    print_header("Junmai AutoDev - Integration Test Suite")
    logger.info("Integration test suite started")
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'e2e':
            result = run_e2e_tests(logger)
            sys.exit(result)
        elif test_type == 'api':
            result = run_api_tests(logger)
            sys.exit(result)
        elif test_type == 'websocket':
            result = run_websocket_tests(logger)
            sys.exit(result)
        elif test_type == 'all':
            result = run_all_integration_tests(logger)
            sys.exit(result)
        else:
            print(f"Unknown test type: {test_type}")
            print("Usage: python run_integration_tests.py [e2e|api|websocket|all]")
            sys.exit(1)
    
    # Run all tests by default
    results = []
    
    try:
        # Run E2E tests
        results.append(run_e2e_tests(logger))
        
        # Run API tests
        results.append(run_api_tests(logger))
        
        # Run WebSocket tests
        results.append(run_websocket_tests(logger))
        
    except KeyboardInterrupt:
        logger.warning("Test execution interrupted by user")
        print("\n\nTest execution interrupted!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed with error: {e}", exc_info=True)
        print(f"\n\nTest execution failed: {e}")
        sys.exit(1)
    
    # Print summary
    all_passed = print_summary(results)
    
    logger.info(f"Integration test suite completed. All passed: {all_passed}")
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
