"""
フェイルセーフ統合例 (Failsafe Integration Example)

このスクリプトは、フェイルセーフマネージャーをエラーハンドラーと
リトライマネージャーと統合して使用する方法を示します。
"""

import os
import sys
import time
import random

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from failsafe_manager import get_failsafe_manager, ProcessState
from error_handler import get_error_handler, FileReadError, AIProcessingError
from retry_manager import get_retry_manager, RetryConfig, RetryStrategy


def example_integrated_photo_processing():
    """
    フェイルセーフ、エラーハンドリング、リトライを統合した
    写真処理の例
    """
    print("\n" + "=" * 60)
    print("Integrated Photo Processing Example")
    print("=" * 60)
    
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    operation_id = "integrated_batch_001"
    operation_name = "Integrated Photo Processing"
    total_photos = 20
    
    # バックアップを作成
    print("\n1. Creating backup...")
    try:
        # テストファイルを作成
        from pathlib import Path
        test_db = Path('data/test_processing.db')
        test_db.parent.mkdir(parents=True, exist_ok=True)
        test_db.write_text("Test database")
        
        backup_info = failsafe.create_backup(str(test_db))
        print(f"   ✓ Backup created: {backup_info.backup_id}")
    except Exception as e:
        print(f"   ✗ Backup failed: {e}")
    
    # 処理を開始
    print(f"\n2. Starting {operation_name}...")
    print(f"   Total photos: {total_photos}")
    
    # 初期チェックポイント
    failsafe.save_checkpoint(
        operation_id=operation_id,
        operation_name=operation_name,
        state=ProcessState.INITIALIZED,
        progress=0.0,
        data={'processed': 0, 'total': total_photos, 'errors': 0}
    )
    
    processed = 0
    errors = 0
    
    for i in range(total_photos):
        photo_id = f"photo_{i:03d}"
        
        # リトライ付きで写真を処理
        def process_photo():
            # ランダムにエラーを発生させる（デモ用）
            if random.random() < 0.1:  # 10%の確率でエラー
                raise FileReadError(f"photos/{photo_id}.jpg", "Simulated error")
            
            # 処理をシミュレート
            time.sleep(0.1)
            return f"Processed {photo_id}"
        
        try:
            # リトライ設定
            retry_config = RetryConfig(
                max_retries=2,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                initial_delay=0.5
            )
            
            # リトライ付きで実行
            result = retry_manager.retry_with_backoff(
                operation=process_photo,
                operation_name=f"process_{photo_id}",
                operation_id=f"{operation_id}_{photo_id}",
                config=retry_config
            )
            
            processed += 1
            print(f"   ✓ {photo_id}: {result}")
            
        except Exception as e:
            # エラーを記録
            error_context = error_handler.handle_error(
                e,
                context={'photo_id': photo_id, 'operation_id': operation_id}
            )
            
            errors += 1
            print(f"   ✗ {photo_id}: {error_context.message}")
        
        # 5枚ごとにチェックポイントを保存
        if (i + 1) % 5 == 0:
            progress = (i + 1) / total_photos
            failsafe.save_checkpoint(
                operation_id=operation_id,
                operation_name=operation_name,
                state=ProcessState.RUNNING,
                progress=progress,
                data={
                    'processed': processed,
                    'total': total_photos,
                    'errors': errors,
                    'current_index': i + 1
                }
            )
            print(f"\n   📍 Checkpoint: {progress:.0%} complete ({processed}/{total_photos} processed, {errors} errors)\n")
    
    # 完了チェックポイント
    failsafe.save_checkpoint(
        operation_id=operation_id,
        operation_name=operation_name,
        state=ProcessState.COMPLETED,
        progress=1.0,
        data={
            'processed': processed,
            'total': total_photos,
            'errors': errors,
            'status': 'completed'
        }
    )
    
    print(f"\n3. Processing completed!")
    print(f"   - Processed: {processed}/{total_photos}")
    print(f"   - Errors: {errors}")
    print(f"   - Success rate: {(processed/total_photos)*100:.1f}%")


def example_resume_with_error_recovery():
    """
    エラー復旧を含む処理再開の例
    """
    print("\n" + "=" * 60)
    print("Resume with Error Recovery Example")
    print("=" * 60)
    
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    
    operation_id = "resume_with_errors_001"
    operation_name = "Resumable Processing"
    
    # 中断された処理をシミュレート
    print("\n1. Simulating interrupted process...")
    failsafe.save_checkpoint(
        operation_id=operation_id,
        operation_name=operation_name,
        state=ProcessState.PAUSED,
        progress=0.4,
        data={
            'processed': 40,
            'total': 100,
            'last_error': None
        }
    )
    print("   ✓ Process interrupted at 40%")
    
    # 再開処理
    print("\n2. Attempting to resume...")
    
    if failsafe.can_resume(operation_id):
        def resume_with_error_handling(checkpoint):
            print(f"   Resuming from {checkpoint.progress:.0%}")
            
            start_from = checkpoint.data['processed']
            total = checkpoint.data['total']
            
            try:
                # 残りの処理を実行
                for i in range(start_from, total):
                    # ランダムにエラーを発生させる
                    if random.random() < 0.05:  # 5%の確率
                        raise AIProcessingError(
                            f"AI processing failed at item {i}",
                            model_name="test_model"
                        )
                    
                    time.sleep(0.05)
                    
                    if (i + 1) % 20 == 0:
                        print(f"   Progress: {(i+1)/total:.0%}")
                
                return "Completed successfully"
                
            except Exception as e:
                # エラーを記録
                error_context = error_handler.handle_error(e)
                
                # 失敗状態を保存
                failsafe.save_checkpoint(
                    operation_id=operation_id,
                    operation_name=operation_name,
                    state=ProcessState.FAILED,
                    progress=i / total,
                    data={
                        'processed': i,
                        'total': total,
                        'last_error': error_context.message
                    }
                )
                
                raise
        
        try:
            result = failsafe.resume_operation(
                operation_id,
                resume_with_error_handling
            )
            print(f"\n   ✓ {result}")
            
        except Exception as e:
            print(f"\n   ✗ Resume failed: {e}")
            print("   State saved for future recovery")


def example_statistics_and_monitoring():
    """
    統合システムの統計とモニタリングの例
    """
    print("\n" + "=" * 60)
    print("Integrated Statistics and Monitoring")
    print("=" * 60)
    
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    # フェイルセーフ統計
    print("\n1. Failsafe Statistics:")
    failsafe_stats = failsafe.get_statistics()
    print(f"   - Checkpoints: {failsafe_stats['checkpoints']['total']}")
    print(f"   - Active operations: {failsafe_stats['checkpoints']['active_operations']}")
    print(f"   - Backups: {failsafe_stats['backups']['total']}")
    print(f"   - Backup size: {failsafe_stats['backups']['total_size_mb']:.2f} MB")
    
    # エラー統計
    print("\n2. Error Statistics:")
    error_stats = error_handler.get_error_statistics()
    print(f"   - Total errors: {error_stats['total_errors']}")
    if error_stats['by_category']:
        print("   - By category:")
        for category, count in error_stats['by_category'].items():
            print(f"     • {category}: {count}")
    
    # リトライ統計
    print("\n3. Retry Statistics:")
    retry_stats = retry_manager.get_retry_statistics()
    print(f"   - Total operations: {retry_stats['total_operations']}")
    print(f"   - Successful: {retry_stats['successful_operations']}")
    print(f"   - Failed: {retry_stats['failed_operations']}")
    print(f"   - Success rate: {retry_stats['success_rate']*100:.1f}%")
    print(f"   - Average attempts: {retry_stats['avg_attempts']:.2f}")
    print(f"   - Total retries: {retry_stats['total_retries']}")


def example_complete_workflow():
    """
    完全な統合ワークフローの例
    """
    print("\n" + "=" * 60)
    print("Complete Integrated Workflow")
    print("=" * 60)
    
    failsafe = get_failsafe_manager()
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    operation_id = "complete_workflow_001"
    
    print("\n1. Checking for recovery...")
    # クラッシュ復旧をチェック
    recoverable = failsafe.get_recoverable_operations()
    if recoverable:
        print(f"   Found {len(recoverable)} operations to recover")
        for op in recoverable:
            if op['operation_id'] == operation_id:
                print(f"   ✓ Found matching operation at {op['progress']:.0%}")
                # 実際のアプリケーションではここで復旧処理を実行
    else:
        print("   ✓ No recovery needed")
    
    print("\n2. Creating backup...")
    # バックアップを作成
    from pathlib import Path
    workflow_file = Path('data/workflow_test.txt')
    workflow_file.parent.mkdir(parents=True, exist_ok=True)
    workflow_file.write_text("Workflow data")
    
    backup_info = failsafe.create_backup(str(workflow_file))
    print(f"   ✓ Backup created: {backup_info.backup_id}")
    
    print("\n3. Processing with full protection...")
    # 完全保護付きで処理
    total_items = 10
    
    for i in range(total_items):
        def protected_operation():
            # ランダムにエラーを発生
            if random.random() < 0.15:
                raise Exception(f"Random error at item {i}")
            
            time.sleep(0.1)
            return f"Item {i} processed"
        
        try:
            # リトライ付きで実行
            result = retry_manager.retry_with_backoff(
                operation=protected_operation,
                operation_name=f"workflow_item_{i}",
                config=RetryConfig(max_retries=2, initial_delay=0.3)
            )
            
            print(f"   ✓ {result}")
            
        except Exception as e:
            # エラーを記録
            error_handler.handle_error(e, context={'item': i})
            print(f"   ✗ Item {i} failed after retries")
        
        # チェックポイントを保存
        if (i + 1) % 3 == 0:
            failsafe.save_checkpoint(
                operation_id=operation_id,
                operation_name="Complete Workflow",
                state=ProcessState.RUNNING,
                progress=(i + 1) / total_items,
                data={'current_item': i + 1}
            )
    
    # 完了
    failsafe.save_checkpoint(
        operation_id=operation_id,
        operation_name="Complete Workflow",
        state=ProcessState.COMPLETED,
        progress=1.0,
        data={'status': 'completed'}
    )
    
    print("\n4. Workflow completed!")
    print("   All systems working together:")
    print("   - Failsafe: Checkpoints and backups ✓")
    print("   - Error handling: Errors logged ✓")
    print("   - Retry: Failed operations retried ✓")


def main():
    """メイン関数"""
    print("=" * 60)
    print("Failsafe Integration Examples")
    print("=" * 60)
    
    examples = [
        ("Integrated Photo Processing", example_integrated_photo_processing),
        ("Resume with Error Recovery", example_resume_with_error_recovery),
        ("Statistics and Monitoring", example_statistics_and_monitoring),
        ("Complete Workflow", example_complete_workflow),
    ]
    
    print("\nRunning integrated examples...")
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("All integrated examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
