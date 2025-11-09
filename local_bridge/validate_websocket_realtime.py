"""
Validation Script for WebSocket Real-time Updates
WebSocketリアルタイム更新の検証スクリプト

Simple validation script to verify WebSocket functionality without pytest.
"""

import sys
import traceback
from flask import Flask

# Test imports
print("Testing imports...")
try:
    from websocket_server import init_websocket_server, get_websocket_server, EventType
    print("✓ websocket_server imported successfully")
except Exception as e:
    print(f"✗ Failed to import websocket_server: {e}")
    sys.exit(1)

try:
    import websocket_events
    print("✓ websocket_events imported successfully")
except Exception as e:
    print(f"✗ Failed to import websocket_events: {e}")
    sys.exit(1)

# Test WebSocket server initialization
print("\nTesting WebSocket server initialization...")
try:
    app = Flask(__name__)
    app.config['TESTING'] = True
    ws_server = init_websocket_server(app)
    print(f"✓ WebSocket server initialized")
    print(f"  - Client count: {ws_server.get_client_count()}")
except Exception as e:
    print(f"✗ Failed to initialize WebSocket server: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test EventType constants
print("\nTesting EventType constants...")
event_types = [
    'JOB_CREATED', 'JOB_STARTED', 'JOB_PROGRESS', 'JOB_COMPLETED', 'JOB_FAILED',
    'PHOTO_IMPORTED', 'PHOTO_ANALYZED', 'PHOTO_SELECTED', 'PHOTO_APPROVED', 'PHOTO_REJECTED',
    'SESSION_CREATED', 'SESSION_UPDATED', 'SESSION_COMPLETED',
    'SYSTEM_STATUS', 'RESOURCE_WARNING', 'ERROR_OCCURRED',
    'QUEUE_STATUS', 'PRIORITY_CHANGED'
]

for event_type in event_types:
    if hasattr(EventType, event_type):
        print(f"✓ EventType.{event_type} = {getattr(EventType, event_type)}")
    else:
        print(f"✗ EventType.{event_type} not found")

# Test event broadcasting functions
print("\nTesting event broadcasting functions...")

test_cases = [
    ("broadcast_job_created", lambda: websocket_events.broadcast_job_created("test_123", 456, 2)),
    ("broadcast_job_started", lambda: websocket_events.broadcast_job_started("test_123", 456)),
    ("broadcast_job_progress", lambda: websocket_events.broadcast_job_progress("test_123", "analyzing", 45.5, "Test")),
    ("broadcast_job_completed", lambda: websocket_events.broadcast_job_completed("test_123", 456, {'status': 'success'})),
    ("broadcast_job_failed", lambda: websocket_events.broadcast_job_failed("test_123", 456, "Test error", {})),
    ("broadcast_photo_imported", lambda: websocket_events.broadcast_photo_imported(789, 12, "test.jpg", "/test/test.jpg")),
    ("broadcast_photo_analyzed", lambda: websocket_events.broadcast_photo_analyzed(789, 4.2, {'focus_score': 4.5})),
    ("broadcast_photo_selected", lambda: websocket_events.broadcast_photo_selected(789, "portrait", "WhiteLayer_v4")),
    ("broadcast_photo_approved", lambda: websocket_events.broadcast_photo_approved(789, 12)),
    ("broadcast_photo_rejected", lambda: websocket_events.broadcast_photo_rejected(789, 12, "Test reason")),
    ("broadcast_session_created", lambda: websocket_events.broadcast_session_created(12, "Test_Session", "/test/path")),
    ("broadcast_session_updated", lambda: websocket_events.broadcast_session_updated(12, 100, 45, "processing")),
    ("broadcast_session_completed", lambda: websocket_events.broadcast_session_completed(12, "Test_Session", 100, 85)),
    ("broadcast_system_status", lambda: websocket_events.broadcast_system_status("running", {'cpu': 45.2})),
    ("broadcast_resource_warning", lambda: websocket_events.broadcast_resource_warning("gpu", 78.5, 75.0, "Test warning")),
    ("broadcast_error_occurred", lambda: websocket_events.broadcast_error_occurred("TEST_ERROR", "Test error", {}, "job_123", 456)),
    ("broadcast_queue_status", lambda: websocket_events.broadcast_queue_status(15, 3, 82, 2)),
    ("broadcast_priority_changed", lambda: websocket_events.broadcast_priority_changed("job_123", 2, 1, "Test reason")),
    ("broadcast_approval_queue_updated", lambda: websocket_events.broadcast_approval_queue_updated(12, 5)),
    ("broadcast_export_started", lambda: websocket_events.broadcast_export_started(789, "SNS_2048", "/test/export")),
    ("broadcast_export_completed", lambda: websocket_events.broadcast_export_completed(789, "SNS_2048", "/test/out.jpg", 2048576)),
    ("broadcast_export_failed", lambda: websocket_events.broadcast_export_failed(789, "SNS_2048", "Test error")),
]

passed = 0
failed = 0

for test_name, test_func in test_cases:
    try:
        test_func()
        print(f"✓ {test_name}")
        passed += 1
    except Exception as e:
        print(f"✗ {test_name}: {e}")
        traceback.print_exc()
        failed += 1

# Test WebSocket server methods
print("\nTesting WebSocket server methods...")

try:
    clients = ws_server.get_connected_clients()
    print(f"✓ get_connected_clients() returned {len(clients)} clients")
    passed += 1
except Exception as e:
    print(f"✗ get_connected_clients() failed: {e}")
    failed += 1

try:
    count = ws_server.get_client_count()
    print(f"✓ get_client_count() returned {count}")
    passed += 1
except Exception as e:
    print(f"✗ get_client_count() failed: {e}")
    failed += 1

try:
    ws_server.broadcast({'type': 'test', 'data': 'test'}, channel='test')
    print(f"✓ broadcast() with channel")
    passed += 1
except Exception as e:
    print(f"✗ broadcast() failed: {e}")
    failed += 1

try:
    ws_server.send_to_client_type('gui', {'type': 'test', 'data': 'test'})
    print(f"✓ send_to_client_type()")
    passed += 1
except Exception as e:
    print(f"✗ send_to_client_type() failed: {e}")
    failed += 1

try:
    def test_handler(ws, message):
        return {'type': 'response', 'status': 'ok'}
    
    ws_server.register_handler('test_message', test_handler)
    print(f"✓ register_handler()")
    passed += 1
except Exception as e:
    print(f"✗ register_handler() failed: {e}")
    failed += 1

# Summary
print("\n" + "="*60)
print(f"VALIDATION SUMMARY")
print("="*60)
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total:  {passed + failed}")

if failed == 0:
    print("\n✓ All validations passed!")
    sys.exit(0)
else:
    print(f"\n✗ {failed} validation(s) failed")
    sys.exit(1)
