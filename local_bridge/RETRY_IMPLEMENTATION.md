# リトライロジック実装ドキュメント

## 概要

Junmai AutoDevのリトライロジックは、指数バックオフリトライ、リトライ上限管理、リトライ履歴記録機能を提供します。このシステムは、要件14.1を満たすために設計されています。

**実装日**: 2025-11-08  
**バージョン**: 1.0  
**Requirements**: 14.1

## アーキテクチャ

### コンポーネント構成

```
retry_manager.py
├── リトライ設定
│   ├── RetryStrategy (列挙型)
│   └── RetryConfig (データクラス)
│
├── リトライ履歴
│   ├── RetryAttempt (データクラス)
│   └── RetryHistory (データクラス)
│
├── リトライマネージャー
│   └── RetryManager (メインクラス)
│
├── デコレーター
│   └── @retry
│
└── 便利関数
    ├── retry_operation()
    └── get_retry_manager()
```

## 主要機能

### 1. リトライ戦略

4種類のリトライ戦略を提供：

#### EXPONENTIAL_BACKOFF（指数バックオフ）

遅延が指数的に増加します。ネットワーク操作に最適。

```python
delay = initial_delay * (backoff_multiplier ^ attempt)
delay = min(delay, max_delay)

# 例: initial_delay=1.0, multiplier=2.0
# 遅延: 1秒 → 2秒 → 4秒 → 8秒 → 16秒...
```

**用途**:
- API呼び出し
- クラウド同期
- データベース接続

#### LINEAR_BACKOFF（線形バックオフ）

遅延が線形に増加します。

```python
delay = initial_delay * (attempt + 1)

# 例: initial_delay=1.0
# 遅延: 1秒 → 2秒 → 3秒 → 4秒 → 5秒...
```

**用途**:
- ファイル操作
- ローカルリソースアクセス

#### FIXED_DELAY（固定遅延）

常に同じ遅延を使用します。

```python
delay = initial_delay

# 例: initial_delay=2.0
# 遅延: 2秒 → 2秒 → 2秒 → 2秒...
```

**用途**:
- 定期的なポーリング
- リソース待機

#### IMMEDIATE（即座）

遅延なしで即座にリトライします。

```python
delay = 0.0

# 遅延: 0秒 → 0秒 → 0秒...
```

**用途**:
- 軽量操作
- 高速リトライが必要な場合

### 2. ジッター（Jitter）

同時リトライを分散させるため、遅延にランダム性を追加します。

```python
if jitter:
    jitter_amount = delay * 0.1  # 遅延の10%
    delay += random.uniform(-jitter_amount, jitter_amount)
    delay = max(0.0, delay)
```

**効果**:
- サーバー負荷の分散
- 同時リトライの衝突回避
- スロットリング回避

### 3. リトライ上限管理

#### 最大リトライ回数

```python
config = RetryConfig(max_retries=3)
# 総試行回数 = 初回 + 3回リトライ = 4回
```

#### リトライ対象の例外

特定の例外のみリトライ対象にできます。

```python
config = RetryConfig(
    retry_on_exceptions=(ConnectionError, TimeoutError)
)
```

#### 最大遅延

遅延が無限に増加しないように制限します。

```python
config = RetryConfig(
    max_delay=60.0  # 最大60秒
)
```

### 4. リトライ履歴記録

#### RetryAttempt（試行記録）

各試行の詳細を記録：

```python
@dataclass
class RetryAttempt:
    attempt_number: int          # 試行番号
    timestamp: str               # タイムスタンプ
    delay_seconds: float         # 遅延時間
    exception_type: str          # 例外タイプ
    exception_message: str       # 例外メッセージ
    stack_trace: Optional[str]   # スタックトレース
    success: bool                # 成功/失敗
```

#### RetryHistory（操作履歴）

操作全体の履歴を記録：

```python
@dataclass
class RetryHistory:
    operation_id: str                    # 操作ID
    operation_name: str                  # 操作名
    started_at: str                      # 開始時刻
    completed_at: Optional[str]          # 完了時刻
    total_attempts: int                  # 総試行回数
    success: bool                        # 成功/失敗
    final_exception: Optional[str]       # 最終例外
    attempts: List[RetryAttempt]         # 試行リスト
```

## 実装詳細

### RetryManager クラス

```python
class RetryManager:
    def __init__(self, log_file: str = 'logs/retry.log'):
        self.log_file = log_file
        self.retry_histories: Dict[str, RetryHistory] = {}
        self.logger = self._setup_logger()
    
    def retry_with_backoff(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        operation_id: Optional[str] = None,
        config: Optional[RetryConfig] = None
    ) -> Any:
        """指数バックオフでリトライを実行"""
        # リトライロジック
    
    def _calculate_delay(
        self,
        attempt: int,
        config: RetryConfig
    ) -> float:
        """リトライ遅延を計算"""
        # 遅延計算ロジック
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """リトライ統計を取得"""
        # 統計計算ロジック
```

### デコレーター

```python
@retry(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay=1.0,
    max_delay=60.0,
    backoff_multiplier=2.0,
    jitter=True,
    retry_on_exceptions=(Exception,)
)
def my_function():
    # 処理
    pass
```

### 便利関数

```python
result = retry_operation(
    operation=lambda: my_function(),
    operation_name="my_function",
    max_retries=3,
    initial_delay=1.0
)
```

## リトライフロー

### 成功フロー

```
操作実行
    ↓
成功
    ↓
結果を返す
    ↓
履歴に記録（1回の試行）
```

### リトライフロー

```
操作実行
    ↓
失敗（リトライ可能な例外）
    ↓
履歴に記録
    ↓
遅延計算（指数バックオフ）
    ↓
遅延待機
    ↓
リトライ実行
    ↓
成功 or 最大リトライ回数超過
```

### 最大リトライ回数超過フロー

```
操作実行
    ↓
失敗
    ↓
リトライ（最大回数まで）
    ↓
すべて失敗
    ↓
履歴に記録（失敗）
    ↓
例外を再スロー
```

## エラーハンドラーとの統合

### JunmaiErrorの拡張

```python
class JunmaiError(Exception):
    def should_retry(self) -> bool:
        """このエラーがリトライ可能かどうかを判定"""
        return self.recovery_strategy in [
            ErrorRecoveryStrategy.RETRY,
            ErrorRecoveryStrategy.RETRY_WITH_BACKOFF
        ]
    
    def get_retry_config(self) -> RetryConfig:
        """このエラーに適したリトライ設定を取得"""
        if self.recovery_strategy == ErrorRecoveryStrategy.RETRY:
            return RetryConfig(
                max_retries=3,
                strategy=RetryStrategy.IMMEDIATE
            )
        elif self.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF:
            return RetryConfig(
                max_retries=3,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                initial_delay=1.0
            )
```

### 統合使用例

```python
from error_handler import FileReadError, handle_error
from retry_manager import retry

@retry(max_retries=3, initial_delay=1.0)
def read_photo_file(file_path: str):
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except IOError as e:
        error = FileReadError(file_path, str(e))
        handle_error(error)
        raise
```

## 統計とモニタリング

### リトライ統計

```python
stats = manager.get_retry_statistics()

# 出力例:
{
    'total_operations': 100,
    'successful_operations': 85,
    'failed_operations': 15,
    'success_rate': 0.85,
    'avg_attempts': 1.5,
    'total_retries': 50
}
```

### 履歴の取得

```python
# 特定の操作の履歴
history = manager.get_retry_history("operation_id")

# すべての履歴
all_histories = manager.get_all_histories()
```

### ログのエクスポート

```python
manager.export_retry_log("retry_log.json")
```

## パフォーマンス考慮事項

### メモリ使用量

リトライ履歴は自動的に保存されます。定期的にクリアすることを推奨します。

```python
# 1000件を超えたらクリア
if len(manager.retry_histories) > 1000:
    manager.clear_history()
```

### ログローテーション

- 最大ファイルサイズ: 5MB
- バックアップ数: 10
- 自動ローテーション

### 計算量

- 遅延計算: O(1)
- ジッター追加: O(1)
- 履歴記録: O(1)

## ベストプラクティス

### 1. 適切なリトライ戦略を選択

| 操作タイプ | 推奨戦略 | 理由 |
|-----------|---------|------|
| ネットワーク操作 | EXPONENTIAL_BACKOFF | サーバー負荷を分散 |
| ファイル操作 | LINEAR_BACKOFF | 段階的な待機 |
| ローカルリソース | FIXED_DELAY | 一定間隔でチェック |
| 軽量操作 | IMMEDIATE | 高速リトライ |

### 2. リトライ対象の例外を限定

```python
# 良い例: 特定の例外のみリトライ
config = RetryConfig(
    retry_on_exceptions=(ConnectionError, TimeoutError)
)

# 悪い例: すべての例外をリトライ
config = RetryConfig(
    retry_on_exceptions=(Exception,)
)
```

### 3. 最大遅延を設定

```python
config = RetryConfig(
    max_delay=60.0  # 最大60秒
)
```

### 4. ジッターを有効化

```python
config = RetryConfig(
    jitter=True  # 同時リトライを分散
)
```

### 5. 適切な最大リトライ回数

```python
# 短時間で完了すべき操作
config = RetryConfig(max_retries=3)

# 重要だが時間がかかる操作
config = RetryConfig(max_retries=10)
```

## 実践的な使用例

### ファイル読み込み

```python
@retry(
    max_retries=3,
    initial_delay=1.0,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    retry_on_exceptions=(IOError, PermissionError)
)
def read_file(file_path: str):
    with open(file_path, 'r') as f:
        return f.read()
```

### AI処理

```python
@retry(
    max_retries=3,
    initial_delay=2.0,
    retry_on_exceptions=(TimeoutError,)
)
def llm_inference(prompt: str):
    return ollama_client.generate(prompt, timeout=30)
```

### クラウド同期

```python
@retry(
    max_retries=5,
    initial_delay=1.0,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    retry_on_exceptions=(ConnectionError, TimeoutError)
)
def upload_to_cloud(file_path: str):
    return cloud_storage.upload(file_path)
```

### データベース操作

```python
@retry(
    max_retries=3,
    initial_delay=0.5,
    retry_on_exceptions=(DatabaseConnectionError,)
)
def save_to_database(data: dict):
    with db.session() as session:
        session.add(data)
        session.commit()
```

## トラブルシューティング

### 問題: リトライが多すぎる

**症状**: 操作が何度もリトライされる

**解決策**:
```python
# max_retriesを減らす
config = RetryConfig(max_retries=2)

# または retry_on_exceptions を限定
config = RetryConfig(
    retry_on_exceptions=(SpecificError,)
)
```

### 問題: リトライ間隔が長すぎる

**症状**: リトライまでの待機時間が長い

**解決策**:
```python
# initial_delay を減らす
config = RetryConfig(initial_delay=0.5)

# または max_delay を設定
config = RetryConfig(max_delay=10.0)
```

### 問題: すべての例外でリトライされる

**症状**: リトライすべきでない例外もリトライされる

**解決策**:
```python
# retry_on_exceptions を明示的に指定
config = RetryConfig(
    retry_on_exceptions=(ConnectionError, TimeoutError)
)
```

### 問題: メモリ使用量が増加

**症状**: リトライ履歴でメモリを消費

**解決策**:
```python
# 定期的に履歴をクリア
if len(manager.retry_histories) > 1000:
    manager.clear_history()
```

## テスト戦略

### 単体テスト

```python
def test_retry_success_after_failures():
    manager = RetryManager()
    
    mock_operation = Mock(side_effect=[
        ValueError("Error 1"),
        ValueError("Error 2"),
        "success"
    ])
    
    result = manager.retry_with_backoff(
        operation=mock_operation,
        operation_name="test_operation"
    )
    
    assert result == "success"
    assert mock_operation.call_count == 3
```

### 統合テスト

```python
def test_real_world_file_read_retry():
    manager = get_retry_manager()
    
    def read_file():
        # 実際のファイル読み込み
        pass
    
    result = manager.retry_with_backoff(
        operation=read_file,
        operation_name="read_file"
    )
```

## 運用ガイドライン

### 1. リトライ統計の監視

```python
# 定期的に統計を確認
stats = manager.get_retry_statistics()

if stats['success_rate'] < 0.8:
    # 成功率が低い場合はアラート
    send_alert("Low retry success rate")
```

### 2. ログの分析

```python
# リトライログを定期的にエクスポート
manager.export_retry_log(f'reports/retry_{date}.json')
```

### 3. 履歴のクリーンアップ

```python
# 日次でクリーンアップ
manager.clear_history()
```

## 今後の拡張

### 1. 適応的リトライ

成功率に基づいて自動的にリトライ戦略を調整：

```python
if success_rate < 0.5:
    # リトライ回数を増やす
    config.max_retries += 1
```

### 2. 分散リトライ

複数のワーカー間でリトライを調整：

```python
# Redisを使用した分散ロック
with distributed_lock(operation_id):
    retry_with_backoff(operation)
```

### 3. リトライ予算

時間ベースのリトライ予算管理：

```python
config = RetryConfig(
    max_retry_time=300  # 最大5分間リトライ
)
```

### 4. メトリクス統合

Prometheus等のメトリクスシステムとの統合：

```python
retry_counter.inc()
retry_duration.observe(duration)
```

## 関連ファイル

- `retry_manager.py` - メイン実装
- `test_retry_manager.py` - テストコード
- `example_retry_usage.py` - 使用例
- `example_retry_error_integration.py` - エラーハンドラー統合例
- `RETRY_QUICK_REFERENCE.md` - クイックリファレンス
- `error_handler.py` - エラーハンドラー統合

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-11-08 | 1.0 | 初回リリース |

## まとめ

リトライロジックは、Junmai AutoDevの堅牢性を大幅に向上させる重要なコンポーネントです。適切なリトライ戦略を選択し、統計を監視することで、システムの信頼性を最大化できます。

**主な利点**:
- 一時的なエラーからの自動回復
- 詳細なリトライ履歴と統計
- 柔軟なリトライ戦略
- エラーハンドラーとのシームレスな統合
- 保守性の向上
