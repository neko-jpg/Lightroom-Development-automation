# リトライロジック クイックリファレンス

## 概要

リトライマネージャーは、指数バックオフリトライ、リトライ上限管理、リトライ履歴記録機能を提供します。

**Requirements**: 14.1

## クイックスタート

### 1. 基本的な使用方法

```python
from retry_manager import RetryManager

manager = RetryManager()

def unstable_operation():
    # 不安定な処理
    return process_data()

result = manager.retry_with_backoff(
    operation=unstable_operation,
    operation_name="process_data"
)
```

### 2. デコレーターを使用

```python
from retry_manager import retry

@retry(max_retries=3, initial_delay=1.0)
def fetch_data():
    # データ取得処理
    return api.get_data()

result = fetch_data()
```

### 3. 便利関数を使用

```python
from retry_manager import retry_operation

result = retry_operation(
    operation=lambda: read_file("/path/to/file"),
    operation_name="read_file",
    max_retries=3,
    initial_delay=1.0
)
```

## リトライ戦略

### EXPONENTIAL_BACKOFF（指数バックオフ）

遅延が指数的に増加します。

```python
config = RetryConfig(
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay=1.0,
    backoff_multiplier=2.0
)
# 遅延: 1秒 → 2秒 → 4秒 → 8秒...
```

### LINEAR_BACKOFF（線形バックオフ）

遅延が線形に増加します。

```python
config = RetryConfig(
    strategy=RetryStrategy.LINEAR_BACKOFF,
    initial_delay=1.0
)
# 遅延: 1秒 → 2秒 → 3秒 → 4秒...
```

### FIXED_DELAY（固定遅延）

常に同じ遅延を使用します。

```python
config = RetryConfig(
    strategy=RetryStrategy.FIXED_DELAY,
    initial_delay=2.0
)
# 遅延: 2秒 → 2秒 → 2秒...
```

### IMMEDIATE（即座）

遅延なしで即座にリトライします。

```python
config = RetryConfig(
    strategy=RetryStrategy.IMMEDIATE
)
# 遅延: 0秒 → 0秒 → 0秒...
```

## カスタム設定

```python
from retry_manager import RetryConfig, RetryStrategy

config = RetryConfig(
    max_retries=5,                              # 最大リトライ回数
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF, # リトライ戦略
    initial_delay=1.0,                          # 初期遅延（秒）
    max_delay=60.0,                             # 最大遅延（秒）
    backoff_multiplier=2.0,                     # バックオフ乗数
    jitter=True,                                # ジッター有効
    retry_on_exceptions=(ValueError, IOError)   # リトライ対象の例外
)

manager.retry_with_backoff(
    operation=my_operation,
    operation_name="my_operation",
    config=config
)
```

## リトライ統計

```python
from retry_manager import get_retry_manager

manager = get_retry_manager()

# 統計を取得
stats = manager.get_retry_statistics()

print(f"総操作数: {stats['total_operations']}")
print(f"成功操作数: {stats['successful_operations']}")
print(f"失敗操作数: {stats['failed_operations']}")
print(f"成功率: {stats['success_rate']:.2%}")
print(f"平均試行回数: {stats['avg_attempts']:.2f}")
print(f"総リトライ回数: {stats['total_retries']}")
```

## リトライ履歴

```python
# 特定の操作の履歴を取得
history = manager.get_retry_history("operation_id")

if history:
    print(f"操作名: {history.operation_name}")
    print(f"成功: {history.success}")
    print(f"総試行回数: {history.total_attempts}")
    
    for attempt in history.attempts:
        print(f"  試行 {attempt.attempt_number}: {attempt.exception_message}")
```

## ログのエクスポート

```python
# リトライログをJSONファイルにエクスポート
manager.export_retry_log("retry_log.json")
```

## エラーハンドラーとの統合

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

## 実践的な例

### ファイル読み込みのリトライ

```python
from retry_manager import retry, RetryStrategy

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

### AI処理のリトライ

```python
@retry(
    max_retries=3,
    initial_delay=2.0,
    retry_on_exceptions=(TimeoutError,)
)
def llm_inference(prompt: str):
    return ollama_client.generate(prompt, timeout=30)
```

### クラウド同期のリトライ

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

### データベース操作のリトライ

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

## ベストプラクティス

### 1. 適切なリトライ戦略を選択

- **ネットワーク操作**: EXPONENTIAL_BACKOFF（サーバー負荷を分散）
- **ファイル操作**: LINEAR_BACKOFF または FIXED_DELAY
- **軽量操作**: IMMEDIATE

### 2. 最大リトライ回数を設定

```python
# 短時間で完了すべき操作
config = RetryConfig(max_retries=3)

# 重要だが時間がかかる操作
config = RetryConfig(max_retries=10)
```

### 3. リトライ対象の例外を限定

```python
# 特定の例外のみリトライ
config = RetryConfig(
    retry_on_exceptions=(ConnectionError, TimeoutError)
)
```

### 4. ジッターを有効化

同時リトライを分散させるため、ジッターを有効にします。

```python
config = RetryConfig(jitter=True)
```

### 5. 最大遅延を設定

無限に遅延が増加しないように最大遅延を設定します。

```python
config = RetryConfig(
    max_delay=60.0  # 最大60秒
)
```

## トラブルシューティング

### 問題: リトライが多すぎる

**解決策**: max_retriesを減らすか、retry_on_exceptionsを限定する

```python
config = RetryConfig(
    max_retries=2,
    retry_on_exceptions=(SpecificError,)
)
```

### 問題: リトライ間隔が長すぎる

**解決策**: initial_delayを減らすか、max_delayを設定する

```python
config = RetryConfig(
    initial_delay=0.5,
    max_delay=10.0
)
```

### 問題: すべての例外でリトライされる

**解決策**: retry_on_exceptionsを明示的に指定する

```python
config = RetryConfig(
    retry_on_exceptions=(ConnectionError, TimeoutError)
)
```

## パフォーマンス考慮事項

### メモリ使用量

リトライ履歴は自動的に保存されます。定期的にクリアしてください。

```python
# 1000件を超えたらクリア
if len(manager.retry_histories) > 1000:
    manager.clear_history()
```

### ログローテーション

リトライログは自動的にローテーションされます（5MB、10バックアップ）。

## API リファレンス

### RetryManager

```python
manager = RetryManager(log_file='logs/retry.log')

# リトライ実行
result = manager.retry_with_backoff(
    operation=callable,
    operation_name=str,
    operation_id=Optional[str],
    config=Optional[RetryConfig]
)

# 統計取得
stats = manager.get_retry_statistics()

# 履歴取得
history = manager.get_retry_history(operation_id)

# 履歴クリア
manager.clear_history()

# ログエクスポート
manager.export_retry_log(output_file)
```

### RetryConfig

```python
config = RetryConfig(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay=1.0,
    max_delay=60.0,
    backoff_multiplier=2.0,
    jitter=True,
    retry_on_exceptions=(Exception,)
)
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
    pass
```

### 便利関数

```python
result = retry_operation(
    operation=callable,
    operation_name=str,
    max_retries=3,
    initial_delay=1.0
)
```

## 関連ファイル

- `retry_manager.py` - メイン実装
- `test_retry_manager.py` - テストコード
- `example_retry_usage.py` - 使用例
- `error_handler.py` - エラーハンドラー統合

## まとめ

リトライマネージャーは、システムの堅牢性を向上させる重要なコンポーネントです。適切なリトライ戦略を選択し、統計を監視することで、システムの信頼性を最大化できます。
