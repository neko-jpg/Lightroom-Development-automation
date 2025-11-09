"""
リトライマネージャーのテスト

Requirements: 14.1
"""

import pytest
import time
import os
import json
import tempfile
from unittest.mock import Mock, patch

from retry_manager import (
    RetryStrategy,
    RetryConfig,
    RetryAttempt,
    RetryHistory,
    RetryManager,
    retry,
    get_retry_manager,
    retry_operation
)


class TestRetryConfig:
    """RetryConfigのテスト"""
    
    def test_default_config(self):
        """デフォルト設定をテスト"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True
    
    def test_custom_config(self):
        """カスタム設定をテスト"""
        config = RetryConfig(
            max_retries=5,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            initial_delay=2.0,
            max_delay=120.0,
            backoff_multiplier=3.0,
            jitter=False
        )
        
        assert config.max_retries == 5
        assert config.strategy == RetryStrategy.LINEAR_BACKOFF
        assert config.initial_delay == 2.0
        assert config.max_delay == 120.0
        assert config.backoff_multiplier == 3.0
        assert config.jitter is False


class TestRetryHistory:
    """RetryHistoryのテスト"""
    
    def test_retry_history_creation(self):
        """RetryHistoryの作成をテスト"""
        history = RetryHistory(
            operation_id="test_op_1",
            operation_name="test_operation",
            started_at="2025-11-08T10:00:00"
        )
        
        assert history.operation_id == "test_op_1"
        assert history.operation_name == "test_operation"
        assert history.total_attempts == 0
        assert history.success is False
    
    def test_add_attempt(self):
        """試行の追加をテスト"""
        history = RetryHistory(
            operation_id="test_op_1",
            operation_name="test_operation",
            started_at="2025-11-08T10:00:00"
        )
        
        attempt = RetryAttempt(
            attempt_number=1,
            timestamp="2025-11-08T10:00:01",
            delay_seconds=1.0,
            exception_type="ValueError",
            exception_message="Test error"
        )
        
        history.add_attempt(attempt)
        
        assert history.total_attempts == 1
        assert len(history.attempts) == 1
        assert history.attempts[0].attempt_number == 1
    
    def test_mark_completed_success(self):
        """成功完了のマークをテスト"""
        history = RetryHistory(
            operation_id="test_op_1",
            operation_name="test_operation",
            started_at="2025-11-08T10:00:00"
        )
        
        history.mark_completed(success=True)
        
        assert history.success is True
        assert history.completed_at is not None
        assert history.final_exception is None
    
    def test_mark_completed_failure(self):
        """失敗完了のマークをテスト"""
        history = RetryHistory(
            operation_id="test_op_1",
            operation_name="test_operation",
            started_at="2025-11-08T10:00:00"
        )
        
        exception = ValueError("Test error")
        history.mark_completed(success=False, exception=exception)
        
        assert history.success is False
        assert history.completed_at is not None
        assert "ValueError" in history.final_exception
    
    def test_to_dict(self):
        """辞書変換をテスト"""
        history = RetryHistory(
            operation_id="test_op_1",
            operation_name="test_operation",
            started_at="2025-11-08T10:00:00"
        )
        
        attempt = RetryAttempt(
            attempt_number=1,
            timestamp="2025-11-08T10:00:01",
            delay_seconds=1.0,
            exception_type="ValueError",
            exception_message="Test error"
        )
        history.add_attempt(attempt)
        
        result = history.to_dict()
        
        assert result['operation_id'] == "test_op_1"
        assert result['operation_name'] == "test_operation"
        assert result['total_attempts'] == 1
        assert len(result['attempts']) == 1


class TestRetryManager:
    """RetryManagerのテスト"""
    
    @pytest.fixture
    def temp_log_file(self):
        """一時ログファイルを作成"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file = f.name
        yield log_file
        
        # クリーンアップ
        import logging
        logger = logging.getLogger('junmai_autodev.retry')
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        try:
            if os.path.exists(log_file):
                os.unlink(log_file)
        except PermissionError:
            pass
    
    def test_retry_manager_initialization(self, temp_log_file):
        """RetryManagerの初期化をテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        assert manager.log_file == temp_log_file
        assert len(manager.retry_histories) == 0
    
    def test_calculate_delay_exponential(self, temp_log_file):
        """指数バックオフの遅延計算をテスト"""
        manager = RetryManager(log_file=temp_log_file)
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            initial_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False
        )
        
        # 1回目: 1.0秒
        delay0 = manager._calculate_delay(0, config)
        assert delay0 == 1.0
        
        # 2回目: 2.0秒
        delay1 = manager._calculate_delay(1, config)
        assert delay1 == 2.0
        
        # 3回目: 4.0秒
        delay2 = manager._calculate_delay(2, config)
        assert delay2 == 4.0
    
    def test_calculate_delay_linear(self, temp_log_file):
        """線形バックオフの遅延計算をテスト"""
        manager = RetryManager(log_file=temp_log_file)
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            initial_delay=1.0,
            jitter=False
        )
        
        # 1回目: 1.0秒
        delay0 = manager._calculate_delay(0, config)
        assert delay0 == 1.0
        
        # 2回目: 2.0秒
        delay1 = manager._calculate_delay(1, config)
        assert delay1 == 2.0
        
        # 3回目: 3.0秒
        delay2 = manager._calculate_delay(2, config)
        assert delay2 == 3.0
    
    def test_calculate_delay_fixed(self, temp_log_file):
        """固定遅延の計算をテスト"""
        manager = RetryManager(log_file=temp_log_file)
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            initial_delay=2.0,
            jitter=False
        )
        
        # すべて2.0秒
        assert manager._calculate_delay(0, config) == 2.0
        assert manager._calculate_delay(1, config) == 2.0
        assert manager._calculate_delay(2, config) == 2.0
    
    def test_calculate_delay_immediate(self, temp_log_file):
        """即座リトライの遅延計算をテスト"""
        manager = RetryManager(log_file=temp_log_file)
        config = RetryConfig(
            strategy=RetryStrategy.IMMEDIATE,
            jitter=False
        )
        
        # すべて0秒
        assert manager._calculate_delay(0, config) == 0.0
        assert manager._calculate_delay(1, config) == 0.0
        assert manager._calculate_delay(2, config) == 0.0
    
    def test_calculate_delay_max_limit(self, temp_log_file):
        """最大遅延の制限をテスト"""
        manager = RetryManager(log_file=temp_log_file)
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            initial_delay=10.0,
            max_delay=20.0,
            backoff_multiplier=2.0,
            jitter=False
        )
        
        # 3回目は40秒になるはずだが、max_delay=20秒で制限される
        delay2 = manager._calculate_delay(2, config)
        assert delay2 == 20.0
    
    def test_retry_success_first_attempt(self, temp_log_file):
        """1回目で成功するケースをテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        mock_operation = Mock(return_value="success")
        
        result = manager.retry_with_backoff(
            operation=mock_operation,
            operation_name="test_operation",
            operation_id="test_op_1"
        )
        
        assert result == "success"
        assert mock_operation.call_count == 1
        
        # 履歴を確認
        history = manager.get_retry_history("test_op_1")
        assert history is not None
        assert history.success is True
        assert history.total_attempts == 1
    
    def test_retry_success_after_failures(self, temp_log_file):
        """失敗後に成功するケースをテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        # 2回失敗して3回目で成功
        mock_operation = Mock(side_effect=[
            ValueError("Error 1"),
            ValueError("Error 2"),
            "success"
        ])
        
        config = RetryConfig(
            max_retries=3,
            initial_delay=0.1,  # テストを高速化
            jitter=False
        )
        
        result = manager.retry_with_backoff(
            operation=mock_operation,
            operation_name="test_operation",
            operation_id="test_op_2",
            config=config
        )
        
        assert result == "success"
        assert mock_operation.call_count == 3
        
        # 履歴を確認
        history = manager.get_retry_history("test_op_2")
        assert history is not None
        assert history.success is True
        assert history.total_attempts == 3
    
    def test_retry_max_retries_exceeded(self, temp_log_file):
        """最大リトライ回数を超えるケースをテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        # すべて失敗
        mock_operation = Mock(side_effect=ValueError("Persistent error"))
        
        config = RetryConfig(
            max_retries=2,
            initial_delay=0.1,
            jitter=False
        )
        
        with pytest.raises(ValueError, match="Persistent error"):
            manager.retry_with_backoff(
                operation=mock_operation,
                operation_name="test_operation",
                operation_id="test_op_3",
                config=config
            )
        
        # 3回試行されたことを確認（初回 + 2回リトライ）
        assert mock_operation.call_count == 3
        
        # 履歴を確認
        history = manager.get_retry_history("test_op_3")
        assert history is not None
        assert history.success is False
        assert history.total_attempts == 3
        assert "ValueError" in history.final_exception
    
    def test_retry_specific_exceptions(self, temp_log_file):
        """特定の例外のみリトライするケースをテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        # ValueError のみリトライ対象
        config = RetryConfig(
            max_retries=2,
            initial_delay=0.1,
            retry_on_exceptions=(ValueError,)
        )
        
        # TypeError は即座に失敗
        mock_operation = Mock(side_effect=TypeError("Type error"))
        
        with pytest.raises(TypeError, match="Type error"):
            manager.retry_with_backoff(
                operation=mock_operation,
                operation_name="test_operation",
                operation_id="test_op_4",
                config=config
            )
        
        # 1回のみ試行（リトライなし）
        assert mock_operation.call_count == 1
    
    def test_get_retry_statistics(self, temp_log_file):
        """リトライ統計の取得をテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        # 成功操作
        mock_success = Mock(return_value="success")
        manager.retry_with_backoff(
            operation=mock_success,
            operation_name="success_op",
            operation_id="op_1"
        )
        
        # 失敗操作
        mock_failure = Mock(side_effect=ValueError("Error"))
        config = RetryConfig(max_retries=1, initial_delay=0.1)
        
        try:
            manager.retry_with_backoff(
                operation=mock_failure,
                operation_name="failure_op",
                operation_id="op_2",
                config=config
            )
        except ValueError:
            pass
        
        # 統計を取得
        stats = manager.get_retry_statistics()
        
        assert stats['total_operations'] == 2
        assert stats['successful_operations'] == 1
        assert stats['failed_operations'] == 1
        assert stats['success_rate'] == 0.5
        assert stats['total_retries'] == 1  # op_2で1回リトライ
    
    def test_clear_history(self, temp_log_file):
        """履歴のクリアをテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        mock_operation = Mock(return_value="success")
        manager.retry_with_backoff(
            operation=mock_operation,
            operation_name="test_operation",
            operation_id="test_op_1"
        )
        
        assert len(manager.retry_histories) == 1
        
        manager.clear_history()
        
        assert len(manager.retry_histories) == 0
    
    def test_export_retry_log(self, temp_log_file):
        """リトライログのエクスポートをテスト"""
        manager = RetryManager(log_file=temp_log_file)
        
        # 操作を実行
        mock_operation = Mock(return_value="success")
        manager.retry_with_backoff(
            operation=mock_operation,
            operation_name="test_operation",
            operation_id="test_op_1"
        )
        
        # エクスポート
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            export_file = f.name
        
        try:
            manager.export_retry_log(export_file)
            
            # エクスポートされたファイルを確認
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert len(exported_data) == 1
            assert exported_data[0]['operation_id'] == "test_op_1"
            assert exported_data[0]['operation_name'] == "test_operation"
            assert exported_data[0]['success'] is True
        finally:
            if os.path.exists(export_file):
                os.unlink(export_file)


class TestRetryDecorator:
    """リトライデコレーターのテスト"""
    
    def test_decorator_success(self):
        """デコレーターで成功するケースをテスト"""
        call_count = 0
        
        @retry(max_retries=3, initial_delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_function()
        
        assert result == "success"
        assert call_count == 1
    
    def test_decorator_retry_and_success(self):
        """デコレーターでリトライ後に成功するケースをテスト"""
        call_count = 0
        
        @retry(max_retries=3, initial_delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = test_function()
        
        assert result == "success"
        assert call_count == 3
    
    def test_decorator_max_retries_exceeded(self):
        """デコレーターで最大リトライ回数を超えるケースをテスト"""
        call_count = 0
        
        @retry(max_retries=2, initial_delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            test_function()
        
        assert call_count == 3  # 初回 + 2回リトライ


class TestRetryOperation:
    """retry_operation便利関数のテスト"""
    
    def test_retry_operation_success(self):
        """retry_operationで成功するケースをテスト"""
        mock_operation = Mock(return_value="success")
        
        result = retry_operation(
            operation=mock_operation,
            operation_name="test_operation",
            max_retries=3,
            initial_delay=0.1
        )
        
        assert result == "success"
        assert mock_operation.call_count == 1
    
    def test_retry_operation_with_retries(self):
        """retry_operationでリトライするケースをテスト"""
        mock_operation = Mock(side_effect=[
            ValueError("Error 1"),
            "success"
        ])
        
        result = retry_operation(
            operation=mock_operation,
            operation_name="test_operation",
            max_retries=3,
            initial_delay=0.1
        )
        
        assert result == "success"
        assert mock_operation.call_count == 2


class TestGlobalRetryManager:
    """グローバルリトライマネージャーのテスト"""
    
    def test_get_retry_manager_singleton(self):
        """グローバルリトライマネージャーのシングルトンをテスト"""
        manager1 = get_retry_manager()
        manager2 = get_retry_manager()
        
        assert manager1 is manager2


class TestRetryIntegration:
    """統合テスト"""
    
    def test_real_world_file_read_retry(self, tmp_path):
        """実際のファイル読み込みリトライをテスト"""
        manager = get_retry_manager()
        
        # 存在しないファイルを読み込もうとする
        file_path = tmp_path / "nonexistent.txt"
        
        attempt_count = 0
        
        def read_file():
            nonlocal attempt_count
            attempt_count += 1
            
            # 3回目で成功するようにファイルを作成
            if attempt_count == 3:
                file_path.write_text("success")
            
            with open(file_path, 'r') as f:
                return f.read()
        
        config = RetryConfig(
            max_retries=3,
            initial_delay=0.1,
            retry_on_exceptions=(FileNotFoundError, IOError)
        )
        
        result = manager.retry_with_backoff(
            operation=read_file,
            operation_name="read_file",
            config=config
        )
        
        assert result == "success"
        assert attempt_count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
