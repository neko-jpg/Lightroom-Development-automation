# Integration Tests Quick Reference
統合テストクイックリファレンス

## Quick Start

```bash
# Run all integration tests
python run_integration_tests.py

# Run specific test category
python run_integration_tests.py e2e
python run_integration_tests.py api
python run_integration_tests.py websocket
```

## Test Files

| File | Purpose | Requirements |
|------|---------|--------------|
| `test_integration_e2e.py` | End-to-End workflows | 全要件 |
| `test_integration_api.py` | API endpoint integration | 9.1 |
| `test_integration_websocket.py` | WebSocket communication | 4.5, 7.2 |

## Common Commands

### Run Tests

```bash
# All tests
py -m pytest test_integration_*.py -v

# Specific file
py -m pytest test_integration_e2e.py -v

# Specific class
py -m pytest test_integration_e2e.py::TestCompleteWorkflow -v

# Specific test
py -m pytest test_integration_e2e.py::TestCompleteWorkflow::test_full_workflow_import_to_export -v

# With coverage
py -m pytest test_integration_*.py --cov=. --cov-report=html
```

### Test Output

```bash
# Verbose output
py -m pytest test_integration_*.py -v

# Show print statements
py -m pytest test_integration_*.py -v -s

# Stop on first failure
py -m pytest test_integration_*.py -x

# Run last failed tests
py -m pytest test_integration_*.py --lf
```

## Test Classes

### E2E Tests

- `TestCompleteWorkflow` - Complete workflows
- `TestBatchProcessing` - Batch operations
- `TestErrorRecovery` - Error handling
- `TestPerformanceMetrics` - Performance tracking

### API Tests

- `TestSessionAPI` - Session management
- `TestPhotoAPI` - Photo management
- `TestJobAPI` - Job management
- `TestApprovalAPI` - Approval queue
- `TestStatisticsAPI` - Statistics
- `TestSystemAPI` - System management
- `TestAPIErrorHandling` - Error handling
- `TestAPIConcurrency` - Concurrency

### WebSocket Tests

- `TestWebSocketEventBroadcasting` - Event broadcasting
- `TestWebSocketChannelRouting` - Channel routing
- `TestWebSocketAPIIntegration` - API integration
- `TestWebSocketMessageFormat` - Message format
- `TestWebSocketClientManagement` - Client management
- `TestWebSocketErrorHandling` - Error handling
- `TestWebSocketPerformance` - Performance
- `TestWebSocketEventSequencing` - Event sequencing
- `TestWebSocketReconnection` - Reconnection

## Fixtures

### Common Fixtures

```python
@pytest.fixture
def app():
    """Flask application instance"""

@pytest.fixture
def client(app):
    """Flask test client"""

@pytest.fixture
def test_db():
    """Temporary test database with sample data"""

@pytest.fixture
def temp_dirs():
    """Temporary directories for file operations"""

@pytest.fixture
def sample_image_file(temp_dirs):
    """Sample image file for testing"""

@pytest.fixture
def mock_websocket_server():
    """Mocked WebSocket server"""
```

## Common Patterns

### Create Session

```python
session_data = {
    'name': 'Test_Session',
    'import_folder': '/test/folder'
}
response = client.post('/api/sessions', 
                      data=json.dumps(session_data),
                      content_type='application/json')
session_id = json.loads(response.data)['id']
```

### Create Photo

```python
db_session = get_session()
try:
    photo = Photo(
        session_id=session_id,
        file_path='/test/photo.jpg',
        file_name='photo.jpg',
        file_size=1024000,
        status='completed'
    )
    db_session.add(photo)
    db_session.commit()
    photo_id = photo.id
finally:
    db_session.close()
```

### Create Job

```python
job_data = {
    'photo_id': photo_id,
    'config': {
        'version': '1.0',
        'pipeline': [],
        'safety': {'snapshot': True, 'dryRun': False}
    },
    'priority': 2
}
response = client.post('/api/jobs',
                      data=json.dumps(job_data),
                      content_type='application/json')
job_id = json.loads(response.data)['id']
```

### Approve Photo

```python
response = client.post(f'/api/approval/{photo_id}/approve',
                      data=json.dumps({}),
                      content_type='application/json')
assert response.status_code == 200
```

### Verify WebSocket Broadcast

```python
assert mock_websocket_server.broadcast.called
message = mock_websocket_server.broadcast.call_args[0][0]
assert message['type'] == 'photo_imported'
assert message['photo_id'] == 123
```

## Assertions

### HTTP Status Codes

```python
assert response.status_code == 200  # OK
assert response.status_code == 201  # Created
assert response.status_code == 400  # Bad Request
assert response.status_code == 404  # Not Found
assert response.status_code == 500  # Internal Server Error
```

### Response Data

```python
data = json.loads(response.data)
assert 'sessions' in data
assert data['count'] > 0
assert data['sessions'][0]['name'] == 'Test_Session'
```

### Database State

```python
db_session = get_session()
try:
    photo = db_session.query(Photo).filter_by(id=photo_id).first()
    assert photo is not None
    assert photo.approved == True
    assert photo.status == 'completed'
finally:
    db_session.close()
```

### WebSocket Events

```python
# Verify broadcast was called
assert mock_websocket_server.broadcast.called

# Get message
call_args = mock_websocket_server.broadcast.call_args
message = call_args[0][0]
channel = call_args[1].get('channel')

# Verify message content
assert message['type'] == 'photo_imported'
assert message['photo_id'] == 123
assert 'timestamp' in message

# Verify channel
assert channel == 'photos'
```

## Mocking

### Mock AI Evaluation

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
    # Test code
```

### Mock LLM

```python
@patch('ollama_client.OllamaClient.generate')
def test_with_mocked_llm(mock_ollama, client):
    mock_ollama.return_value = {
        'score': 4.5,
        'recommendation': 'Great photo'
    }
    # Test code
```

### Mock WebSocket Server

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

## Troubleshooting

### Database Lock

```python
# Always close database sessions
db_session = get_session()
try:
    # Operations
    db_session.commit()
finally:
    db_session.close()
```

### WebSocket Mock Not Called

```python
# Ensure correct patch location
with patch('websocket_events.get_websocket_server') as mock:
    # Not 'websocket_server.get_websocket_server'
```

### Temporary Files

```python
# Use fixtures for cleanup
@pytest.fixture
def temp_dirs():
    base_dir = Path(tempfile.mkdtemp())
    yield base_dir
    shutil.rmtree(base_dir, ignore_errors=True)
```

## Performance

### Expected Times

- E2E Tests: ~30-60 seconds
- API Tests: ~20-40 seconds
- WebSocket Tests: ~10-20 seconds

### Optimization

```bash
# Run tests in parallel (requires pytest-xdist)
py -m pytest test_integration_*.py -n auto

# Run only fast tests
py -m pytest test_integration_*.py -m "not slow"
```

## Coverage

```bash
# Generate coverage report
py -m pytest test_integration_*.py --cov=. --cov-report=html

# View report
# Open htmlcov/index.html
```

## CI/CD

```yaml
# GitHub Actions
- name: Run integration tests
  run: |
    cd local_bridge
    python run_integration_tests.py all
```

## Quick Tips

1. **Use fixtures** for common setup
2. **Mock external dependencies** (AI, LLM, WebSocket)
3. **Close database sessions** to avoid locks
4. **Use descriptive test names**
5. **Follow Arrange-Act-Assert** pattern
6. **Test error cases** not just happy paths
7. **Keep tests independent**
8. **Use temporary databases** for isolation

## Resources

- Full Guide: `INTEGRATION_TESTS_GUIDE.md`
- Test Runner: `run_integration_tests.py`
- E2E Tests: `test_integration_e2e.py`
- API Tests: `test_integration_api.py`
- WebSocket Tests: `test_integration_websocket.py`

---

**Version**: 1.0
**Last Updated**: 2025-11-09
