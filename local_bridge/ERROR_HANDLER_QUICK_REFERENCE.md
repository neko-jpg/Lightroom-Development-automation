# エラーハンドラー クイックリファレンス

## 概要

Junmai AutoDevのエラー分類システムは、包括的なエラー処理、ロギング、回復戦略を提供します。

**Requirements**: 14.1, 14.2

## エラーカテゴリ

| カテゴリ | 説明 | 例 |
|---------|------|-----|
| `FILE_SYSTEM` | ファイルシステム関連 | ファイル読み込み失敗、ディスク容量不足 |
| `AI_PROCESSING` | AI処理関連 | LLMタイムアウト、GPU OOM |
| `LIGHTROOM_INTEGRATION` | Lightroom統合関連 | カタログロック、プラグイン通信失敗 |
| `EXPORT` | エクスポート関連 | 書き出し失敗、クラウド同期エラー |
| `DATABASE` | データベース関連 | 接続失敗、クエリエラー |
| `NETWORK` | ネットワーク関連 | 接続タイムアウト、API エラー |
| `RESOURCE` | リソース関連 | CPU過負荷、GPU過熱 |
| `VALIDATION` | バリデーション関連 | 入力検証失敗 |
| `CONFIGURATION` | 設定関連 | 設定ファイルエラー |

## エラー重要度

| 重要度 | 説明 | 対応 |
|--------|------|------|
| `CRITICAL` | システム停止が必要 | 即座の対応 |
| `HIGH` | 即座の対応が必要 | 優先的に対応 |
| `MEDIUM` | 通常の対応が必要 | 通常対応 |
| `LOW` | 記録のみ | 監視 |
| `INFO` | 情報レベル | 記録のみ |

## エラー回復戦略

| 戦略 | 説明 | 使用例 |
|------|------|--------|
| `RETRY` | 即座にリトライ | 一時的なネットワークエラー |
| `RETRY_WITH_BACKOFF` | 指数バックオフでリトライ | API レート制限 |
| `WAIT_FOR_RESOURCE` | リソース待機 | GPU メモリ不足 |
| `SKIP` | スキップして続行 | 個別写真の処理失敗 |
| `FAIL_QUEUE` | 失敗キューへ移動 | 最大リトライ超過 |
| `NOTIFY_USER` | ユーザー通知 | 設定エラー |
| `SYSTEM_HALT` | システム停止 | ディスク容量不足 |

## 基本的な使用方法

### 1. エラーハンドラーの初期化

```python
from error_handler import ErrorHandler

# カスタムログファイルで初期化
handler = ErrorHandler(log_file='logs/errors.log')

# またはグローバルハンドラーを使用
from error_handler import get_error_handler
handler = get_error_handler()
```

### 2. エラーの発生と処理

```python
from error_handler import FileReadError, handle_error

try:
    # 何らかの処理
    raise FileReadError("/path/to/file.jpg", "File not found")
except Exception as e:
    # エラーを処理
    context = handle_error(e, {'user_id': 'user123'})
    print(f"エラーコード: {context.error_code}")
    print(f"回復戦略: {context.recovery_strategy.value}")
```

### 3. カスタムエラーの作成

```python
from error_handler import JunmaiError, ErrorCategory, ErrorSeverity

class CustomError(JunmaiError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            error_code='CUSTOM_ERROR'
        )
```

## 主要なエラークラス

### ファイルシステムエラー

```python
from error_handler import (
    FileReadError,
    FileWriteError,
    DiskSpaceError
)

# ファイル読み込みエラー
error = FileReadError("/path/to/file.jpg", "Permission denied")

# ファイル書き込みエラー
error = FileWriteError("/path/to/output.jpg", "Disk full")

# ディスク容量不足
error = DiskSpaceError(required_mb=1000, available_mb=500)
```

### AI処理エラー

```python
from error_handler import (
    LLMTimeoutError,
    GPUOutOfMemoryError,
    ModelLoadError
)

# LLMタイムアウト
error = LLMTimeoutError("llama3.1:8b", timeout_seconds=30)

# GPU メモリ不足
error = GPUOutOfMemoryError(required_mb=8000, available_mb=6000)

# モデル読み込み失敗
error = ModelLoadError("llama3.1:8b", "Model file not found")
```

### Lightroomエラー

```python
from error_handler import (
    CatalogLockError,
    PluginCommunicationError,
    DevelopSettingsError
)

# カタログロック
error = CatalogLockError("/path/to/catalog.lrcat", wait_time_seconds=300)

# プラグイン通信エラー
error = PluginCommunicationError("Connection refused")

# 現像設定エラー
error = DevelopSettingsError("photo_123", "WhiteLayer_v4", "Invalid parameter")
```

### エクスポートエラー

```python
from error_handler import (
    ExportFailedError,
    CloudSyncError
)

# 書き出し失敗
error = ExportFailedError("photo_456", "JPEG", "Codec error")

# クラウド同期エラー
error = CloudSyncError("Dropbox", "/photos/image.jpg", "Network timeout")
```

### リソースエラー

```python
from error_handler import (
    CPUOverloadError,
    GPUOverheatError
)

# CPU過負荷
error = CPUOverloadError(current_usage=95.5, threshold=80.0)

# GPU過熱
error = GPUOverheatError(current_temp=82.0, threshold=75.0)
```

## エラー統計の取得

```python
handler = get_error_handler()

# 統計を取得
stats = handler.get_error_statistics()

print(f"総エラー数: {stats['total_errors']}")
print(f"カテゴリ別: {stats['by_category']}")
print(f"重要度別: {stats['by_severity']}")
print(f"コード別: {stats['by_code']}")
print(f"最近のエラー: {stats['recent_errors']}")
```

## エラーログのエクスポート

```python
handler = get_error_handler()

# JSON形式でエクスポート
handler.export_error_log('logs/error_export.json')
```

## リトライロジックの実装例

```python
from error_handler import ErrorRecoveryStrategy
import time

def process_with_retry(file_path: str, max_retries: int = 3):
    """指数バックオフでリトライ"""
    for attempt in range(max_retries):
        try:
            # 処理を実行
            process_file(file_path)
            return True
        except Exception as e:
            context = handle_error(e)
            
            if context.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1, 2, 4秒
                    time.sleep(wait_time)
                else:
                    return False
            else:
                return False
```

## リソース監視の実装例

```python
from error_handler import CPUOverloadError, GPUOverheatError

def check_resources():
    """システムリソースをチェック"""
    cpu_usage = get_cpu_usage()
    if cpu_usage > 80.0:
        error = CPUOverloadError(cpu_usage, 80.0)
        context = handle_error(error)
        # 処理速度を制限
        throttle_processing()
    
    gpu_temp = get_gpu_temperature()
    if gpu_temp > 75.0:
        error = GPUOverheatError(gpu_temp, 75.0)
        context = handle_error(error)
        # 処理を一時停止
        pause_processing()
```

## エラーコンテキストの活用

```python
try:
    # 処理
    raise FileReadError("/photo.jpg")
except Exception as e:
    context = handle_error(e, {
        'user_id': 'user123',
        'session_id': 'session456',
        'photo_count': 120
    })
    
    # コンテキスト情報を使用
    print(f"エラー: {context.message}")
    print(f"ユーザー: {context.details['user_id']}")
    print(f"セッション: {context.details['session_id']}")
```

## ベストプラクティス

### 1. 適切なエラークラスを使用

```python
# ❌ 悪い例
raise Exception("File not found")

# ✅ 良い例
raise FileReadError("/path/to/file.jpg", "File not found")
```

### 2. コンテキスト情報を追加

```python
# ❌ 悪い例
handle_error(error)

# ✅ 良い例
handle_error(error, {
    'user_id': user_id,
    'session_id': session_id,
    'operation': 'export'
})
```

### 3. 回復戦略に従う

```python
context = handle_error(error)

if context.recovery_strategy == ErrorRecoveryStrategy.RETRY:
    retry_operation()
elif context.recovery_strategy == ErrorRecoveryStrategy.SKIP:
    skip_and_continue()
elif context.recovery_strategy == ErrorRecoveryStrategy.SYSTEM_HALT:
    shutdown_system()
```

### 4. 定期的に統計を確認

```python
# 定期的にエラー統計を確認
stats = handler.get_error_statistics()
if stats['total_errors'] > 100:
    send_alert_to_admin()
```

## トラブルシューティング

### ログファイルが作成されない

```python
# ディレクトリが存在することを確認
import os
os.makedirs('logs', exist_ok=True)

handler = ErrorHandler(log_file='logs/errors.log')
```

### エラー履歴が多すぎる

```python
# 定期的にクリア
handler = get_error_handler()
handler.clear_history()
```

### カスタムエラーが正しく分類されない

```python
# 正しいカテゴリと重要度を指定
class MyError(JunmaiError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,  # 明示的に指定
            severity=ErrorSeverity.HIGH,        # 明示的に指定
            error_code='MY_ERROR'
        )
```

## 関連ドキュメント

- [要件定義書](../.kiro/specs/ui-ux-enhancement/requirements.md) - Requirement 14
- [設計書](../.kiro/specs/ui-ux-enhancement/design.md) - Error Handling セクション
- [テストコード](test_error_handler.py) - 詳細なテスト例

## サポート

問題が発生した場合は、以下を確認してください：

1. ログファイル: `logs/errors.log`
2. エラー統計: `handler.get_error_statistics()`
3. エクスポートログ: `handler.export_error_log('debug.json')`
