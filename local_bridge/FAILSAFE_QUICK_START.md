# フェイルセーフ機能 クイックスタートガイド

## 5分で始めるフェイルセーフ機能

### 1. 基本的な使い方

```python
from failsafe_manager import get_failsafe_manager, ProcessState

# マネージャーを取得
manager = get_failsafe_manager()
```

### 2. チェックポイントの保存

```python
# 処理の途中でチェックポイントを保存
checkpoint_id = manager.save_checkpoint(
    operation_id="my_operation",
    operation_name="Photo Processing",
    state=ProcessState.RUNNING,
    progress=0.5,  # 50%完了
    data={'processed': 50, 'total': 100}
)
```

### 3. 処理の再開

```python
# 再開可能かチェック
if manager.can_resume("my_operation"):
    # 再開処理を定義
    def resume_work(checkpoint):
        start_from = checkpoint.data['processed']
        total = checkpoint.data['total']
        
        # 残りの処理を実行
        for i in range(start_from, total):
            # 処理...
            pass
        
        return "Completed"
    
    # 再開実行
    result = manager.resume_operation("my_operation", resume_work)
```

### 4. バックアップの作成

```python
# 重要なファイルをバックアップ
backup_info = manager.create_backup('data/junmai.db')
print(f"Backup created: {backup_info.backup_id}")
```

### 5. バックアップの復元

```python
# バックアップから復元
restored_path = manager.restore_backup(backup_info.backup_id)
print(f"Restored to: {restored_path}")
```

### 6. 自動バックアップ

```python
# 自動バックアップを開始（5分間隔）
manager.start_auto_backup([
    'data/junmai.db',
    'config/config.json'
])

# 停止
manager.stop_auto_backup()
```

### 7. クラッシュ復旧

```python
# 起動時に復旧可能な操作をチェック
recoverable = manager.get_recoverable_operations()

for op in recoverable:
    print(f"Found: {op['operation_name']} at {op['progress']:.0%}")
    # 復旧処理...
```

## 実践例

### 長時間処理の保護

```python
def protected_batch_processing():
    manager = get_failsafe_manager()
    operation_id = "batch_001"
    
    # バックアップを作成
    manager.create_backup('data/junmai.db')
    
    try:
        for i in range(100):
            # 処理
            process_photo(i)
            
            # 10枚ごとにチェックポイント
            if i % 10 == 0:
                manager.save_checkpoint(
                    operation_id=operation_id,
                    operation_name="Batch Processing",
                    state=ProcessState.RUNNING,
                    progress=i / 100,
                    data={'index': i}
                )
        
        # 完了
        manager.save_checkpoint(
            operation_id=operation_id,
            operation_name="Batch Processing",
            state=ProcessState.COMPLETED,
            progress=1.0,
            data={'status': 'done'}
        )
        
    except Exception as e:
        # エラー時も保存
        manager.save_checkpoint(
            operation_id=operation_id,
            operation_name="Batch Processing",
            state=ProcessState.FAILED,
            progress=i / 100,
            data={'error': str(e)}
        )
        raise
```

## よくある質問

### Q: チェックポイントはどのくらいの頻度で保存すべき？

**A:** 処理時間に応じて：
- 短時間（< 1分）: 不要
- 中時間（1-10分）: 主要ステップごと
- 長時間（> 10分）: 1-2分ごと

### Q: バックアップはどこに保存される？

**A:** デフォルトでは `data/backups/` ディレクトリに保存されます。

### Q: 古いチェックポイントは自動削除される？

**A:** はい、デフォルトで最新10個のみ保持されます。

### Q: 自動バックアップの間隔は変更できる？

**A:** はい、初期化時に設定できます：
```python
manager = FailsafeManager(auto_backup_interval=600)  # 10分
```

## 次のステップ

- [詳細実装ドキュメント](FAILSAFE_IMPLEMENTATION.md)
- [使用例](example_failsafe_usage.py)
- [テストコード](test_failsafe_manager.py)
