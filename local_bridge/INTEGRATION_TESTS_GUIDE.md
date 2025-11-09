# Integration Tests Guide
統合テストガイド

## Overview

This document describes the integration test suite for the Junmai AutoDev system. The integration tests verify that all system components work together correctly and that the complete workflows function as expected.

## Test Categories

### 1. End-to-End (E2E) Tests
**File**: `test_integration_e2e.py`

Tests complete workflows from file import to export:
- Complete workflow: Import → Analyze → Select → Develop → Export
- Workflow with photo rejection
- Workflow with preset modification
- Batch processing of multiple photos
- Batch export functionality
- Error recovery and retry logic
- Performance metrics tracking

**Requirements Covered**: 全要件 (All requirements)

### 2. API Integration Tests
**File**: `test_integration_api.py`

Tests API endpoint integration and data flow:
- Session management (CRUD operations)
- Photo management (filtering, updates)
- Job management (creation, cancellation)
- Approval queue operations
- Statistics endpoints
- System management endpoints
- Error handling
- Concurrency handling

**Requirements Covered**: 9.1

### 3. WebSocket Integration Tests
**File**: `test_integration_websocket.py`

Tests WebSocket communication and real-time updates:
- Event broadcasting (photos, sessions, jobs, system)
- Channel routing
- API-WebSocket integration
- Message format consistency
- Client management
- Error handling
- Performance under load
- Event sequencing
- Reconnection handling

**Requirements Covered**: 4.5, 7.2

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-html pytest-cov

# Ensure database is initialized
python init_database.py
```

### Run All Integration Tests

```bash
# Run all integration tests
python run_integration_tests.py

# Or using pytest directly
py -m pytest test_integration_*.py -v
```

### Run Specific Test Categories

```bash
# Run only E2E tests
python run_integration_tests.py e2e

# Run only API tests
python run_integration_tests.py api

# Run only WebSocket tests
python run_integration_tests.py websocket
```

### Run Individual Test Files

```bash
# E2E tests
py -m pytest test_integration_e2e.py -v

# API tests
py -m pytest test_integration_api.py -v

# WebSocket tests
py -m pytest test_integration_websocket.py -v
```

### Run Specific Test Classes or Methods

```bash
# Run specific test class
py -m pytest test_integration_e2e.py::TestCompleteWorkflow -v

# Run specific test method
py -m pytest test_integration_e2e.py::TestCompleteWorkflow::test_full_workflow_import_to_export -v
```

## Test Structure

### E2E Test Structure

```python
class TestCompleteWorkflow:
    """Test complete workflow from import to export"""
    
    def test_full_workflow_import_to_export(self, client, temp_dirs, sample_image_file):
        # 1. Create session
        # 2. Import photo
        # 3. Analyze photo (EXIF + AI)
        # 4. Create development job
        # 5. Simulate job completion
        # 6. Approve photo
        # 7. Verify photo is approved
        # 8. Verify session statistics
```

### API Test Structure

```python
class TestSessionAPI:
    """Test session management API endpoints"""
    
    def test_list_sessions(self, client, test_db):
        # Test GET /api/sessions
        
    def test_create_session(self, client, test_db):
        # Test POST /api/sessions
        
    def test_update_session(self, client, test_db):
        # Test PATCH /api/sessions/<id>
```

### WebSocket Test Structure

```python
class TestWebSocketEventBroadcasting:
    """Test WebSocket event broadcasting"""
    
    def test_photo_imported_broadcast(self, mock_websocket_server):
        # Test photo imported event broadcast
        
    def test_session_created_broadcast(self, mock_websocket_server):
        # Test session created event broadcast
```

## Fixtures

### Common Fixtures

- `app`: Flask application instance
- `client`: Flask test client
- `test_db`: Temporary test database
- `temp_dirs`: Temporary directories for file operations
- `sample_image_file`: Sample image file for testing
- `mock_websocket_server`: Mocked WebSocket server

### Database Fixtures

The `test_db` fixture creates a temporary SQLite database with sample data:
- 3 sessions (2 processing, 1 completed)
- Multiple photos per session
- 5 jobs with different statuses
- 3 presets
- 7 days of statistics

## Test Data

### Sample Session
```python
{
    'name': 'Test_Session_0',
    'import_folder': '/test/folder_0',
    'total_photos': 10,
    'processed_photos': 5,
    'status': 'processing'
}
```

### Sample Photo
```python
{
    'session_id': 1,
    'file_path': '/test/photo_1_0.jpg',
    'file_name': 'photo_1_0.jpg',
    'file_size': 1024000,
    'ai_score': 3.0,
    'focus_score': 3.5,
    'exposure_score': 4.0,
    'composition_score': 3.8,
    'status': 'completed',
    'approved': False
}
```

### Sample Job
```python
{
    'id': 'job_0',
    'photo_id': 1,
    'priority': 1,
    'config_json': '{"version": "1.0", "pipeline": []}',
    'status': 'completed'
}
```

## Assertions

### Common Assertions

```python
# HTTP status codes
assert response.status_code == 200
assert response.status_code == 201  # Created
assert response.status_code == 404  # Not found

# Response data
data = json.loads(response.data)
assert 'sessions' in data
assert data['count'] > 0

# Database state
photo = db_session.query(Photo).filter_by(id=photo_id).first()
assert photo.approved == True
assert photo.status == 'completed'

# WebSocket events
assert mock_websocket_server.broadcast.called
message = mock_websocket_server.broadcast.call_args[0][0]
assert message['type'] == 'photo_imported'
```

## Mocking

### WebSocket Server Mock

```python
@pytest.fixture
def mock_websocket_server():
    with patch('websocket_events.get_websocket_server') as mock_get_ws:
        mock_ws = Mock()
        mock_ws.broadcast = Mock()
        mock_ws.get_connected_clients = Mock(return_value=[])
        mock_get_ws.return_value = mock_ws
        yield mock_ws
```

### AI Evaluation Mock

```python
@patch('ai_selector.AISelector.evaluate')
def test_with_mocked_ai(mock_ai_eval, client):
    mock_ai_eval.return_value = {
        'overall_score': 4.5,
        'focus_score': 4.2,
        'exposure_score': 4.8,
        'composition_score': 4.3,
        'faces_detected': 1
    }
    # Test code here
```

## Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
py -m pytest test_integration_*.py --cov=. --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

### Expected Coverage

- E2E Tests: Cover complete workflows
- API Tests: Cover all API endpoints
- WebSocket Tests: Cover all event types

## Troubleshooting

### Common Issues

#### 1. Database Lock Errors

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**:
```python
# Ensure database sessions are properly closed
db_session = get_session()
try:
    # Database operations
    db_session.commit()
finally:
    db_session.close()
```

#### 2. WebSocket Mock Not Called

**Problem**: `assert mock_websocket_server.broadcast.called` fails

**Solution**:
- Verify the API endpoint actually triggers WebSocket events
- Check that `websocket_events` module is imported correctly
- Ensure mock is patched at the correct location

#### 3. Temporary Files Not Cleaned Up

**Problem**: Temporary test files remain after tests

**Solution**:
```python
@pytest.fixture
def temp_dirs():
    base_dir = Path(tempfile.mkdtemp())
    # ... create directories
    yield dirs
    # Cleanup
    shutil.rmtree(base_dir, ignore_errors=True)
```

#### 4. Test Database Conflicts

**Problem**: Tests interfere with each other

**Solution**:
- Use unique temporary database for each test
- Ensure proper cleanup in fixtures
- Use `test_db` fixture consistently

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on other tests:

```python
def test_independent(self, client, test_db):
    # Create own test data
    # Run test
    # Verify results
    # Cleanup is automatic via fixtures
```

### 2. Descriptive Test Names

```python
def test_full_workflow_import_to_export(self):
    """Test complete workflow: Import → Analyze → Select → Develop → Export"""
    pass

def test_workflow_with_rejection(self):
    """Test workflow with photo rejection"""
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_create_session(self, client):
    # Arrange
    session_data = {'name': 'Test', 'import_folder': '/test'}
    
    # Act
    response = client.post('/api/sessions', data=json.dumps(session_data))
    
    # Assert
    assert response.status_code == 201
    assert 'id' in json.loads(response.data)
```

### 4. Use Fixtures for Common Setup

```python
@pytest.fixture
def sample_session(test_db):
    db_session = get_session()
    try:
        session = Session(name='Test', import_folder='/test')
        db_session.add(session)
        db_session.commit()
        return session.id
    finally:
        db_session.close()
```

### 5. Test Error Cases

```python
def test_invalid_session_id(self, client):
    """Test handling of invalid session ID"""
    response = client.get('/api/sessions/99999')
    assert response.status_code == 404

def test_missing_required_fields(self, client):
    """Test handling of missing required fields"""
    response = client.post('/api/sessions', data=json.dumps({}))
    assert response.status_code in [400, 422]
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-html pytest-cov
    
    - name: Run integration tests
      run: |
        cd local_bridge
        python run_integration_tests.py all
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: test-results
        path: local_bridge/test_results_*.xml
```

## Performance Benchmarks

### Expected Test Execution Times

- E2E Tests: ~30-60 seconds
- API Tests: ~20-40 seconds
- WebSocket Tests: ~10-20 seconds
- Total: ~60-120 seconds

### Performance Optimization

1. Use in-memory SQLite database for tests
2. Mock external dependencies (AI, LLM)
3. Parallelize independent tests
4. Use fixtures for expensive setup

## Maintenance

### Adding New Tests

1. Identify the component or workflow to test
2. Choose appropriate test file (E2E, API, or WebSocket)
3. Create test class if needed
4. Write test method with descriptive name
5. Use existing fixtures or create new ones
6. Follow Arrange-Act-Assert pattern
7. Add assertions to verify behavior
8. Run tests to verify they pass
9. Update this documentation

### Updating Existing Tests

1. Identify failing or outdated test
2. Update test logic to match current implementation
3. Update assertions if API contracts changed
4. Verify test passes
5. Update documentation if needed

## References

- [pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [WebSocket Testing](https://websockets.readthedocs.io/en/stable/topics/testing.html)

## Support

For issues or questions about integration tests:
1. Check this documentation
2. Review test code and comments
3. Check pytest output for detailed error messages
4. Review logs in `logs/integration_tests_*.log`

---

**Last Updated**: 2025-11-09
**Version**: 1.0
**Requirements**: 全要件
