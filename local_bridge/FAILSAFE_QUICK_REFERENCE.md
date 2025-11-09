# フェイルセーフ機能 クイックリファレンス

## 初期化

```python
from failsafe_manager import get_failsafe_manager, ProcessState

manager = get_failsafe_manager()
```

## チェックポイント

### 保存
```python
checkpoint_id = manager.save_checkpoint(
    operation_id="op_001",
    operation_name="My Operation",
    state=ProcessState.RUNNING,
    progress=0.5,
    data={'key': 'value'}
)
```

### 読み込み
```python
checkpoint = manager.load_checkpoint(checkpoint_id)
latest = manager.get_latest_checkpoint(operation_id)
```

### 再開
```python
if manager.can_resume(operation_id):
    result = manager.resume_operation(operation_id, callback_func)
```

## バックアップ

### 作成
```python
backup_info = manager.create_backup('path/to/file')
```

### 復元
```python
restored_path = manager.restore_backup(backup_info.backup_id)
```

### 自動バックアップ
```python
# 開始
manager.start_auto_backup(['file1.db', 'file2.json'])

# 停止
manager.stop_auto_backup()
```

## クラッシュ復旧

```python
# 復旧可能な操作を取得
recoverable = manager.get_recoverable_operations()

for op in recoverable:
    print(f"{op['operation_name']}: {op['progress']:.0%}")
```

## 統計

```python
stats = manager.get_statistics()
print(f"Checkpoints: {stats['checkpoints']['total']}")
print(f"Backups: {stats['backups']['total']}")
```

## 処理状態

- `ProcessState.INITIALIZED` - 初期化済み
- `ProcessState.RUNNING` - 実行中
- `ProcessState.PAUSED` - 一時停止
- `ProcessState.COMPLETED` - 完了
- `ProcessState.FAILED` - 失敗
- `ProcessState.RECOVERING` - 復旧中

## ベストプラクティス

1. **定期的なチェックポイント**: 長時間処理では1-2分ごと
2. **重要なファイルのバックアップ**: 処理前後に実行
3. **エラー時も状態保存**: 失敗状態でもチェックポイントを保存
4. **起動時の復旧チェック**: アプリケーション起動時に実行

## ファイル構造

```
data/
├── checkpoints/
│   ├── checkpoint_op_001_20251109_120000.json
│   └── checkpoint_op_002_20251109_120100.json
└── backups/
    ├── backup_index.json
    ├── junmai_backup_20251109_120000.db
    └── config_backup_20251109_120100.json
```

## ログ

```
logs/
└── failsafe.log  # フェイルセーフ操作のログ
```
