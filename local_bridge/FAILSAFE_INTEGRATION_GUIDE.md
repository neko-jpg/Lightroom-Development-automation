# フェイルセーフ統合ガイド (Failsafe Integration Guide)

## 概要

このガイドでは、フェイルセーフマネージャーを他のシステムコンポーネント（エラーハンドラー、リトライマネージャー）と統合する方法を説明します。

## 統合アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Failsafe   │  │    Error     │  │    Retry     │
│   Manager    │  │   Handler    │  │   Manager    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Logging System │
                  └─────────────────┘
```

## 基本的な統合パターン

### パターン1: 保護された処理

```python
from failsafe_manager import get_failsafe_manager, ProcessState
from error_handler import get_error_handler
from retry_manager import get_retry_manager, RetryConfig

def protected_operation(operation_id, operation_name, items):
    """完全に保護された処理"""
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    # 1. バックアップを作成
    backup_info = failsafe.create_backup('data/important.db')
    
    # 2. 初期チェックポイント
    failsafe.save_checkpoint(
        operation_id=operation_id,
        operation_name=operation_name,
        state=ProcessState.INITIALIZED,
        progress=0.0,
        data={'processed': 0, 'total': len(items)}
    )
    
    # 3. 処理を実行
    processed = 0
    for i, item in enumerate(items):
        try:
            # リトライ付きで処理
            def process_item():
                # 実際の処理
                return process(item)
            
            result = retry_manager.retry_with_backoff(
                operation=process_item,
                operation_name=f"process_{item}",
                config=RetryConfig(max_retries=3)
            )
            
            processed += 1
            
        except Exception as e:
            # エラーを記録
            error_handler.handle_error(e, context={'item': item})
        
        # 定期的にチェックポイント
        if (i + 1) % 10 == 0:
            failsafe.save_checkpoint(
                operation_id=operation_id,
                operation_name=operation_name,
                state=ProcessState.RUNNING,
                progress=(i + 1) / len(items),
                data={'processed': processed, 'total': len(items)}
            )
    
    # 4. 完了チェックポイント
    failsafe.save_checkpoint(
        operation_id=operation_id,
        operation_name=operation_name,
        state=ProcessState.COMPLETED,
        progress=1.0,
        data={'processed': processed, 'total': len(items)}
    )
    
    return processed
```

### パターン2: 再開可能な処理

```python
def resumable_operation(operation_id, operation_name, items):
    """再開可能な処理"""
    failsafe = get_failsafe_manager()
    
    # 既存のチェックポイントをチェック
    if failsafe.can_resume(operation_id):
        print("Resuming from checkpoint...")
        
        def resume_callback(checkpoint):
            # チェックポイントから再開
            start_from = checkpoint.data['processed']
            return process_items(items[start_from:], start_from)
        
        return failsafe.resume_operation(operation_id, resume_callback)
    
    # 新規処理
    return process_items(items, 0)


def process_items(items, start_index):
    """アイテムを処理"""
    failsafe = get_failsafe_manager()
    
    for i, item in enumerate(items, start=start_index):
        # 処理
        process(item)
        
        # チェックポイント
        if i % 10 == 0:
            failsafe.save_checkpoint(
                operation_id=operation_id,
                operation_name=operation_name,
                state=ProcessState.RUNNING,
                progress=i / total_items,
                data={'processed': i}
            )
    
    return len(items)
```

### パターン3: エラー回復付き処理

```python
def error_recoverable_operation(operation_id, items):
    """エラー回復機能付き処理"""
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    
    try:
        # 処理を実行
        for i, item in enumerate(items):
            try:
                process(item)
            except Exception as e:
                # エラーを記録
                error_context = error_handler.handle_error(e)
                
                # エラー状態を保存
                failsafe.save_checkpoint(
                    operation_id=operation_id,
                    operation_name="Error Recovery",
                    state=ProcessState.PAUSED,
                    progress=i / len(items),
                    data={
                        'processed': i,
                        'last_error': error_context.message,
                        'error_code': error_context.error_code
                    }
                )
                
                # エラーが回復可能かチェック
                if error_context.recovery_strategy.value == 'retry':
                    # リトライ
                    continue
                else:
                    # 処理を中断
                    raise
        
        # 成功
        failsafe.save_checkpoint(
            operation_id=operation_id,
            operation_name="Error Recovery",
            state=ProcessState.COMPLETED,
            progress=1.0,
            data={'status': 'completed'}
        )
        
    except Exception as e:
        # 最終的な失敗
        failsafe.save_checkpoint(
            operation_id=operation_id,
            operation_name="Error Recovery",
            state=ProcessState.FAILED,
            progress=i / len(items),
            data={'final_error': str(e)}
        )
        raise
```

## 起動時の復旧処理

```python
def startup_recovery():
    """アプリケーション起動時の復旧処理"""
    failsafe = get_failsafe_manager()
    
    # 復旧可能な操作を取得
    recoverable = failsafe.get_recoverable_operations()
    
    if not recoverable:
        print("No operations need recovery")
        return
    
    print(f"Found {len(recoverable)} operations to recover:")
    
    for op in recoverable:
        print(f"\nOperation: {op['operation_name']}")
        print(f"  - ID: {op['operation_id']}")
        print(f"  - Progress: {op['progress']:.0%}")
        print(f"  - State: {op['state']}")
        
        # ユーザーに確認
        response = input("  Recover this operation? (y/n): ")
        
        if response.lower() == 'y':
            try:
                # 復旧処理を実行
                def recovery_callback(checkpoint):
                    # 操作タイプに応じた復旧処理
                    if checkpoint.operation_name == "Photo Processing":
                        return recover_photo_processing(checkpoint)
                    elif checkpoint.operation_name == "Export":
                        return recover_export(checkpoint)
                    else:
                        return recover_generic(checkpoint)
                
                result = failsafe.resume_operation(
                    op['operation_id'],
                    recovery_callback
                )
                
                print(f"  ✓ Recovery successful: {result}")
                
            except Exception as e:
                print(f"  ✗ Recovery failed: {e}")
```

## 自動バックアップの設定

```python
def setup_auto_backup():
    """自動バックアップを設定"""
    failsafe = get_failsafe_manager()
    
    # 重要なファイルのリスト
    critical_files = [
        'data/junmai.db',           # データベース
        'config/config.json',        # 設定ファイル
        'data/sessions.db',          # セッションデータ
    ]
    
    # 存在するファイルのみをフィルタ
    from pathlib import Path
    existing_files = [
        f for f in critical_files
        if Path(f).exists()
    ]
    
    if existing_files:
        # 自動バックアップを開始（5分間隔）
        failsafe.start_auto_backup(existing_files)
        print(f"Auto backup started for {len(existing_files)} files")
    
    # アプリケーション終了時に停止
    import atexit
    atexit.register(failsafe.stop_auto_backup)
```

## 統計とモニタリング

```python
def monitor_system_health():
    """システムヘルスをモニタリング"""
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    # 統計を収集
    failsafe_stats = failsafe.get_statistics()
    error_stats = error_handler.get_error_statistics()
    retry_stats = retry_manager.get_retry_statistics()
    
    # ヘルスチェック
    health = {
        'status': 'healthy',
        'issues': []
    }
    
    # チェックポイントの確認
    if failsafe_stats['checkpoints']['active_operations'] > 10:
        health['issues'].append('Too many active operations')
        health['status'] = 'warning'
    
    # エラー率の確認
    if error_stats['total_errors'] > 100:
        health['issues'].append('High error count')
        health['status'] = 'warning'
    
    # リトライ成功率の確認
    if retry_stats['success_rate'] < 0.8:
        health['issues'].append('Low retry success rate')
        health['status'] = 'critical'
    
    # バックアップサイズの確認
    if failsafe_stats['backups']['total_size_mb'] > 1000:
        health['issues'].append('Backup size exceeds 1GB')
        health['status'] = 'warning'
    
    return health
```

## ベストプラクティス

### 1. レイヤー化された保護

```python
# レイヤー1: リトライ（一時的なエラー）
# レイヤー2: エラーハンドリング（エラー記録）
# レイヤー3: フェイルセーフ（状態保存）

def layered_protection(item):
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    # チェックポイントを保存
    failsafe.save_checkpoint(...)
    
    try:
        # リトライ付きで実行
        result = retry_manager.retry_with_backoff(
            operation=lambda: process(item),
            operation_name="process_item"
        )
        return result
        
    except Exception as e:
        # エラーを記録
        error_handler.handle_error(e)
        
        # 失敗状態を保存
        failsafe.save_checkpoint(..., state=ProcessState.FAILED)
        
        raise
```

### 2. 定期的なクリーンアップ

```python
def periodic_cleanup():
    """定期的なクリーンアップ"""
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    # 完了したチェックポイントをクリア
    failsafe.clear_completed_checkpoints()
    
    # エラー履歴をクリア（古いもの）
    error_handler.clear_history()
    
    # リトライ履歴をクリア
    retry_manager.clear_history()
    
    print("Cleanup completed")
```

### 3. ログの統合

```python
import logging

# 統合ロガーの設定
def setup_integrated_logging():
    """統合ロギングを設定"""
    
    # メインロガー
    main_logger = logging.getLogger('junmai_autodev')
    main_logger.setLevel(logging.INFO)
    
    # ハンドラー
    handler = logging.FileHandler('logs/integrated.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    main_logger.addHandler(handler)
    
    # 各コンポーネントのロガーを統合
    for component in ['failsafe', 'errors', 'retry']:
        logger = logging.getLogger(f'junmai_autodev.{component}')
        logger.addHandler(handler)
```

## トラブルシューティング

### 問題: チェックポイントが多すぎる

**解決策**:
```python
# max_checkpointsを調整
manager = FailsafeManager(max_checkpoints=5)

# または定期的にクリーンアップ
manager.clear_completed_checkpoints()
```

### 問題: バックアップサイズが大きい

**解決策**:
```python
# max_backupsを減らす
manager = FailsafeManager(max_backups=3)

# または古いバックアップを手動削除
# （自動クリーンアップが実行される）
```

### 問題: 復旧が失敗する

**解決策**:
```python
# エラーハンドリングを追加
try:
    result = manager.resume_operation(op_id, callback)
except Exception as e:
    # エラーを記録
    error_handler.handle_error(e)
    
    # 手動で状態をリセット
    manager.save_checkpoint(
        operation_id=op_id,
        operation_name="Manual Reset",
        state=ProcessState.FAILED,
        progress=0.0,
        data={'reset_reason': str(e)}
    )
```

## 関連ドキュメント

- [フェイルセーフ実装](FAILSAFE_IMPLEMENTATION.md)
- [エラーハンドラー実装](ERROR_HANDLER_IMPLEMENTATION.md)
- [リトライマネージャー実装](RETRY_IMPLEMENTATION.md)
- [統合例](example_failsafe_integration.py)
