# エラー分類システム実装ドキュメント

## 概要

Junmai AutoDevのエラー分類システムは、包括的なエラー処理、ロギング、回復戦略を提供します。このシステムは、要件14.1および14.2を満たすために設計されています。

**実装日**: 2025-11-08  
**バージョン**: 1.0  
**Requirements**: 14.1, 14.2

## アーキテクチャ

### コンポーネント構成

```
error_handler.py
├── エラータイプ定義
│   ├── ErrorCategory (列挙型)
│   ├── ErrorSeverity (列挙型)
│   └── ErrorRecoveryStrategy (列挙型)
│
├── エラーコンテキスト
│   └── ErrorContext (データクラス)
│
├── カスタムエラークラス
│   ├── JunmaiError (基底クラス)
│   ├── FileSystemError
│   │   ├── FileReadError
│   │   ├── FileWriteError
│   │   └── DiskSpaceError
│   ├── AIProcessingError
│   │   ├── LLMTimeoutError
│   │   ├── GPUOutOfMemoryError
│   │   └── ModelLoadError
│   ├── LightroomError
│   │   ├── CatalogLockError
│   │   ├── PluginCommunicationError
│   │   └── DevelopSettingsError
│   ├── ExportError
│   │   ├── ExportFailedError
│   │   └── CloudSyncError
│   ├── DatabaseError
│   │   └── DatabaseConnectionError
│   └── ResourceError
│       ├── CPUOverloadError
│       └── GPUOverheatError
│
└── エラーハンドラー
    ├── ErrorHandler (メインクラス)
    ├── get_error_handler() (シングルトン取得)
    └── handle_error() (便利関数)
```

## 主要機能

### 1. エラー分類

エラーは以下のカテゴリに分類されます：

- **FILE_SYSTEM**: ファイルシステム関連のエラー
- **AI_PROCESSING**: AI処理関連のエラー
- **LIGHTROOM_INTEGRATION**: Lightroom統合関連のエラー
- **EXPORT**: エクスポート関連のエラー
- **DATABASE**: データベース関連のエラー
- **NETWORK**: ネットワーク関連のエラー
- **RESOURCE**: リソース関連のエラー
- **VALIDATION**: バリデーション関連のエラー
- **CONFIGURATION**: 設定関連のエラー
- **UNKNOWN**: 未分類のエラー

### 2. エラー重要度

エラーの重要度は5段階で評価されます：

- **CRITICAL**: システム停止が必要（例: ディスク容量不足）
- **HIGH**: 即座の対応が必要（例: GPU OOM）
- **MEDIUM**: 通常の対応が必要（例: ファイル読み込み失敗）
- **LOW**: 記録のみ（例: 軽微な警告）
- **INFO**: 情報レベル（例: 処理完了通知）

### 3. エラー回復戦略

各エラーには適切な回復戦略が定義されています：

- **RETRY**: 即座にリトライ
- **RETRY_WITH_BACKOFF**: 指数バックオフでリトライ
- **WAIT_FOR_RESOURCE**: リソースが利用可能になるまで待機
- **SKIP**: エラーをスキップして続行
- **FAIL_QUEUE**: 失敗キューへ移動
- **NOTIFY_USER**: ユーザーに通知
- **SYSTEM_HALT**: システムを停止

### 4. エラーロギング

エラーは構造化されたログとして記録されます：

```python
{
    "timestamp": "2025-11-08T10:00:00",
    "category": "file_system",
    "severity": "medium",
    "recovery_strategy": "retry_backoff",
    "error_code": "FS_READ_ERROR",
    "message": "Failed to read file: /path/to/file.jpg",
    "details": {
        "file_path": "/path/to/file.jpg",
        "reason": "Permission denied"
    },
    "stack_trace": "...",
    "retry_count": 0,
    "max_retries": 3
}
```

## 実装詳細

### ErrorContext データクラス

エラーコンテキスト情報を保持するデータクラス：

```python
@dataclass
class ErrorContext:
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
```

### JunmaiError 基底クラス

すべてのカスタムエラーの基底クラス：

```python
class JunmaiError(Exception):
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_strategy: ErrorRecoveryStrategy = ErrorRecoveryStrategy.NOTIFY_USER,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        # 初期化処理
```

### ErrorHandler クラス

エラーの処理、ロギング、統計収集を管理：

```python
class ErrorHandler:
    def __init__(self, log_file: str = 'logs/errors.log'):
        self.log_file = log_file
        self.error_history: List[ErrorContext] = []
        self.error_counts: Dict[str, int] = {}
        self.logger = self._setup_logger()
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        # エラー処理ロジック
    
    def get_error_statistics(self) -> Dict[str, Any]:
        # 統計情報を返す
    
    def export_error_log(self, output_file: str):
        # エラーログをエクスポート
```

## エラーフロー

### 1. ファイルシステムエラーのフロー

```
ファイル読み込み試行
    ↓
FileReadError 発生
    ↓
ErrorHandler.handle_error()
    ↓
エラーコンテキスト作成
    ↓
ログに記録
    ↓
回復戦略: RETRY_WITH_BACKOFF
    ↓
指数バックオフでリトライ (1秒, 2秒, 4秒)
    ↓
最大リトライ回数超過
    ↓
失敗キューへ移動
```

### 2. AI処理エラーのフロー

```
LLM推論実行
    ↓
タイムアウト発生
    ↓
LLMTimeoutError 発生
    ↓
ErrorHandler.handle_error()
    ↓
エラーコンテキスト作成
    ↓
ログに記録
    ↓
回復戦略: RETRY_WITH_BACKOFF
    ↓
温度パラメータ調整
    ↓
リトライ実行
```

### 3. リソースエラーのフロー

```
GPU温度監視
    ↓
過熱検知 (82°C > 75°C)
    ↓
GPUOverheatError 発生
    ↓
ErrorHandler.handle_error()
    ↓
エラーコンテキスト作成
    ↓
ログに記録
    ↓
回復戦略: WAIT_FOR_RESOURCE
    ↓
処理を一時停止
    ↓
温度が閾値以下に低下
    ↓
処理を再開
```

## 統合ポイント

### 1. ホットフォルダー監視との統合

```python
from error_handler import FileReadError, handle_error

def process_new_file(file_path: str):
    try:
        # ファイル処理
        process_file(file_path)
    except IOError as e:
        error = FileReadError(file_path, str(e))
        context = handle_error(error, {'source': 'hot_folder'})
        
        if context.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF:
            schedule_retry(file_path, context.retry_count)
```

### 2. AI選別エンジンとの統合

```python
from error_handler import LLMTimeoutError, GPUOutOfMemoryError, handle_error

def evaluate_photo(photo_path: str):
    try:
        # AI評価
        result = ai_selector.evaluate(photo_path)
        return result
    except TimeoutError as e:
        error = LLMTimeoutError("llama3.1:8b", 30)
        context = handle_error(error, {'photo_path': photo_path})
        return None
    except MemoryError as e:
        error = GPUOutOfMemoryError(8000, 6000)
        context = handle_error(error)
        # 量子化モデルに切り替え
        switch_to_quantized_model()
```

### 3. Lightroomプラグインとの統合

```python
from error_handler import CatalogLockError, DevelopSettingsError, handle_error

def apply_develop_settings(photo_id: str, settings: dict):
    try:
        # 現像設定を適用
        lightroom.apply_settings(photo_id, settings)
    except CatalogLockedException as e:
        error = CatalogLockError(catalog_path, 300)
        context = handle_error(error)
        
        if context.recovery_strategy == ErrorRecoveryStrategy.WAIT_FOR_RESOURCE:
            wait_for_catalog_unlock(300)
            retry_apply_settings(photo_id, settings)
```

### 4. エクスポートパイプラインとの統合

```python
from error_handler import ExportFailedError, CloudSyncError, handle_error

def export_photo(photo_id: str, format: str):
    try:
        # 書き出し
        export_file = lightroom.export(photo_id, format)
        
        # クラウド同期
        cloud_sync.upload(export_file)
    except ExportException as e:
        error = ExportFailedError(photo_id, format, str(e))
        context = handle_error(error)
        
        # 代替フォーマットで再試行
        if format == "TIFF":
            export_photo(photo_id, "JPEG")
    except SyncException as e:
        error = CloudSyncError("Dropbox", export_file, str(e))
        context = handle_error(error)
        
        # ローカル保存して後で再試行
        save_to_local_queue(export_file)
```

## パフォーマンス考慮事項

### 1. ログローテーション

エラーログは自動的にローテーションされます：

- 最大ファイルサイズ: 5MB
- バックアップ数: 10
- 古いログは自動削除

### 2. メモリ管理

エラー履歴は定期的にクリアされます：

```python
# 1000件を超えたらクリア
if len(handler.error_history) > 1000:
    handler.clear_history()
```

### 3. 非同期ロギング

重い処理はバックグラウンドで実行：

```python
# 将来の拡張: 非同期ロギング
async def log_error_async(context: ErrorContext):
    await asyncio.to_thread(logger.log, context)
```

## テスト戦略

### 1. 単体テスト

各エラークラスとハンドラーの機能をテスト：

```bash
py -m pytest local_bridge/test_error_handler.py -v
```

### 2. 統合テスト

実際のワークフローでのエラー処理をテスト：

```python
def test_end_to_end_error_handling():
    # ファイル処理 → エラー → リトライ → 成功
    pass
```

### 3. ストレステスト

大量のエラーを処理してパフォーマンスを確認：

```python
def test_handle_1000_errors():
    handler = ErrorHandler()
    for i in range(1000):
        handler.handle_error(FileReadError(f"/file{i}.jpg"))
    
    stats = handler.get_error_statistics()
    assert stats['total_errors'] == 1000
```

## 運用ガイドライン

### 1. エラー監視

定期的にエラー統計を確認：

```python
# 毎時実行
stats = handler.get_error_statistics()
if stats['by_severity'].get('critical', 0) > 0:
    send_alert_to_admin()
```

### 2. ログ分析

エラーログを定期的に分析：

```bash
# エラーコード別の集計
grep "error_code" logs/errors.log | sort | uniq -c
```

### 3. エラーレポート

週次でエラーレポートを生成：

```python
handler.export_error_log(f'reports/errors_{date}.json')
```

## トラブルシューティング

### 問題: ログファイルが作成されない

**解決策**:
```python
import os
os.makedirs('logs', exist_ok=True)
```

### 問題: エラー履歴が多すぎてメモリを圧迫

**解決策**:
```python
# 定期的にクリア
handler.clear_history()
```

### 問題: カスタムエラーが正しく分類されない

**解決策**:
```python
# カテゴリと重要度を明示的に指定
class MyError(JunmaiError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            error_code='MY_ERROR'
        )
```

## 今後の拡張

### 1. エラー通知の強化

- メール通知
- Slack通知
- LINE Notify統合

### 2. エラー分析の自動化

- 機械学習によるエラーパターン検出
- 自動的な回復戦略の最適化

### 3. ダッシュボード統合

- リアルタイムエラー監視
- エラートレンドの可視化

## 関連ファイル

- `error_handler.py` - メイン実装
- `test_error_handler.py` - テストコード
- `example_error_handler_usage.py` - 使用例
- `ERROR_HANDLER_QUICK_REFERENCE.md` - クイックリファレンス

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-11-08 | 1.0 | 初回リリース |

## まとめ

エラー分類システムは、Junmai AutoDevの堅牢性と保守性を大幅に向上させます。適切なエラー処理により、システムの信頼性が向上し、問題の早期発見と解決が可能になります。

**主な利点**:
- 統一されたエラー処理
- 詳細なエラーログ
- 自動的な回復戦略
- エラー統計と分析
- 保守性の向上
