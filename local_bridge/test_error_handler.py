"""
エラーハンドラーのテスト

Requirements: 14.1, 14.2
"""

import pytest
import os
import json
import tempfile
from datetime import datetime

from error_handler import (
    # エラーカテゴリとタイプ
    ErrorCategory,
    ErrorSeverity,
    ErrorRecoveryStrategy,
    ErrorContext,
    
    # 基底エラークラス
    JunmaiError,
    
    # ファイルシステムエラー
    FileSystemError,
    FileReadError,
    FileWriteError,
    DiskSpaceError,
    
    # AI処理エラー
    AIProcessingError,
    LLMTimeoutError,
    GPUOutOfMemoryError,
    ModelLoadError,
    
    # Lightroomエラー
    LightroomError,
    CatalogLockError,
    PluginCommunicationError,
    DevelopSettingsError,
    
    # エクスポートエラー
    ExportError,
    ExportFailedError,
    CloudSyncError,
    
    # データベースエラー
    DatabaseError,
    DatabaseConnectionError,
    
    # リソースエラー
    ResourceError,
    CPUOverloadError,
    GPUOverheatError,
    
    # エラーハンドラー
    ErrorHandler,
    get_error_handler,
    handle_error
)


class TestErrorCategories:
    """エラーカテゴリのテスト"""
    
    def test_error_category_enum(self):
        """ErrorCategoryの列挙値をテスト"""
        assert ErrorCategory.FILE_SYSTEM.value == "file_system"
        assert ErrorCategory.AI_PROCESSING.value == "ai_processing"
        assert ErrorCategory.LIGHTROOM_INTEGRATION.value == "lightroom_integration"
        assert ErrorCategory.EXPORT.value == "export"
        assert ErrorCategory.DATABASE.value == "database"
    
    def test_error_severity_enum(self):
        """ErrorSeverityの列挙値をテスト"""
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.LOW.value == "low"
    
    def test_error_recovery_strategy_enum(self):
        """ErrorRecoveryStrategyの列挙値をテスト"""
        assert ErrorRecoveryStrategy.RETRY.value == "retry"
        assert ErrorRecoveryStrategy.RETRY_WITH_BACKOFF.value == "retry_backoff"
        assert ErrorRecoveryStrategy.WAIT_FOR_RESOURCE.value == "wait_resource"
        assert ErrorRecoveryStrategy.SKIP.value == "skip"


class TestFileSystemErrors:
    """ファイルシステムエラーのテスト"""
    
    def test_file_read_error(self):
        """FileReadErrorのテスト"""
        error = FileReadError("/path/to/file.jpg", "Permission denied")
        
        assert error.category == ErrorCategory.FILE_SYSTEM
        assert error.error_code == "FS_READ_ERROR"
        assert error.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF
        assert error.details['file_path'] == "/path/to/file.jpg"
        assert error.details['reason'] == "Permission denied"
    
    def test_file_write_error(self):
        """FileWriteErrorのテスト"""
        error = FileWriteError("/path/to/output.jpg", "Disk full")
        
        assert error.category == ErrorCategory.FILE_SYSTEM
        assert error.error_code == "FS_WRITE_ERROR"
        assert error.details['file_path'] == "/path/to/output.jpg"
    
    def test_disk_space_error(self):
        """DiskSpaceErrorのテスト"""
        error = DiskSpaceError(required_mb=1000, available_mb=500)
        
        assert error.category == ErrorCategory.FILE_SYSTEM
        assert error.error_code == "FS_DISK_SPACE"
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.recovery_strategy == ErrorRecoveryStrategy.SYSTEM_HALT
        assert error.details['required_mb'] == 1000
        assert error.details['available_mb'] == 500


class TestAIProcessingErrors:
    """AI処理エラーのテスト"""
    
    def test_llm_timeout_error(self):
        """LLMTimeoutErrorのテスト"""
        error = LLMTimeoutError("llama3.1:8b", 30)
        
        assert error.category == ErrorCategory.AI_PROCESSING
        assert error.error_code == "AI_LLM_TIMEOUT"
        assert error.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF
        assert error.details['model_name'] == "llama3.1:8b"
        assert error.details['timeout_seconds'] == 30
    
    def test_gpu_out_of_memory_error(self):
        """GPUOutOfMemoryErrorのテスト"""
        error = GPUOutOfMemoryError(required_mb=8000, available_mb=6000)
        
        assert error.category == ErrorCategory.AI_PROCESSING
        assert error.error_code == "AI_GPU_OOM"
        assert error.severity == ErrorSeverity.HIGH
        assert error.recovery_strategy == ErrorRecoveryStrategy.WAIT_FOR_RESOURCE
        assert error.details['required_mb'] == 8000
        assert error.details['available_mb'] == 6000
        assert 'quantization' in error.details['suggestion'].lower()
    
    def test_model_load_error(self):
        """ModelLoadErrorのテスト"""
        error = ModelLoadError("llama3.1:8b", "Model file not found")
        
        assert error.category == ErrorCategory.AI_PROCESSING
        assert error.error_code == "AI_MODEL_LOAD"
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.details['model_name'] == "llama3.1:8b"


class TestLightroomErrors:
    """Lightroomエラーのテスト"""
    
    def test_catalog_lock_error(self):
        """CatalogLockErrorのテスト"""
        error = CatalogLockError("/path/to/catalog.lrcat", 300)
        
        assert error.category == ErrorCategory.LIGHTROOM_INTEGRATION
        assert error.error_code == "LR_CATALOG_LOCK"
        assert error.recovery_strategy == ErrorRecoveryStrategy.WAIT_FOR_RESOURCE
        assert error.details['catalog_path'] == "/path/to/catalog.lrcat"
        assert error.details['wait_time_seconds'] == 300
    
    def test_plugin_communication_error(self):
        """PluginCommunicationErrorのテスト"""
        error = PluginCommunicationError("Connection refused")
        
        assert error.category == ErrorCategory.LIGHTROOM_INTEGRATION
        assert error.error_code == "LR_PLUGIN_COMM"
        assert error.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF
    
    def test_develop_settings_error(self):
        """DevelopSettingsErrorのテスト"""
        error = DevelopSettingsError("photo_123", "WhiteLayer_v4", "Invalid parameter")
        
        assert error.category == ErrorCategory.LIGHTROOM_INTEGRATION
        assert error.error_code == "LR_DEVELOP_SETTINGS"
        assert error.recovery_strategy == ErrorRecoveryStrategy.SKIP
        assert error.details['photo_id'] == "photo_123"
        assert error.details['setting_name'] == "WhiteLayer_v4"


class TestExportErrors:
    """エクスポートエラーのテスト"""
    
    def test_export_failed_error(self):
        """ExportFailedErrorのテスト"""
        error = ExportFailedError("photo_456", "JPEG", "Codec error")
        
        assert error.category == ErrorCategory.EXPORT
        assert error.error_code == "EXPORT_FAILED"
        assert error.recovery_strategy == ErrorRecoveryStrategy.RETRY
        assert error.details['photo_id'] == "photo_456"
        assert error.details['format'] == "JPEG"
    
    def test_cloud_sync_error(self):
        """CloudSyncErrorのテスト"""
        error = CloudSyncError("Dropbox", "/photos/image.jpg", "Network timeout")
        
        assert error.category == ErrorCategory.EXPORT
        assert error.error_code == "EXPORT_CLOUD_SYNC"
        assert error.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF
        assert error.details['provider'] == "Dropbox"


class TestDatabaseErrors:
    """データベースエラーのテスト"""
    
    def test_database_connection_error(self):
        """DatabaseConnectionErrorのテスト"""
        error = DatabaseConnectionError("/path/to/db.sqlite", "File locked")
        
        assert error.category == ErrorCategory.DATABASE
        assert error.error_code == "DB_CONNECTION"
        assert error.severity == ErrorSeverity.CRITICAL
        assert error.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF


class TestResourceErrors:
    """リソースエラーのテスト"""
    
    def test_cpu_overload_error(self):
        """CPUOverloadErrorのテスト"""
        error = CPUOverloadError(current_usage=95.5, threshold=80.0)
        
        assert error.category == ErrorCategory.RESOURCE
        assert error.error_code == "RESOURCE_CPU_OVERLOAD"
        assert error.details['current_usage'] == 95.5
        assert error.details['threshold'] == 80.0
    
    def test_gpu_overheat_error(self):
        """GPUOverheatErrorのテスト"""
        error = GPUOverheatError(current_temp=82.0, threshold=75.0)
        
        assert error.category == ErrorCategory.RESOURCE
        assert error.error_code == "RESOURCE_GPU_OVERHEAT"
        assert error.severity == ErrorSeverity.HIGH
        assert error.details['current_temp'] == 82.0


class TestErrorContext:
    """ErrorContextのテスト"""
    
    def test_error_context_creation(self):
        """ErrorContextの作成をテスト"""
        context = ErrorContext(
            timestamp="2025-11-08T10:00:00",
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=ErrorRecoveryStrategy.RETRY,
            error_code="TEST_ERROR",
            message="Test error message",
            details={'key': 'value'}
        )
        
        assert context.timestamp == "2025-11-08T10:00:00"
        assert context.category == ErrorCategory.FILE_SYSTEM
        assert context.severity == ErrorSeverity.HIGH
        assert context.error_code == "TEST_ERROR"
    
    def test_error_context_to_dict(self):
        """ErrorContextの辞書変換をテスト"""
        context = ErrorContext(
            timestamp="2025-11-08T10:00:00",
            category=ErrorCategory.AI_PROCESSING,
            severity=ErrorSeverity.MEDIUM,
            recovery_strategy=ErrorRecoveryStrategy.SKIP,
            error_code="TEST_ERROR",
            message="Test message",
            details={'test': 'data'}
        )
        
        result = context.to_dict()
        
        assert result['timestamp'] == "2025-11-08T10:00:00"
        assert result['category'] == "ai_processing"
        assert result['severity'] == "medium"
        assert result['recovery_strategy'] == "skip"
        assert result['error_code'] == "TEST_ERROR"
        assert result['details']['test'] == 'data'


class TestErrorHandler:
    """ErrorHandlerのテスト"""
    
    @pytest.fixture
    def temp_log_file(self):
        """一時ログファイルを作成"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        yield log_file
        # クリーンアップ - Windowsでファイルハンドルを確実に閉じる
        import logging
        # すべてのハンドラーを閉じる
        logger = logging.getLogger('junmai_autodev.errors')
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # ファイルを削除
        try:
            if os.path.exists(log_file):
                os.unlink(log_file)
        except PermissionError:
            # Windowsでファイルが使用中の場合はスキップ
            pass
    
    def test_error_handler_initialization(self, temp_log_file):
        """ErrorHandlerの初期化をテスト"""
        handler = ErrorHandler(log_file=temp_log_file)
        
        assert handler.log_file == temp_log_file
        assert len(handler.error_history) == 0
        assert len(handler.error_counts) == 0
    
    def test_handle_junmai_error(self, temp_log_file):
        """JunmaiErrorの処理をテスト"""
        handler = ErrorHandler(log_file=temp_log_file)
        error = FileReadError("/test/file.jpg", "Not found")
        
        context = handler.handle_error(error)
        
        assert context.category == ErrorCategory.FILE_SYSTEM
        assert context.error_code == "FS_READ_ERROR"
        assert len(handler.error_history) == 1
        assert handler.error_counts["FS_READ_ERROR"] == 1
    
    def test_handle_generic_exception(self, temp_log_file):
        """一般的な例外の処理をテスト"""
        handler = ErrorHandler(log_file=temp_log_file)
        error = ValueError("Invalid value")
        
        context = handler.handle_error(error, {'extra': 'info'})
        
        assert context.category == ErrorCategory.UNKNOWN
        assert context.error_code == "UNKNOWN_ERROR"
        assert context.details['extra'] == 'info'
        assert len(handler.error_history) == 1
    
    def test_error_statistics(self, temp_log_file):
        """エラー統計の取得をテスト"""
        handler = ErrorHandler(log_file=temp_log_file)
        
        # 複数のエラーを処理
        handler.handle_error(FileReadError("/file1.jpg"))
        handler.handle_error(FileReadError("/file2.jpg"))
        handler.handle_error(LLMTimeoutError("llama3.1", 30))
        handler.handle_error(GPUOverheatError(80.0, 75.0))
        
        stats = handler.get_error_statistics()
        
        assert stats['total_errors'] == 4
        assert stats['by_category']['file_system'] == 2
        assert stats['by_category']['ai_processing'] == 1
        assert stats['by_category']['resource'] == 1
        assert stats['by_code']['FS_READ_ERROR'] == 2
        assert stats['by_code']['AI_LLM_TIMEOUT'] == 1
        assert len(stats['recent_errors']) == 4
    
    def test_clear_history(self, temp_log_file):
        """エラー履歴のクリアをテスト"""
        handler = ErrorHandler(log_file=temp_log_file)
        
        handler.handle_error(FileReadError("/file.jpg"))
        assert len(handler.error_history) == 1
        
        handler.clear_history()
        assert len(handler.error_history) == 0
        assert len(handler.error_counts) == 0
    
    def test_export_error_log(self, temp_log_file):
        """エラーログのエクスポートをテスト"""
        handler = ErrorHandler(log_file=temp_log_file)
        
        # エラーを処理
        handler.handle_error(FileReadError("/file.jpg"))
        handler.handle_error(LLMTimeoutError("llama3.1", 30))
        
        # エクスポート
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            export_file = f.name
        
        try:
            handler.export_error_log(export_file)
            
            # エクスポートされたファイルを確認
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert len(exported_data) == 2
            assert exported_data[0]['error_code'] == "FS_READ_ERROR"
            assert exported_data[1]['error_code'] == "AI_LLM_TIMEOUT"
        finally:
            if os.path.exists(export_file):
                os.unlink(export_file)


class TestGlobalErrorHandler:
    """グローバルエラーハンドラーのテスト"""
    
    def test_get_error_handler_singleton(self):
        """グローバルエラーハンドラーのシングルトンをテスト"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2
    
    def test_handle_error_convenience_function(self):
        """handle_error便利関数をテスト"""
        error = FileReadError("/test.jpg")
        context = handle_error(error)
        
        assert context.error_code == "FS_READ_ERROR"
        assert context.category == ErrorCategory.FILE_SYSTEM


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
