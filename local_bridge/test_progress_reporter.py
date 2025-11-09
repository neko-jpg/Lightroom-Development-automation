# test_progress_reporter.py
#
# Tests for the progress reporter module
#
# Requirements: 4.5

import pytest
import time
from progress_reporter import ProgressReporter, ProcessingStage, init_progress_reporter, get_progress_reporter


class MockWebSocketServer:
    """Mock WebSocket server for testing"""
    
    def __init__(self):
        self.messages = []
        self.broadcasts = []
    
    def broadcast(self, message, channel=None):
        """Record broadcast messages"""
        self.broadcasts.append({
            'message': message,
            'channel': channel
        })


def test_progress_reporter_initialization():
    """Test progress reporter initialization"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    assert reporter is not None
    assert reporter.websocket_server == mock_ws
    assert len(reporter.active_jobs) == 0


def test_start_job():
    """Test starting a job"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_001"
    photo_id = 123
    photo_info = {
        'file_name': 'IMG_001.CR3',
        'file_path': '/path/to/IMG_001.CR3'
    }
    
    reporter.start_job(job_id, photo_id, photo_info)
    
    # Check job is tracked
    assert job_id in reporter.active_jobs
    assert reporter.active_jobs[job_id]['photo_id'] == photo_id
    assert reporter.active_jobs[job_id]['photo_info'] == photo_info
    
    # Check broadcast was sent
    assert len(mock_ws.broadcasts) == 1
    assert mock_ws.broadcasts[0]['message']['type'] == 'job_started'
    assert mock_ws.broadcasts[0]['message']['job_id'] == job_id


def test_update_progress():
    """Test updating job progress"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_002"
    reporter.start_job(job_id, 456, {'file_name': 'test.jpg'})
    
    # Clear initial broadcast
    mock_ws.broadcasts.clear()
    
    # Update progress
    reporter.update_progress(
        job_id,
        ProcessingStage.EXIF_ANALYSIS,
        25.0,
        "Analyzing EXIF data",
        {'camera': 'Canon EOS R5'}
    )
    
    # Check job info updated
    job_info = reporter.active_jobs[job_id]
    assert job_info['current_stage'] == ProcessingStage.EXIF_ANALYSIS.value
    assert job_info['progress'] == 25.0
    
    # Check broadcast
    assert len(mock_ws.broadcasts) == 1
    broadcast = mock_ws.broadcasts[0]
    assert broadcast['message']['type'] == 'job_progress'
    assert broadcast['message']['stage'] == ProcessingStage.EXIF_ANALYSIS.value
    assert broadcast['message']['progress'] == 25.0
    assert broadcast['channel'] == 'jobs'


def test_complete_stage():
    """Test completing a processing stage"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_003"
    reporter.start_job(job_id, 789, {'file_name': 'test.jpg'})
    mock_ws.broadcasts.clear()
    
    # Complete a stage
    stage_result = {'iso': 400, 'aperture': 2.8}
    reporter.complete_stage(job_id, ProcessingStage.EXIF_ANALYSIS, stage_result)
    
    # Check stage recorded
    job_info = reporter.active_jobs[job_id]
    assert len(job_info['stages_completed']) == 1
    assert job_info['stages_completed'][0]['stage'] == ProcessingStage.EXIF_ANALYSIS.value
    assert job_info['stages_completed'][0]['result'] == stage_result
    
    # Check broadcast
    assert len(mock_ws.broadcasts) == 1
    assert mock_ws.broadcasts[0]['message']['type'] == 'stage_completed'


def test_complete_job_success():
    """Test completing a job successfully"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_004"
    reporter.start_job(job_id, 101, {'file_name': 'test.jpg'})
    mock_ws.broadcasts.clear()
    
    # Complete job
    result = {'preset_applied': 'WhiteLayer_v4', 'success': True}
    reporter.complete_job(job_id, True, result)
    
    # Check job info
    job_info = reporter.active_jobs[job_id]
    assert job_info['success'] is True
    assert job_info['result'] == result
    assert 'completed_at' in job_info
    
    # Check broadcast
    assert len(mock_ws.broadcasts) == 1
    broadcast = mock_ws.broadcasts[0]
    assert broadcast['message']['type'] == 'job_completed'
    assert broadcast['message']['success'] is True
    assert 'duration' in broadcast['message']


def test_complete_job_failure():
    """Test completing a job with failure"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_005"
    reporter.start_job(job_id, 102, {'file_name': 'test.jpg'})
    mock_ws.broadcasts.clear()
    
    # Complete job with failure
    result = {'error': 'File not found'}
    reporter.complete_job(job_id, False, result)
    
    # Check broadcast
    assert len(mock_ws.broadcasts) == 1
    broadcast = mock_ws.broadcasts[0]
    assert broadcast['message']['type'] == 'job_failed'
    assert broadcast['message']['success'] is False


def test_report_error():
    """Test reporting an error"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_006"
    reporter.start_job(job_id, 103, {'file_name': 'test.jpg'})
    mock_ws.broadcasts.clear()
    
    # Report error
    reporter.report_error(
        job_id,
        'validation_error',
        'Invalid configuration',
        {'field': 'exposure', 'value': 999},
        ProcessingStage.APPLYING_PRESET
    )
    
    # Check error recorded
    job_info = reporter.active_jobs[job_id]
    assert len(job_info['errors']) == 1
    error = job_info['errors'][0]
    assert error['error_type'] == 'validation_error'
    assert error['error_message'] == 'Invalid configuration'
    assert error['stage'] == ProcessingStage.APPLYING_PRESET.value
    
    # Check broadcast
    assert len(mock_ws.broadcasts) == 1
    broadcast = mock_ws.broadcasts[0]
    assert broadcast['message']['type'] == 'error_occurred'
    assert broadcast['message']['error_type'] == 'validation_error'


def test_send_photo_info():
    """Test sending photo information"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_007"
    reporter.start_job(job_id, 104, {'file_name': 'test.jpg'})
    mock_ws.broadcasts.clear()
    
    # Send photo info
    photo_data = {
        'exif': {'iso': 800, 'aperture': 4.0},
        'ai_score': 4.2,
        'context': 'portrait'
    }
    reporter.send_photo_info(job_id, photo_data)
    
    # Check broadcast
    assert len(mock_ws.broadcasts) == 1
    broadcast = mock_ws.broadcasts[0]
    assert broadcast['message']['type'] == 'photo_info'
    assert broadcast['message']['photo_data'] == photo_data
    assert broadcast['channel'] == 'photos'


def test_get_job_status():
    """Test getting job status"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_008"
    reporter.start_job(job_id, 105, {'file_name': 'test.jpg'})
    reporter.update_progress(job_id, ProcessingStage.AI_EVALUATION, 50.0)
    
    # Get status
    status = reporter.get_job_status(job_id)
    
    assert status is not None
    assert status['job_id'] == job_id
    assert status['photo_id'] == 105
    assert status['current_stage'] == ProcessingStage.AI_EVALUATION.value
    assert status['progress'] == 50.0
    assert 'elapsed_seconds' in status


def test_get_job_status_not_found():
    """Test getting status of non-existent job"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    status = reporter.get_job_status("nonexistent_job")
    assert status is None


def test_get_active_jobs():
    """Test getting all active jobs"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    # Start multiple jobs
    reporter.start_job("job_1", 201, {'file_name': 'img1.jpg'})
    reporter.start_job("job_2", 202, {'file_name': 'img2.jpg'})
    reporter.start_job("job_3", 203, {'file_name': 'img3.jpg'})
    
    # Get active jobs
    active_jobs = reporter.get_active_jobs()
    
    assert len(active_jobs) == 3
    assert "job_1" in active_jobs
    assert "job_2" in active_jobs
    assert "job_3" in active_jobs


def test_no_websocket_server():
    """Test reporter works without WebSocket server"""
    reporter = ProgressReporter(None)
    
    # Should not raise errors
    job_id = "test_job_009"
    reporter.start_job(job_id, 106, {'file_name': 'test.jpg'})
    reporter.update_progress(job_id, ProcessingStage.EXIF_ANALYSIS, 25.0)
    reporter.complete_job(job_id, True, {})
    
    # Job should still be tracked
    assert job_id in reporter.active_jobs


def test_global_progress_reporter():
    """Test global progress reporter initialization"""
    mock_ws = MockWebSocketServer()
    
    # Initialize global reporter
    reporter = init_progress_reporter(mock_ws)
    assert reporter is not None
    
    # Get global reporter
    retrieved = get_progress_reporter()
    assert retrieved is reporter


def test_processing_stages_enum():
    """Test ProcessingStage enum values"""
    assert ProcessingStage.IMPORTING.value == "importing"
    assert ProcessingStage.EXIF_ANALYSIS.value == "exif_analysis"
    assert ProcessingStage.AI_EVALUATION.value == "ai_evaluation"
    assert ProcessingStage.CONTEXT_DETECTION.value == "context_detection"
    assert ProcessingStage.PRESET_SELECTION.value == "preset_selection"
    assert ProcessingStage.APPLYING_PRESET.value == "applying_preset"
    assert ProcessingStage.QUALITY_CHECK.value == "quality_check"
    assert ProcessingStage.EXPORTING.value == "exporting"
    assert ProcessingStage.COMPLETED.value == "completed"
    assert ProcessingStage.FAILED.value == "failed"


def test_multiple_errors():
    """Test recording multiple errors for a job"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_010"
    reporter.start_job(job_id, 107, {'file_name': 'test.jpg'})
    
    # Report multiple errors
    reporter.report_error(job_id, 'error1', 'First error')
    reporter.report_error(job_id, 'error2', 'Second error')
    reporter.report_error(job_id, 'error3', 'Third error')
    
    # Check all errors recorded
    job_info = reporter.active_jobs[job_id]
    assert len(job_info['errors']) == 3
    assert job_info['errors'][0]['error_type'] == 'error1'
    assert job_info['errors'][1]['error_type'] == 'error2'
    assert job_info['errors'][2]['error_type'] == 'error3'


def test_progress_sequence():
    """Test a complete progress sequence"""
    mock_ws = MockWebSocketServer()
    reporter = ProgressReporter(mock_ws)
    
    job_id = "test_job_011"
    photo_id = 108
    
    # Start job
    reporter.start_job(job_id, photo_id, {'file_name': 'test.jpg'})
    
    # Progress through stages
    stages = [
        (ProcessingStage.IMPORTING, 10),
        (ProcessingStage.EXIF_ANALYSIS, 20),
        (ProcessingStage.AI_EVALUATION, 40),
        (ProcessingStage.CONTEXT_DETECTION, 50),
        (ProcessingStage.PRESET_SELECTION, 60),
        (ProcessingStage.APPLYING_PRESET, 80),
        (ProcessingStage.QUALITY_CHECK, 90),
        (ProcessingStage.COMPLETED, 100)
    ]
    
    for stage, progress in stages:
        reporter.update_progress(job_id, stage, progress)
        reporter.complete_stage(job_id, stage)
    
    # Complete job
    reporter.complete_job(job_id, True, {'all_stages_completed': True})
    
    # Verify
    job_info = reporter.active_jobs[job_id]
    assert len(job_info['stages_completed']) == len(stages)
    assert job_info['success'] is True
    assert job_info['progress'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
