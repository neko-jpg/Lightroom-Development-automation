"""
リトライロジック実装 (Retry Logic Implementation)

このモジュールは、指数バックオフリトライ、リトライ上限管理、
リトライ履歴記録機能を提供します。

Requirements: 14.1
"""

import time
import logging
import json
from datetime import datetime
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, asdict, field
from enum import Enum
import traceback


# ================================================================================
# リトライ設定 (Retry Configuration)
# ================================================================================

class RetryStrategy(Enum):
    """リトライ戦略の列挙型"""
    IMMEDIATE = "immediate"              # 即座にリトライ
    EXPONENTIAL_BACKOFF = "exponential"  # 指数バックオフ
    LINEAR_BACKOFF = "linear"            # 線形バックオフ
    FIXED_DELAY = "fixed"                # 固定遅延


@dataclass
class RetryConfig:
    """リトライ設定"""
    max_retries: int = 3                    # 最大リトライ回数
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_delay: float = 1.0              # 初期遅延（秒）
    max_delay: float = 60.0                 # 最大遅延（秒）
    backoff_multiplier: float = 2.0         # バックオフ乗数
    jitter: bool = True                     # ジッター（ランダム遅延）を追加
    retry_on_exceptions: tuple = (Exception,)  # リトライ対象の例外


# ================================================================================
# リトライ履歴 (Retry History)
# ================================================================================

@dataclass
class RetryAttempt:
    """リトライ試行の記録"""
    attempt_number: int
    timestamp: str
    delay_seconds: float
    exception_type: str
    exception_message: str
    stack_trace: Optional[str] = None
    success: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)


@dataclass
class RetryHistory:
    """リトライ履歴"""
    operation_id: str
    operation_name: str
    started_at: str
    completed_at: Optional[str] = None
    total_attempts: int = 0
    success: bool = False
    final_exception: Optional[str] = None
    attempts: List[RetryAttempt] = field(default_factory=list)
    
    def add_attempt(self, attempt: RetryAttempt):
        """試行を追加"""
        self.attempts.append(attempt)
        self.total_attempts = len(self.attempts)
    
    def mark_completed(self, success: bool, exception: Optional[Exception] = None):
        """完了をマーク"""
        self.completed_at = datetime.now().isoformat()
        self.success = success
        if exception:
            self.final_exception = f"{type(exception).__name__}: {str(exception)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'operation_id': self.operation_id,
            'operation_name': self.operation_name,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'total_attempts': self.total_attempts,
            'success': self.success,
            'final_exception': self.final_exception,
            'attempts': [attempt.to_dict() for attempt in self.attempts]
        }


# ================================================================================
# リトライマネージャー (Retry Manager)
# ================================================================================

class RetryManager:
    """
    リトライマネージャー
    
    指数バックオフリトライ、リトライ上限管理、履歴記録を提供します。
    """
    
    def __init__(self, log_file: str = 'logs/retry.log'):
        """
        Args:
            log_file: リトライログファイルのパス
        """
        self.log_file = log_file
        self.retry_histories: Dict[str, RetryHistory] = {}
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """ロガーのセットアップ"""
        logger = logging.getLogger('junmai_autodev.retry')
        logger.setLevel(logging.DEBUG)
        
        # ログディレクトリを作成
        import os
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # ファイルハンドラー
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        return logger
    
    def _calculate_delay(
        self,
        attempt: int,
        config: RetryConfig
    ) -> float:
        """
        リトライ遅延を計算
        
        Args:
            attempt: 試行回数（0から開始）
            config: リトライ設定
        
        Returns:
            float: 遅延時間（秒）
        """
        if config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0.0
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            # 指数バックオフ: delay = initial_delay * (multiplier ^ attempt)
            delay = config.initial_delay * (config.backoff_multiplier ** attempt)
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            # 線形バックオフ: delay = initial_delay * (attempt + 1)
            delay = config.initial_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            # 固定遅延
            delay = config.initial_delay
        else:
            delay = config.initial_delay
        
        # 最大遅延を超えないようにクリップ
        delay = min(delay, config.max_delay)
        
        # ジッターを追加（ランダム性を加えて同時リトライを分散）
        if config.jitter:
            import random
            jitter_amount = delay * 0.1  # 遅延の10%をジッター範囲とする
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.0, delay)  # 負の値にならないように
        
        return delay
    
    def retry_with_backoff(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        operation_id: Optional[str] = None,
        config: Optional[RetryConfig] = None
    ) -> Any:
        """
        指数バックオフでリトライを実行
        
        Args:
            operation: 実行する操作（関数）
            operation_name: 操作名（ログ用）
            operation_id: 操作ID（履歴管理用）
            config: リトライ設定（Noneの場合はデフォルト）
        
        Returns:
            Any: 操作の戻り値
        
        Raises:
            Exception: 最大リトライ回数を超えた場合
        """
        if config is None:
            config = RetryConfig()
        
        if operation_id is None:
            operation_id = f"{operation_name}_{datetime.now().timestamp()}"
        
        # リトライ履歴を作成
        history = RetryHistory(
            operation_id=operation_id,
            operation_name=operation_name,
            started_at=datetime.now().isoformat()
        )
        self.retry_histories[operation_id] = history
        
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                self.logger.info(
                    f"Executing {operation_name} (attempt {attempt + 1}/{config.max_retries + 1})"
                )
                
                # 操作を実行
                result = operation()
                
                # 成功
                self.logger.info(f"Operation {operation_name} succeeded on attempt {attempt + 1}")
                
                # 成功の試行を記録
                success_attempt = RetryAttempt(
                    attempt_number=attempt + 1,
                    timestamp=datetime.now().isoformat(),
                    delay_seconds=0.0,
                    exception_type="None",
                    exception_message="Success",
                    success=True
                )
                history.add_attempt(success_attempt)
                history.mark_completed(success=True)
                
                return result
                
            except config.retry_on_exceptions as e:
                last_exception = e
                
                # 失敗の試行を記録
                delay = self._calculate_delay(attempt, config) if attempt < config.max_retries else 0.0
                
                failed_attempt = RetryAttempt(
                    attempt_number=attempt + 1,
                    timestamp=datetime.now().isoformat(),
                    delay_seconds=delay,
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                    stack_trace=traceback.format_exc(),
                    success=False
                )
                history.add_attempt(failed_attempt)
                
                if attempt < config.max_retries:
                    self.logger.warning(
                        f"Operation {operation_name} failed on attempt {attempt + 1}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # 遅延
                    if delay > 0:
                        time.sleep(delay)
                else:
                    # 最大リトライ回数に達した
                    self.logger.error(
                        f"Operation {operation_name} failed after {config.max_retries + 1} attempts"
                    )
                    history.mark_completed(success=False, exception=e)
                    raise
        
        # ここには到達しないはずだが、念のため
        history.mark_completed(success=False, exception=last_exception)
        raise last_exception
    
    def get_retry_history(self, operation_id: str) -> Optional[RetryHistory]:
        """
        リトライ履歴を取得
        
        Args:
            operation_id: 操作ID
        
        Returns:
            Optional[RetryHistory]: リトライ履歴（存在しない場合はNone）
        """
        return self.retry_histories.get(operation_id)
    
    def get_all_histories(self) -> List[RetryHistory]:
        """
        すべてのリトライ履歴を取得
        
        Returns:
            List[RetryHistory]: リトライ履歴のリスト
        """
        return list(self.retry_histories.values())
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """
        リトライ統計を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        total_operations = len(self.retry_histories)
        
        if total_operations == 0:
            return {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'success_rate': 0.0,
                'avg_attempts': 0.0,
                'total_retries': 0
            }
        
        successful = sum(1 for h in self.retry_histories.values() if h.success)
        failed = total_operations - successful
        total_attempts = sum(h.total_attempts for h in self.retry_histories.values())
        total_retries = sum(h.total_attempts - 1 for h in self.retry_histories.values())
        
        return {
            'total_operations': total_operations,
            'successful_operations': successful,
            'failed_operations': failed,
            'success_rate': successful / total_operations if total_operations > 0 else 0.0,
            'avg_attempts': total_attempts / total_operations if total_operations > 0 else 0.0,
            'total_retries': total_retries
        }
    
    def clear_history(self):
        """リトライ履歴をクリア"""
        self.retry_histories.clear()
        self.logger.info("Retry history cleared")
    
    def export_retry_log(self, output_file: str):
        """
        リトライログをエクスポート
        
        Args:
            output_file: 出力ファイルパス
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                [history.to_dict() for history in self.retry_histories.values()],
                f,
                indent=2,
                ensure_ascii=False
            )
        self.logger.info(f"Retry log exported to {output_file}")


# ================================================================================
# デコレーター (Decorator)
# ================================================================================

def retry(
    max_retries: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: tuple = (Exception,)
):
    """
    リトライデコレーター
    
    関数にリトライ機能を追加します。
    
    使用例:
        @retry(max_retries=3, initial_delay=1.0)
        def my_function():
            # 処理
            pass
    
    Args:
        max_retries: 最大リトライ回数
        strategy: リトライ戦略
        initial_delay: 初期遅延（秒）
        max_delay: 最大遅延（秒）
        backoff_multiplier: バックオフ乗数
        jitter: ジッターを追加するか
        retry_on_exceptions: リトライ対象の例外
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_retries=max_retries,
                strategy=strategy,
                initial_delay=initial_delay,
                max_delay=max_delay,
                backoff_multiplier=backoff_multiplier,
                jitter=jitter,
                retry_on_exceptions=retry_on_exceptions
            )
            
            manager = get_retry_manager()
            
            def operation():
                return func(*args, **kwargs)
            
            return manager.retry_with_backoff(
                operation=operation,
                operation_name=func.__name__,
                config=config
            )
        
        return wrapper
    return decorator


# ================================================================================
# グローバルリトライマネージャーインスタンス
# ================================================================================

# シングルトンインスタンス
_global_retry_manager: Optional[RetryManager] = None


def get_retry_manager() -> RetryManager:
    """グローバルリトライマネージャーを取得"""
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = RetryManager()
    return _global_retry_manager


# ================================================================================
# 便利関数 (Convenience Functions)
# ================================================================================

def retry_operation(
    operation: Callable[[], Any],
    operation_name: str,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> Any:
    """
    操作をリトライ実行する便利関数
    
    Args:
        operation: 実行する操作
        operation_name: 操作名
        max_retries: 最大リトライ回数
        initial_delay: 初期遅延（秒）
    
    Returns:
        Any: 操作の戻り値
    """
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay
    )
    
    manager = get_retry_manager()
    return manager.retry_with_backoff(
        operation=operation,
        operation_name=operation_name,
        config=config
    )
