# フェイルセーフ機能実装 (Failsafe Feature Implementation)

## 概要

フェイルセーフマネージャーは、Junmai AutoDevシステムの信頼性と復旧能力を向上させる包括的な機能セットを提供します。

## 主要機能

### 1. 中間状態保存 (Checkpoint Management)

処理の途中状態を定期的に保存し、いつでも復旧可能にします。

**特徴:**
- 操作IDベースのチェックポイント管理
- 進捗率とデータの保存
- 自動的な古いチェックポイントのクリーンアップ
- JSON形式での永続化

**使用例:**
```python
from failsafe_manager import get_failsafe_manager, ProcessState

manager = get_failsafe_manager()

# チェックポイントを保存
checkpoint_id = manager.save_checkpoint(
    operation_id="batch_001",
    operation_name="Photo Processing",
    state=ProcessState.RUNNING,
    progress=0.5,
    data={'processed': 50, 'total': 100}
)

# チェックポイントを読み込み
checkpoint = manager.load_checkpoint(checkpoint_id)
```

### 2. 処理再開機能 (Resume Capability)

中断された処理を最後のチェックポイントから再開できます。

**特徴:**
- 再開可能性の自動判定
- コールバック関数による柔軟な再開処理
- 再開時の状態管理

**使用例:**
```python
# 再開可能かチェック
if manager.can_resume("batch_001"):
    # 再開処理
    def resume_callback(checkpoint):
        # チェックポイントデータを使用して処理を再開
        start_from = checkpoint.data['processed']
        # ... 処理を続行
        return "Resumed successfully"
    
    result = manager.resume_operation("batch_001", resume_callback)
```

### 3. 自動バックアップ (Automatic Backup)

重要なファイルを定期的に自動バックアップします。

**特徴:**
- 設定可能なバックアップ間隔
- チェックサムによる整合性検証
- 最大バックアップ数の管理
- バックグラウンドスレッドでの実行

**使用例:**
```python
# 手動バックアップ
backup_info = manager.create_backup('data/junmai.db')

# 自動バックアップを開始
manager.start_auto_backup([
    'data/junmai.db',
    'config/config.json'
])

# 自動バックアップを停止
manager.stop_auto_backup()
```

### 4. バックアップ復元 (Backup Restore)

バックアップから元の状態に復元できます。

**特徴:**
- チェックサムによる検証
- 復元前の一時バックアップ
- ロールバック機能

**使用例:**
```python
# バックアップを復元
restored_path = manager.restore_backup(backup_info.backup_id)

# 特定の場所に復元
restored_path = manager.restore_backup(
    backup_info.backup_id,
    restore_path='/path/to/restore'
)
```

### 5. クラッシュ後の自動復旧 (Crash Recovery)

システム起動時に未完了の操作を自動検出し、復旧を提案します。

**特徴:**
- 起動時の自動チェック
- 復旧可能な操作のリスト化
- 状態に基づく復旧戦略

**使用例:**
```python
# 復旧可能な操作を取得
recoverable = manager.get_recoverable_operations()

for op in recoverable:
    print(f"Operation: {op['operation_name']}")
    print(f"Progress: {op['progress']:.0%}")
    # 復旧処理を実行
```

## アーキテクチャ

### データ構造

#### CheckpointData
```python
@dataclass
class CheckpointData:
    checkpoint_id: str
    operation_id: str
    operation_name: str
    state: ProcessState
    timestamp: str
    progress: float  # 0.0 - 1.0
    data: Dict[str, Any]
    metadata: Dict[str, Any]
```

#### BackupInfo
```python
@dataclass
class BackupInfo:
    backup_id: str
    source_path: str
    backup_path: str
    timestamp: str
    size_bytes: int
    checksum: str
```

### 処理状態

```python
class ProcessState(Enum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"
```

## 設定

### 初期化パラメータ

```python
manager = FailsafeManager(
    checkpoint_dir='data/checkpoints',  # チェックポイント保存先
    backup_dir='data/backups',          # バックアップ保存先
    auto_backup_interval=300,           # 自動バックアップ間隔（秒）
    max_checkpoints=10,                 # 保持する最大チェックポイント数
    max_backups=5                       # 保持する最大バックアップ数
)
```

## ベストプラクティス

### 1. チェックポイントの頻度

- **短時間処理（< 1分）**: チェックポイント不要
- **中時間処理（1-10分）**: 処理の主要ステップごと
- **長時間処理（> 10分）**: 1-2分ごと、または進捗10%ごと

### 2. バックアップ戦略

- **データベース**: 処理開始前と完了後
- **設定ファイル**: 変更時
- **重要な中間ファイル**: 自動バックアップで定期的に

### 3. 復旧処理

```python
def safe_operation_with_checkpoints():
    manager = get_failsafe_manager()
    operation_id = "safe_op_001"
    
    # 既存のチェックポイントをチェック
    if manager.can_resume(operation_id):
        # 再開処理
        return manager.resume_operation(operation_id, resume_callback)
    
    # 新規処理
    try:
        for i in range(100):
            # 処理
            process_item(i)
            
            # 定期的にチェックポイントを保存
            if i % 10 == 0:
                manager.save_checkpoint(
                    operation_id=operation_id,
                    operation_name="Safe Operation",
                    state=ProcessState.RUNNING,
                    progress=i / 100,
                    data={'current_index': i}
                )
        
        # 完了
        manager.save_checkpoint(
            operation_id=operation_id,
            operation_name="Safe Operation",
            state=ProcessState.COMPLETED,
            progress=1.0,
            data={'status': 'completed'}
        )
        
    except Exception as e:
        # エラー時も状態を保存
        manager.save_checkpoint(
            operation_id=operation_id,
            operation_name="Safe Operation",
            state=ProcessState.FAILED,
            progress=i / 100,
            data={'error': str(e)}
        )
        raise
```

## パフォーマンス考慮事項

### チェックポイント保存

- **ファイルI/O**: JSON形式での保存は高速（< 10ms）
- **メモリ使用**: チェックポイントデータはメモリにもキャッシュ
- **ディスク使用**: 古いチェックポイントは自動削除

### バックアップ

- **コピー時間**: ファイルサイズに依存
- **チェックサム計算**: 大きなファイルでは数秒かかる可能性
- **並行処理**: バックグラウンドスレッドで実行

## エラーハンドリング

### チェックポイント保存失敗

```python
try:
    checkpoint_id = manager.save_checkpoint(...)
except Exception as e:
    logger.error(f"Failed to save checkpoint: {e}")
    # 処理は続行可能（チェックポイントなしで）
```

### バックアップ失敗

```python
try:
    backup_info = manager.create_backup(file_path)
except FileNotFoundError:
    logger.error(f"Source file not found: {file_path}")
except Exception as e:
    logger.error(f"Backup failed: {e}")
```

### 復元失敗

```python
try:
    restored_path = manager.restore_backup(backup_id)
except ValueError as e:
    logger.error(f"Invalid backup: {e}")
except Exception as e:
    logger.error(f"Restore failed: {e}")
    # 元のファイルは保護されている
```

## 統計とモニタリング

```python
# 統計情報を取得
stats = manager.get_statistics()

print(f"Checkpoints: {stats['checkpoints']['total']}")
print(f"Active operations: {stats['checkpoints']['active_operations']}")
print(f"Backups: {stats['backups']['total']}")
print(f"Total backup size: {stats['backups']['total_size_mb']:.2f} MB")
```

## 要件との対応

- **Requirement 14.3**: 中間状態保存機能 ✓
- **Requirement 14.4**: 処理再開機能 ✓
- **Requirement 14.5**: 自動バックアップ機能 ✓
- **Requirement 14.5**: クラッシュ後の自動復旧 ✓

## 関連ドキュメント

- [エラーハンドラー実装](ERROR_HANDLER_IMPLEMENTATION.md)
- [リトライマネージャー実装](RETRY_IMPLEMENTATION.md)
- [クイックスタートガイド](FAILSAFE_QUICK_START.md)
