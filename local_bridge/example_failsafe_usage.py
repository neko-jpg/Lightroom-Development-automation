"""
フェイルセーフマネージャーの使用例 (Failsafe Manager Usage Examples)

このスクリプトは、フェイルセーフマネージャーの主要機能の使用方法を示します。
"""

import os
import sys
import time
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from failsafe_manager import (
    FailsafeManager,
    ProcessState,
    get_failsafe_manager
)


def example_checkpoint_workflow():
    """チェックポイントを使用したワークフローの例"""
    print("\n" + "=" * 60)
    print("Example 1: Checkpoint Workflow")
    print("=" * 60)
    
    manager = get_failsafe_manager()
    
    # 長時間実行される処理をシミュレート
    operation_id = "photo_batch_001"
    operation_name = "Batch Photo Processing"
    total_photos = 100
    
    print(f"\nStarting {operation_name}...")
    print(f"Total photos: {total_photos}")
    
    for i in range(0, total_photos, 10):
        # 10枚ごとにチェックポイントを保存
        progress = (i + 10) / total_photos
        
        checkpoint_id = manager.save_checkpoint(
            operation_id=operation_id,
            operation_name=operation_name,
            state=ProcessState.RUNNING,
            progress=progress,
            data={
                'processed_photos': i + 10,
                'total_photos': total_photos,
                'current_batch': i // 10 + 1
            },
            metadata={
                'start_time': time.time(),
                'user': 'photographer_001'
            }
        )
        
        print(f"  Checkpoint saved: {progress:.0%} complete ({i + 10}/{total_photos} photos)")
        
        # 処理をシミュレート
        time.sleep(0.5)
    
    # 完了状態を保存
    manager.save_checkpoint(
        operation_id=operation_id,
        operation_name=operation_name,
        state=ProcessState.COMPLETED,
        progress=1.0,
        data={
            'processed_photos': total_photos,
            'total_photos': total_photos,
            'status': 'completed'
        }
    )
    
    print(f"\n✓ {operation_name} completed!")


def example_resume_after_interruption():
    """中断後の処理再開の例"""
    print("\n" + "=" * 60)
    print("Example 2: Resume After Interruption")
    print("=" * 60)
    
    manager = get_failsafe_manager()
    
    operation_id = "export_batch_001"
    operation_name = "Photo Export"
    
    # 中断された処理をシミュレート
    print(f"\nSimulating interrupted {operation_name}...")
    manager.save_checkpoint(
        operation_id=operation_id,
        operation_name=operation_name,
        state=ProcessState.PAUSED,
        progress=0.6,
        data={
            'exported_photos': 60,
            'total_photos': 100,
            'export_format': 'JPEG',
            'quality': 95
        }
    )
    print("  Process interrupted at 60% completion")
    
    # 再開可能かチェック
    if manager.can_resume(operation_id):
        print("\n✓ Process can be resumed")
        
        # 再開処理
        def resume_export(checkpoint):
            print(f"\nResuming from checkpoint...")
            print(f"  - Progress: {checkpoint.progress:.0%}")
            print(f"  - Exported: {checkpoint.data['exported_photos']}/{checkpoint.data['total_photos']}")
            print(f"  - Format: {checkpoint.data['export_format']}")
            
            # 残りの処理を実行
            remaining = checkpoint.data['total_photos'] - checkpoint.data['exported_photos']
            print(f"\nExporting remaining {remaining} photos...")
            
            for i in range(remaining):
                time.sleep(0.1)  # 処理をシミュレート
                if (i + 1) % 10 == 0:
                    print(f"  Exported {i + 1}/{remaining} photos")
            
            return "Export completed successfully"
        
        result = manager.resume_operation(operation_id, resume_export)
        print(f"\n✓ {result}")
    else:
        print("\n✗ Process cannot be resumed")


def example_automatic_backup():
    """自動バックアップの例"""
    print("\n" + "=" * 60)
    print("Example 3: Automatic Backup")
    print("=" * 60)
    
    manager = get_failsafe_manager()
    
    # 重要なファイルのパスを設定
    important_files = [
        'data/junmai.db',  # データベース
        'config/config.json',  # 設定ファイル
    ]
    
    # 存在するファイルのみをフィルタ
    existing_files = [f for f in important_files if Path(f).exists()]
    
    if not existing_files:
        print("\nNo files to backup (creating test file)")
        test_file = Path('data/test_backup.txt')
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Test backup data")
        existing_files = [str(test_file)]
    
    print(f"\nFiles to backup: {len(existing_files)}")
    for file in existing_files:
        print(f"  - {file}")
    
    # 手動バックアップを作成
    print("\nCreating manual backups...")
    for file_path in existing_files:
        try:
            backup_info = manager.create_backup(file_path)
            print(f"  ✓ Backed up: {Path(file_path).name}")
            print(f"    - Backup ID: {backup_info.backup_id}")
            print(f"    - Size: {backup_info.size_bytes} bytes")
        except Exception as e:
            print(f"  ✗ Failed to backup {file_path}: {e}")
    
    # 統計情報を表示
    stats = manager.get_statistics()
    print(f"\nBackup Statistics:")
    print(f"  - Total backups: {stats['backups']['total']}")
    print(f"  - Total size: {stats['backups']['total_size_mb']:.2f} MB")


def example_crash_recovery():
    """クラッシュ復旧の例"""
    print("\n" + "=" * 60)
    print("Example 4: Crash Recovery")
    print("=" * 60)
    
    manager = get_failsafe_manager()
    
    # 復旧可能な操作を確認
    recoverable = manager.get_recoverable_operations()
    
    if recoverable:
        print(f"\nFound {len(recoverable)} operations that need recovery:")
        
        for op in recoverable:
            print(f"\n  Operation: {op['operation_name']}")
            print(f"  - ID: {op['operation_id']}")
            print(f"  - State: {op['state']}")
            print(f"  - Progress: {op['progress']:.0%}")
            print(f"  - Timestamp: {op['timestamp']}")
            
            # 復旧を提案
            print(f"\n  Would you like to recover this operation? (y/n)")
            # 実際のアプリケーションではユーザー入力を待つ
            # response = input("  > ")
            # if response.lower() == 'y':
            #     # 復旧処理を実行
            #     pass
    else:
        print("\n✓ No operations need recovery")
        print("  All operations completed successfully or were properly closed")


def example_backup_restore():
    """バックアップ復元の例"""
    print("\n" + "=" * 60)
    print("Example 5: Backup Restore")
    print("=" * 60)
    
    manager = get_failsafe_manager()
    
    # テストファイルを作成
    test_file = Path('data/restore_test.txt')
    test_file.parent.mkdir(parents=True, exist_ok=True)
    original_content = "Original content - Version 1"
    test_file.write_text(original_content)
    
    print(f"\nCreated test file: {test_file}")
    print(f"  Content: {original_content}")
    
    # バックアップを作成
    backup_info = manager.create_backup(str(test_file))
    print(f"\n✓ Backup created: {backup_info.backup_id}")
    
    # ファイルを変更
    modified_content = "Modified content - Version 2"
    test_file.write_text(modified_content)
    print(f"\nFile modified")
    print(f"  New content: {modified_content}")
    
    # バックアップから復元
    print(f"\nRestoring from backup...")
    restored_path = manager.restore_backup(backup_info.backup_id)
    
    # 復元されたファイルの内容を確認
    restored_content = Path(restored_path).read_text()
    print(f"✓ File restored: {restored_path}")
    print(f"  Restored content: {restored_content}")
    
    # 検証
    if restored_content == original_content:
        print("\n✓ Restore successful - content matches original")
    else:
        print("\n✗ Restore failed - content mismatch")


def example_statistics_monitoring():
    """統計情報の監視例"""
    print("\n" + "=" * 60)
    print("Example 6: Statistics Monitoring")
    print("=" * 60)
    
    manager = get_failsafe_manager()
    
    # 統計情報を取得
    stats = manager.get_statistics()
    
    print("\nFailsafe Manager Statistics:")
    print("\nCheckpoints:")
    print(f"  - Total: {stats['checkpoints']['total']}")
    print(f"  - Active operations: {stats['checkpoints']['active_operations']}")
    
    if stats['checkpoints']['by_state']:
        print("  - By state:")
        for state, count in stats['checkpoints']['by_state'].items():
            print(f"    • {state}: {count}")
    
    print("\nBackups:")
    print(f"  - Total: {stats['backups']['total']}")
    print(f"  - Total size: {stats['backups']['total_size_mb']:.2f} MB")
    
    if stats['backups']['oldest']:
        print(f"  - Oldest: {stats['backups']['oldest']}")
    if stats['backups']['newest']:
        print(f"  - Newest: {stats['backups']['newest']}")
    
    print("\nAuto Backup:")
    print(f"  - Enabled: {stats['auto_backup']['enabled']}")
    print(f"  - Interval: {stats['auto_backup']['interval_seconds']}s")


def main():
    """メイン関数"""
    print("=" * 60)
    print("Failsafe Manager Usage Examples")
    print("=" * 60)
    
    examples = [
        ("Checkpoint Workflow", example_checkpoint_workflow),
        ("Resume After Interruption", example_resume_after_interruption),
        ("Automatic Backup", example_automatic_backup),
        ("Crash Recovery", example_crash_recovery),
        ("Backup Restore", example_backup_restore),
        ("Statistics Monitoring", example_statistics_monitoring),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...")
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
