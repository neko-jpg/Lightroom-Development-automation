"""
フェイルセーフマネージャーのテスト (Failsafe Manager Tests)
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from failsafe_manager import (
    FailsafeManager,
    ProcessState,
    CheckpointData,
    BackupInfo,
    get_failsafe_manager
)


def test_checkpoint_save_and_load():
    """チェックポイントの保存と読み込みをテスト"""
    print("\n=== Test: Checkpoint Save and Load ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        # チェックポイントを保存
        operation_id = "test_op_001"
        checkpoint_id = manager.save_checkpoint(
            operation_id=operation_id,
            operation_name="Test Operation",
            state=ProcessState.RUNNING,
            progress=0.5,
            data={'current_step': 5, 'total_steps': 10},
            metadata={'user': 'test_user'}
        )
        
        print(f"✓ Checkpoint saved: {checkpoint_id}")
        
        # チェックポイントを読み込み
        loaded_checkpoint = manager.load_checkpoint(checkpoint_id)
        
        assert loaded_checkpoint is not None, "Checkpoint should be loaded"
        assert loaded_checkpoint.operation_id == operation_id
        assert loaded_checkpoint.state == ProcessState.RUNNING
        assert loaded_checkpoint.progress == 0.5
        assert loaded_checkpoint.data['current_step'] == 5
        
        print("✓ Checkpoint loaded successfully")
        print(f"  - Operation: {loaded_checkpoint.operation_name}")
        print(f"  - Progress: {loaded_checkpoint.progress:.1%}")
        print(f"  - State: {loaded_checkpoint.state.value}")


def test_latest_checkpoint():
    """最新チェックポイントの取得をテスト"""
    print("\n=== Test: Latest Checkpoint ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        operation_id = "test_op_002"
        
        # 複数のチェックポイントを保存
        for i in range(3):
            progress = (i + 1) * 0.3
            manager.save_checkpoint(
                operation_id=operation_id,
                operation_name="Multi Checkpoint Test",
                state=ProcessState.RUNNING,
                progress=progress,
                data={'step': i + 1}
            )
            time.sleep(0.1)  # タイムスタンプを異なるものにする
        
        # 最新のチェックポイントを取得
        latest = manager.get_latest_checkpoint(operation_id)
        
        assert latest is not None, "Latest checkpoint should exist"
        assert latest.data['step'] == 3, "Should get the latest checkpoint"
        assert abs(latest.progress - 0.9) < 0.01, f"Progress should be ~0.9, got {latest.progress}"
        
        print("✓ Latest checkpoint retrieved successfully")
        print(f"  - Step: {latest.data['step']}")
        print(f"  - Progress: {latest.progress:.1%}")


def test_resume_operation():
    """処理再開機能をテスト"""
    print("\n=== Test: Resume Operation ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        operation_id = "test_op_003"
        
        # 中断された処理のチェックポイントを保存
        manager.save_checkpoint(
            operation_id=operation_id,
            operation_name="Resumable Operation",
            state=ProcessState.PAUSED,
            progress=0.6,
            data={'processed_items': 60, 'total_items': 100}
        )
        
        # 再開可能かチェック
        can_resume = manager.can_resume(operation_id)
        assert can_resume, "Operation should be resumable"
        
        print("✓ Operation is resumable")
        
        # 再開処理
        def resume_callback(checkpoint: CheckpointData):
            print(f"  - Resuming from {checkpoint.progress:.1%}")
            print(f"  - Processed: {checkpoint.data['processed_items']}/{checkpoint.data['total_items']}")
            return "Resumed successfully"
        
        result = manager.resume_operation(operation_id, resume_callback)
        
        assert result == "Resumed successfully"
        print("✓ Operation resumed successfully")


def test_backup_creation():
    """バックアップ作成をテスト"""
    print("\n=== Test: Backup Creation ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        # テストファイルを作成
        test_file = Path(temp_dir) / 'test_data.txt'
        test_content = "This is test data for backup"
        test_file.write_text(test_content)
        
        # バックアップを作成
        backup_info = manager.create_backup(str(test_file))
        
        assert backup_info is not None, "Backup should be created"
        assert Path(backup_info.backup_path).exists(), "Backup file should exist"
        
        print("✓ Backup created successfully")
        print(f"  - Backup ID: {backup_info.backup_id}")
        print(f"  - Size: {backup_info.size_bytes} bytes")
        print(f"  - Checksum: {backup_info.checksum[:16]}...")


def test_backup_restore():
    """バックアップ復元をテスト"""
    print("\n=== Test: Backup Restore ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        # テストファイルを作成
        test_file = Path(temp_dir) / 'original.txt'
        original_content = "Original content"
        test_file.write_text(original_content)
        
        # バックアップを作成
        backup_info = manager.create_backup(str(test_file))
        
        # 元のファイルを変更
        test_file.write_text("Modified content")
        
        # バックアップを復元
        restored_path = manager.restore_backup(backup_info.backup_id)
        
        # 復元されたファイルの内容を確認
        restored_content = Path(restored_path).read_text()
        assert restored_content == original_content, "Content should be restored"
        
        print("✓ Backup restored successfully")
        print(f"  - Restored to: {restored_path}")
        print(f"  - Content verified: {restored_content}")


def test_auto_backup():
    """自動バックアップをテスト"""
    print("\n=== Test: Auto Backup ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups'),
            auto_backup_interval=2,  # 2秒間隔
            max_backups=3
        )
        
        # テストファイルを作成
        test_file = Path(temp_dir) / 'auto_backup_test.txt'
        test_file.write_text("Auto backup test")
        
        # 自動バックアップを開始
        manager.start_auto_backup([str(test_file)])
        
        print("✓ Auto backup started")
        print("  - Waiting for backups to be created...")
        
        # 少し待機してバックアップが作成されるのを待つ
        time.sleep(5)
        
        # 自動バックアップを停止
        manager.stop_auto_backup()
        
        # バックアップが作成されたか確認
        stats = manager.get_statistics()
        backup_count = stats['backups']['total']
        
        assert backup_count > 0, "At least one backup should be created"
        
        print(f"✓ Auto backup stopped")
        print(f"  - Backups created: {backup_count}")


def test_crash_recovery():
    """クラッシュ復旧をテスト"""
    print("\n=== Test: Crash Recovery ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 最初のマネージャーで実行中の操作を作成
        manager1 = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        # 実行中の操作を保存（クラッシュをシミュレート）
        manager1.save_checkpoint(
            operation_id="crashed_op_001",
            operation_name="Crashed Operation",
            state=ProcessState.RUNNING,
            progress=0.7,
            data={'status': 'interrupted'}
        )
        
        print("✓ Simulated crash with running operation")
        
        # 新しいマネージャーを作成（再起動をシミュレート）
        manager2 = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        # 復旧可能な操作を取得
        recoverable = manager2.get_recoverable_operations()
        
        assert len(recoverable) > 0, "Should find recoverable operations"
        assert recoverable[0]['operation_id'] == "crashed_op_001"
        
        print("✓ Crash recovery detected")
        print(f"  - Recoverable operations: {len(recoverable)}")
        print(f"  - Operation: {recoverable[0]['operation_name']}")
        print(f"  - Progress: {recoverable[0]['progress']:.1%}")


def test_statistics():
    """統計情報の取得をテスト"""
    print("\n=== Test: Statistics ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups')
        )
        
        # いくつかのチェックポイントとバックアップを作成
        for i in range(3):
            manager.save_checkpoint(
                operation_id=f"op_{i}",
                operation_name=f"Operation {i}",
                state=ProcessState.RUNNING if i < 2 else ProcessState.COMPLETED,
                progress=(i + 1) * 0.3,
                data={'index': i}
            )
        
        # テストファイルを作成してバックアップ
        test_file = Path(temp_dir) / 'stats_test.txt'
        test_file.write_text("Statistics test")
        manager.create_backup(str(test_file))
        
        # 統計情報を取得
        stats = manager.get_statistics()
        
        print("✓ Statistics retrieved")
        print(f"  - Total checkpoints: {stats['checkpoints']['total']}")
        print(f"  - Active operations: {stats['checkpoints']['active_operations']}")
        print(f"  - Total backups: {stats['backups']['total']}")
        print(f"  - Total backup size: {stats['backups']['total_size_mb']:.2f} MB")
        print(f"  - Auto backup enabled: {stats['auto_backup']['enabled']}")


def test_cleanup():
    """クリーンアップ機能をテスト"""
    print("\n=== Test: Cleanup ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = FailsafeManager(
            checkpoint_dir=os.path.join(temp_dir, 'checkpoints'),
            backup_dir=os.path.join(temp_dir, 'backups'),
            max_checkpoints=3,
            max_backups=2
        )
        
        operation_id = "cleanup_test"
        
        # 最大数を超えるチェックポイントを作成
        for i in range(5):
            manager.save_checkpoint(
                operation_id=operation_id,
                operation_name="Cleanup Test",
                state=ProcessState.RUNNING,
                progress=(i + 1) * 0.2,
                data={'step': i}
            )
            time.sleep(0.1)
        
        # チェックポイント数を確認
        checkpoints = manager._load_operation_checkpoints(operation_id)
        assert len(checkpoints) <= manager.max_checkpoints, "Old checkpoints should be cleaned up"
        
        print(f"✓ Checkpoint cleanup working")
        print(f"  - Checkpoints kept: {len(checkpoints)}/{manager.max_checkpoints}")
        
        # 最大数を超えるバックアップを作成
        test_file = Path(temp_dir) / 'cleanup_backup.txt'
        test_file.write_text("Cleanup test")
        
        for i in range(4):
            manager.create_backup(str(test_file))
            time.sleep(0.1)
        
        # バックアップ数を確認
        assert len(manager.backups) <= manager.max_backups, "Old backups should be cleaned up"
        
        print(f"✓ Backup cleanup working")
        print(f"  - Backups kept: {len(manager.backups)}/{manager.max_backups}")


def run_all_tests():
    """すべてのテストを実行"""
    print("=" * 60)
    print("Failsafe Manager Tests")
    print("=" * 60)
    
    tests = [
        test_checkpoint_save_and_load,
        test_latest_checkpoint,
        test_resume_operation,
        test_backup_creation,
        test_backup_restore,
        test_auto_backup,
        test_crash_recovery,
        test_statistics,
        test_cleanup
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
