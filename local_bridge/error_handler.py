"""
エラー分類システム (Error Classification System)

このモジュールは、Junmai AutoDevシステムの包括的なエラー分類、
ハンドリング、ロギング機能を提供します。

Requirements: 14.1, 14.2
"""

import logging
import traceback
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# リトライマネージャーのインポート（循環インポート回避のため遅延インポート）
try:
    from retry_manager import get_retry_manager, RetryConfig, RetryStrategy
    RETRY_MANAGER_AVAILABLE = True
except ImportError:
    RETRY_MANAGER_AVAILABLE = False


# ================================================================================
# エラータイプ定義 (Error Type Definitions)
# ================================================================================

class ErrorCategory(Enum):
    """エラーカテゴリの列挙型"""
    FILE_SYSTEM = "file_system"
    AI_PROCESSING = "ai_processing"
    LIGHTROOM_INTEGRATION = "lightroom_integration"
    EXPORT = "export"
    DATABASE = "database"
    NETWORK = "network"
    RESOURCE = "resource"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """エラー重要度の列挙型"""
    CRITICAL = "critical"  # システム停止が必要
    HIGH = "high"          # 即座の対応が必要
    MEDIUM = "medium"      # 通常の対応が必要
    LOW = "low"            # 記録のみ
    INFO = "info"          # 情報レベル


class ErrorRecoveryStrategy(Enum):
    """エラー回復戦略の列挙型"""
    RETRY = "retry"                    # リトライ
    RETRY_WITH_BACKOFF = "retry_backoff"  # 指数バックオフでリトライ
    WAIT_FOR_RESOURCE = "wait_resource"   # リソース待機
    SKIP = "skip"                      # スキップして続行
    FAIL_QUEUE = "fail_queue"          # 失敗キューへ移動
    NOTIFY_USER = "notify_user"        # ユーザー通知
    SYSTEM_HALT = "system_halt"        # システム停止


# ================================================================================
# カスタムエラークラス (Custom Error Classes)
# ================================================================================

@dataclass
class ErrorContext:
    """エラーコンテキスト情報"""
    timestamp: str
    category: ErrorCategory
    severity: ErrorSeverity
    recovery_strategy: ErrorRecoveryStrategy
    error_code: str
    message: str
    details: Dict[str, Any]
    stack_trace: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'timestamp': self.timestamp,
            'category': self.category.value,
            'severity': self.severity.value,
            'recovery_strategy': self.recovery_strategy.value,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'stack_trace': self.stack_trace,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }


class JunmaiError(Exception):
    """Junmai AutoDevの基底エラークラス"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.NOTIFY_USER,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.recovery_strategy = recovery_strategy
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.stack_trace = traceback.format_exc()
    
    def get_context(self) -> ErrorContext:
        """エラーコンテキストを取得"""
        return ErrorContext(
            timestamp=self.timestamp,
            category=self.category,
            severity=self.severity,
            recovery_strategy=self.recovery_strategy,
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            stack_trace=self.stack_trace
        )
    
    def should_retry(self) -> bool:
        """このエラーがリトライ可能かどうかを判定"""
        return self.recovery_strategy in [
            ErrorRecoveryStrategy.RETRY,
            ErrorRecoveryStrategy.RETRY_WITH_BACKOFF
        ]
    
    def get_retry_config(self) -> 'RetryConfig':
        """このエラーに適したリトライ設定を取得"""
        if not RETRY_MANAGER_AVAILABLE:
            return None
        
        # 回復戦略に基づいてリトライ設定を決定
        if self.recovery_strategy == ErrorRecoveryStrategy.RETRY:
            return RetryConfig(
                max_retries=3,
                strategy=RetryStrategy.IMMEDIATE,
                initial_delay=0.0
            )
        elif self.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF:
            return RetryConfig(
                max_retries=3,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                initial_delay=1.0,
                max_delay=60.0,
                backoff_multiplier=2.0
            )
        else:
            return None


# ================================================================================
# ファイルシステムエラー (File System Errors)
# ================================================================================

class FileSystemError(JunmaiError):
    """ファイルシステム関連のエラー"""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        details = kwargs.pop('details', {})
        if file_path:
            details['file_path'] = file_path
        
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_SYSTEM,
            severity=kwargs.pop('severity', ErrorSeverity.MEDIUM),
            recovery_strategy=kwargs.pop('recovery_strategy', ErrorRecoveryStrategy.RETRY),
            error_code=kwargs.pop('error_code', 'FS_ERROR'),
            details=details
        )


class FileReadError(FileSystemError):
    """ファイル読み込みエラー"""
    
    def __init__(self, file_path: str, reason: str = None):
        super().__init__(
            message=f"Failed to read file: {file_path}",
            file_path=file_path,
            error_code='FS_READ_ERROR',
            recovery_strategy=ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            details={'reason': reason} if reason else {}
        )


class FileWriteError(FileSystemError):
    """ファイル書き込みエラー"""
    
    def __init__(self, file_path: str, reason: str = None):
        super().__init__(
            message=f"Failed to write file: {file_path}",
            file_path=file_path,
            error_code='FS_WRITE_ERROR',
            recovery_strategy=ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            details={'reason': reason} if reason else {}
        )


class DiskSpaceError(FileSystemError):
    """ディスク容量不足エラー"""
    
    def __init__(self, required_mb: float, available_mb: float):
        super().__init__(
            message=f"Insufficient disk space: required {required_mb}MB, available {available_mb}MB",
            error_code='FS_DISK_SPACE',
            severity=ErrorSeverity.CRITICAL,
            recovery_strategy=ErrorRecoveryStrategy.SYSTEM_HALT,
            details={
                'required_mb': required_mb,
                'available_mb': available_mb
            }
        )


# ================================================================================
# AI処理エラー (AI Processing Errors)
# ================================================================================

class AIProcessingError(JunmaiError):
    """AI処理関連のエラー"""
    
    def __init__(self, message: str, model_name: str = None, **kwargs):
        details = kwargs.pop('details', {})
        if model_name:
            details['model_name'] = model_name
        
        super().__init__(
            message=message,
            category=ErrorCategory.AI_PROCESSING,
            severity=kwargs.pop('severity', ErrorSeverity.HIGH),
            recovery_strategy=kwargs.pop('recovery_strategy', ErrorRecoveryStrategy.RETRY),
            error_code=kwargs.pop('error_code', 'AI_ERROR'),
            details=details
        )


class LLMTimeoutError(AIProcessingError):
    """LLM応答タイムアウトエラー"""
    
    def __init__(self, model_name: str, timeout_seconds: int):
        super().__init__(
            message=f"LLM response timeout after {timeout_seconds}s",
            model_name=model_name,
            error_code='AI_LLM_TIMEOUT',
            recovery_strategy=ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            details={'timeout_seconds': timeout_seconds}
        )


class GPUOutOfMemoryError(AIProcessingError):
    """GPU メモリ不足エラー"""
    
    def __init__(self, required_mb: float, available_mb: float):
        super().__init__(
            message=f"GPU out of memory: required {required_mb}MB, available {available_mb}MB",
            error_code='AI_GPU_OOM',
            severity=ErrorSeverity.HIGH,
            recovery_strategy=ErrorRecoveryStrategy.WAIT_FOR_RESOURCE,
            details={
                'required_mb': required_mb,
                'available_mb': available_mb,
                'suggestion': 'Consider enabling model quantization'
            }
        )


class ModelLoadError(AIProcessingError):
    """モデル読み込みエラー"""
    
    def __init__(self, model_name: str, reason: str = None):
        super().__init__(
            message=f"Failed to load model: {model_name}",
            model_name=model_name,
            error_code='AI_MODEL_LOAD',
            severity=ErrorSeverity.CRITICAL,
            recovery_strategy=ErrorRecoveryStrategy.NOTIFY_USER,
            details={'reason': reason} if reason else {}
        )


# ================================================================================
# Lightroom統合エラー (Lightroom Integration Errors)
# ================================================================================

class LightroomError(JunmaiError):
    """Lightroom統合関連のエラー"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.LIGHTROOM_INTEGRATION,
            severity=kwargs.pop('severity', ErrorSeverity.HIGH),
            recovery_strategy=kwargs.pop('recovery_strategy', ErrorRecoveryStrategy.RETRY),
            error_code=kwargs.pop('error_code', 'LR_ERROR'),
            details=kwargs.pop('details', {})
        )


class CatalogLockError(LightroomError):
    """カタログロックエラー"""
    
    def __init__(self, catalog_path: str, wait_time_seconds: int = 300):
        super().__init__(
            message=f"Lightroom catalog is locked: {catalog_path}",
            error_code='LR_CATALOG_LOCK',
            recovery_strategy=ErrorRecoveryStrategy.WAIT_FOR_RESOURCE,
            details={
                'catalog_path': catalog_path,
                'wait_time_seconds': wait_time_seconds
            }
        )


class PluginCommunicationError(LightroomError):
    """プラグイン通信エラー"""
    
    def __init__(self, reason: str = None):
        super().__init__(
            message="Failed to communicate with Lightroom plugin",
            error_code='LR_PLUGIN_COMM',
            recovery_strategy=ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            details={'reason': reason} if reason else {}
        )


class DevelopSettingsError(LightroomError):
    """現像設定適用エラー"""
    
    def __init__(self, photo_id: str, setting_name: str, reason: str = None):
        super().__init__(
            message=f"Failed to apply develop settings to photo {photo_id}",
            error_code='LR_DEVELOP_SETTINGS',
            recovery_strategy=ErrorRecoveryStrategy.SKIP,
            details={
                'photo_id': photo_id,
                'setting_name': setting_name,
                'reason': reason
            }
        )


# ================================================================================
# エクスポートエラー (Export Errors)
# ================================================================================

class ExportError(JunmaiError):
    """エクスポート関連のエラー"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.EXPORT,
            severity=kwargs.pop('severity', ErrorSeverity.MEDIUM),
            recovery_strategy=kwargs.pop('recovery_strategy', ErrorRecoveryStrategy.RETRY),
            error_code=kwargs.pop('error_code', 'EXPORT_ERROR'),
            details=kwargs.pop('details', {})
        )


class ExportFailedError(ExportError):
    """書き出し失敗エラー"""
    
    def __init__(self, photo_id: str, format: str, reason: str = None):
        super().__init__(
            message=f"Failed to export photo {photo_id} as {format}",
            error_code='EXPORT_FAILED',
            recovery_strategy=ErrorRecoveryStrategy.RETRY,
            details={
                'photo_id': photo_id,
                'format': format,
                'reason': reason
            }
        )


class CloudSyncError(ExportError):
    """クラウド同期エラー"""
    
    def __init__(self, provider: str, file_path: str, reason: str = None):
        super().__init__(
            message=f"Failed to sync to {provider}: {file_path}",
            error_code='EXPORT_CLOUD_SYNC',
            recovery_strategy=ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            details={
                'provider': provider,
                'file_path': file_path,
                'reason': reason
            }
        )


# ================================================================================
# データベースエラー (Database Errors)
# ================================================================================

class DatabaseError(JunmaiError):
    """データベース関連のエラー"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=kwargs.pop('severity', ErrorSeverity.HIGH),
            recovery_strategy=kwargs.pop('recovery_strategy', ErrorRecoveryStrategy.RETRY),
            error_code=kwargs.pop('error_code', 'DB_ERROR'),
            details=kwargs.pop('details', {})
        )


class DatabaseConnectionError(DatabaseError):
    """データベース接続エラー"""
    
    def __init__(self, db_path: str, reason: str = None):
        super().__init__(
            message=f"Failed to connect to database: {db_path}",
            error_code='DB_CONNECTION',
            severity=ErrorSeverity.CRITICAL,
            recovery_strategy=ErrorRecoveryStrategy.RETRY_WITH_BACKOFF,
            details={
                'db_path': db_path,
                'reason': reason
            }
        )


# ================================================================================
# リソースエラー (Resource Errors)
# ================================================================================

class ResourceError(JunmaiError):
    """リソース関連のエラー"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=kwargs.pop('severity', ErrorSeverity.MEDIUM),
            recovery_strategy=kwargs.pop('recovery_strategy', ErrorRecoveryStrategy.WAIT_FOR_RESOURCE),
            error_code=kwargs.pop('error_code', 'RESOURCE_ERROR'),
            details=kwargs.pop('details', {})
        )


class CPUOverloadError(ResourceError):
    """CPU過負荷エラー"""
    
    def __init__(self, current_usage: float, threshold: float):
        super().__init__(
            message=f"CPU overload: {current_usage}% (threshold: {threshold}%)",
            error_code='RESOURCE_CPU_OVERLOAD',
            details={
                'current_usage': current_usage,
                'threshold': threshold
            }
        )


class GPUOverheatError(ResourceError):
    """GPU過熱エラー"""
    
    def __init__(self, current_temp: float, threshold: float):
        super().__init__(
            message=f"GPU overheating: {current_temp}°C (threshold: {threshold}°C)",
            error_code='RESOURCE_GPU_OVERHEAT',
            severity=ErrorSeverity.HIGH,
            details={
                'current_temp': current_temp,
                'threshold': threshold
            }
        )


# ================================================================================
# エラーハンドラー (Error Handler)
# ================================================================================

class ErrorHandler:
    """
    統合エラーハンドラー
    
    エラーの分類、ロギング、回復戦略の実行を管理します。
    """
    
    def __init__(self, log_file: str = 'logs/errors.log'):
        """
        Args:
            log_file: エラーログファイルのパス
        """
        self.log_file = log_file
        self.error_history: List[ErrorContext] = []
        self.error_counts: Dict[str, int] = {}
        
        # ロガーの設定
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """ロガーのセットアップ"""
        logger = logging.getLogger('junmai_autodev.errors')
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
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """
        エラーを処理する
        
        Args:
            error: 発生したエラー
            context: 追加のコンテキスト情報
        
        Returns:
            ErrorContext: エラーコンテキスト
        """
        # JunmaiErrorの場合はコンテキストを取得
        if isinstance(error, JunmaiError):
            error_context = error.get_context()
            
            # 追加コンテキストをマージ
            if context:
                error_context.details.update(context)
        else:
            # 一般的な例外の場合は新しいコンテキストを作成
            error_context = ErrorContext(
                timestamp=datetime.now().isoformat(),
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                recovery_strategy=ErrorRecoveryStrategy.NOTIFY_USER,
                error_code='UNKNOWN_ERROR',
                message=str(error),
                details=context or {},
                stack_trace=traceback.format_exc()
            )
        
        # エラーをログに記録
        self._log_error(error_context)
        
        # エラー履歴に追加
        self.error_history.append(error_context)
        
        # エラーカウントを更新
        self.error_counts[error_context.error_code] = \
            self.error_counts.get(error_context.error_code, 0) + 1
        
        return error_context
    
    def _log_error(self, error_context: ErrorContext):
        """エラーをログに記録"""
        log_message = (
            f"[{error_context.error_code}] {error_context.message} | "
            f"Category: {error_context.category.value} | "
            f"Severity: {error_context.severity.value} | "
            f"Recovery: {error_context.recovery_strategy.value}"
        )
        
        # 重要度に応じてログレベルを変更
        if error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # 詳細情報をJSON形式でログ
        self.logger.debug(f"Error details: {json.dumps(error_context.to_dict(), indent=2)}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計を取得"""
        total_errors = len(self.error_history)
        
        if total_errors == 0:
            return {
                'total_errors': 0,
                'by_category': {},
                'by_severity': {},
                'by_code': {},
                'recent_errors': []
            }
        
        # カテゴリ別集計
        by_category = {}
        for error in self.error_history:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # 重要度別集計
        by_severity = {}
        for error in self.error_history:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # 最近のエラー（最新10件）
        recent_errors = [
            error.to_dict()
            for error in self.error_history[-10:]
        ]
        
        return {
            'total_errors': total_errors,
            'by_category': by_category,
            'by_severity': by_severity,
            'by_code': self.error_counts.copy(),
            'recent_errors': recent_errors
        }
    
    def clear_history(self):
        """エラー履歴をクリア"""
        self.error_history.clear()
        self.error_counts.clear()
    
    def export_error_log(self, output_file: str):
        """エラーログをエクスポート"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                [error.to_dict() for error in self.error_history],
                f,
                indent=2,
                ensure_ascii=False
            )


# ================================================================================
# グローバルエラーハンドラーインスタンス
# ================================================================================

# シングルトンインスタンス
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """グローバルエラーハンドラーを取得"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
    """エラーを処理する（便利関数）"""
    return get_error_handler().handle_error(error, context)
