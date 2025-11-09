"""
リトライマネージャーとエラーハンドラーの統合例

このファイルは、retry_manager.pyとerror_handler.pyを
統合して使用する実践的な例を示します。

Requirements: 14.1
"""

import random
import time
from error_handler import (
    FileReadError,
    LLMTimeoutError,
    CloudSyncError,
    GPUOutOfMemoryError,
    handle_error,
    get_error_handler
)
from retry_manager import (
    retry,
    RetryStrategy,
    get_retry_manager
)


# ================================================================================
# 例1: ファイル読み込みのリトライとエラー処理
# ================================================================================

def example_file_read_with_retry():
    """ファイル読み込みのリトライとエラー処理の例"""
    print("=== 例1: ファイル読み込みのリトライとエラー処理 ===\n")
    
    attempt_count = 0
    
    @retry(
        max_retries=3,
        initial_delay=0.5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_on_exceptions=(IOError, PermissionError)
    )
    def read_photo_file(file_path: str):
        nonlocal attempt_count
        attempt_count += 1
        print(f"ファイル読み込み試行 {attempt_count}: {file_path}")
        
        try:
            # ファイル読み込みをシミュレート
            if attempt_count < 3:
                raise IOError("ファイルがロックされています")
            
            return f"Photo data from {file_path}"
            
        except IOError as e:
            # エラーハンドラーで記録
            error = FileReadError(file_path, str(e))
            handle_error(error)
            raise
    
    try:
        result = read_photo_file("/photos/IMG_001.jpg")
        print(f"成功: {result}\n")
    except Exception as e:
        print(f"最終的に失敗: {e}\n")


# ================================================================================
# 例2: AI処理のリトライとエラー処理
# ================================================================================

def example_ai_processing_with_retry():
    """AI処理のリトライとエラー処理の例"""
    print("=== 例2: AI処理のリトライとエラー処理 ===\n")
    
    attempt_count = 0
    
    @retry(
        max_retries=3,
        initial_delay=2.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_on_exceptions=(TimeoutError,)
    )
    def llm_inference(prompt: str):
        nonlocal attempt_count
        attempt_count += 1
        print(f"LLM推論試行 {attempt_count}")
        
        try:
            # LLM推論をシミュレート
            if attempt_count < 2:
                raise TimeoutError("LLM応答タイムアウト")
            
            return {
                "score": 4.5,
                "recommendation": "この写真は良好です"
            }
            
        except TimeoutError as e:
            # エラーハンドラーで記録
            error = LLMTimeoutError("llama3.1:8b", 30)
            handle_error(error)
            raise
    
    try:
        result = llm_inference("Evaluate this photo")
        print(f"成功: {result}\n")
    except Exception as e:
        print(f"最終的に失敗: {e}\n")


# ================================================================================
# 例3: クラウド同期のリトライとエラー処理
# ================================================================================

def example_cloud_sync_with_retry():
    """クラウド同期のリトライとエラー処理の例"""
    print("=== 例3: クラウド同期のリトライとエラー処理 ===\n")
    
    attempt_count = 0
    
    @retry(
        max_retries=5,
        initial_delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_on_exceptions=(ConnectionError, TimeoutError)
    )
    def upload_to_cloud(file_path: str, provider: str):
        nonlocal attempt_count
        attempt_count += 1
        print(f"クラウドアップロード試行 {attempt_count}: {file_path} → {provider}")
        
        try:
            # アップロードをシミュレート
            if attempt_count < 3:
                raise ConnectionError("ネットワーク接続失敗")
            
            return f"アップロード成功: {file_path}"
            
        except ConnectionError as e:
            # エラーハンドラーで記録
            error = CloudSyncError(provider, file_path, str(e))
            handle_error(error)
            raise
    
    try:
        result = upload_to_cloud("/photos/IMG_001.jpg", "Dropbox")
        print(f"成功: {result}\n")
    except Exception as e:
        print(f"最終的に失敗: {e}\n")


# ================================================================================
# 例4: GPU OOMのリトライとエラー処理
# ================================================================================

def example_gpu_oom_with_retry():
    """GPU OOMのリトライとエラー処理の例"""
    print("=== 例4: GPU OOMのリトライとエラー処理 ===\n")
    
    attempt_count = 0
    use_quantization = False
    
    @retry(
        max_retries=2,
        initial_delay=5.0,
        strategy=RetryStrategy.FIXED_DELAY,
        retry_on_exceptions=(MemoryError,)
    )
    def load_and_run_model(model_name: str):
        nonlocal attempt_count, use_quantization
        attempt_count += 1
        print(f"モデル実行試行 {attempt_count}: {model_name}")
        
        try:
            # GPU OOMをシミュレート
            if attempt_count == 1:
                raise MemoryError("GPU out of memory")
            
            # 2回目は量子化モデルに切り替え
            if attempt_count == 2:
                use_quantization = True
                print("  → 量子化モデルに切り替え")
            
            return {
                "model": model_name,
                "quantized": use_quantization,
                "result": "success"
            }
            
        except MemoryError as e:
            # エラーハンドラーで記録
            error = GPUOutOfMemoryError(8000, 6000)
            handle_error(error)
            
            # 量子化モデルに切り替えるフラグを設定
            use_quantization = True
            raise
    
    try:
        result = load_and_run_model("llama3.1:8b")
        print(f"成功: {result}\n")
    except Exception as e:
        print(f"最終的に失敗: {e}\n")


# ================================================================================
# 例5: 統合ワークフロー
# ================================================================================

def example_integrated_workflow():
    """統合ワークフローの例"""
    print("=== 例5: 統合ワークフロー ===\n")
    
    # ステップ1: ファイル読み込み
    @retry(max_retries=3, initial_delay=0.5)
    def read_file(file_path: str):
        print(f"  ステップ1: ファイル読み込み - {file_path}")
        if random.random() < 0.3:
            error = FileReadError(file_path, "Read error")
            handle_error(error)
            raise IOError("Read error")
        return f"Data from {file_path}"
    
    # ステップ2: AI評価
    @retry(max_retries=3, initial_delay=1.0)
    def evaluate(data: str):
        print(f"  ステップ2: AI評価")
        if random.random() < 0.3:
            error = LLMTimeoutError("llama3.1:8b", 30)
            handle_error(error)
            raise TimeoutError("Evaluation timeout")
        return {"score": 4.5, "data": data}
    
    # ステップ3: 結果保存
    @retry(max_retries=3, initial_delay=0.5)
    def save_result(result: dict):
        print(f"  ステップ3: 結果保存")
        if random.random() < 0.2:
            raise IOError("Save error")
        return "Saved"
    
    try:
        print("ワークフロー開始\n")
        
        data = read_file("/photos/IMG_001.jpg")
        evaluation = evaluate(data)
        save_status = save_result(evaluation)
        
        print(f"\nワークフロー完了: {save_status}\n")
        
    except Exception as e:
        print(f"\nワークフローエラー: {e}\n")


# ================================================================================
# 例6: エラー統計とリトライ統計の統合
# ================================================================================

def example_combined_statistics():
    """エラー統計とリトライ統計の統合例"""
    print("=== 例6: エラー統計とリトライ統計の統合 ===\n")
    
    error_handler = get_error_handler()
    retry_manager = get_retry_manager()
    
    # 履歴をクリア
    error_handler.clear_history()
    retry_manager.clear_history()
    
    # 複数の操作を実行
    for i in range(5):
        attempt_count = 0
        
        @retry(max_retries=2, initial_delay=0.1)
        def operation():
            nonlocal attempt_count
            attempt_count += 1
            
            # ランダムに成功/失敗
            if random.random() < 0.6:
                error = FileReadError(f"/file_{i}.jpg", "Random error")
                handle_error(error)
                raise IOError("Random error")
            
            return f"Success {i}"
        
        try:
            operation()
        except Exception:
            pass
    
    # エラー統計を取得
    error_stats = error_handler.get_error_statistics()
    print("エラー統計:")
    print(f"  総エラー数: {error_stats['total_errors']}")
    print(f"  カテゴリ別: {error_stats['by_category']}")
    print(f"  重要度別: {error_stats['by_severity']}")
    print()
    
    # リトライ統計を取得
    retry_stats = retry_manager.get_retry_statistics()
    print("リトライ統計:")
    print(f"  総操作数: {retry_stats['total_operations']}")
    print(f"  成功操作数: {retry_stats['successful_operations']}")
    print(f"  失敗操作数: {retry_stats['failed_operations']}")
    print(f"  成功率: {retry_stats['success_rate']:.2%}")
    print(f"  平均試行回数: {retry_stats['avg_attempts']:.2f}")
    print(f"  総リトライ回数: {retry_stats['total_retries']}")
    print()


# ================================================================================
# 例7: エラー回復戦略に基づく自動リトライ
# ================================================================================

def example_auto_retry_based_on_error():
    """エラー回復戦略に基づく自動リトライの例"""
    print("=== 例7: エラー回復戦略に基づく自動リトライ ===\n")
    
    from error_handler import JunmaiError, ErrorRecoveryStrategy
    
    def process_with_auto_retry(operation, operation_name: str):
        """エラーの回復戦略に基づいて自動的にリトライ"""
        try:
            return operation()
        except JunmaiError as e:
            # エラーを記録
            context = handle_error(e)
            
            # リトライ可能かチェック
            if e.should_retry():
                print(f"  エラー検知: {e.error_code}")
                print(f"  回復戦略: {e.recovery_strategy.value}")
                
                # エラーに適したリトライ設定を取得
                retry_config = e.get_retry_config()
                
                if retry_config:
                    print(f"  自動リトライを実行...")
                    retry_manager = get_retry_manager()
                    return retry_manager.retry_with_backoff(
                        operation=operation,
                        operation_name=operation_name,
                        config=retry_config
                    )
            
            # リトライ不可の場合は再スロー
            raise
    
    # テスト操作
    attempt_count = 0
    
    def unstable_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"  操作試行 {attempt_count}")
        
        if attempt_count < 3:
            raise FileReadError("/test.jpg", "Temporary error")
        
        return "Success!"
    
    try:
        result = process_with_auto_retry(unstable_operation, "unstable_operation")
        print(f"  結果: {result}\n")
    except Exception as e:
        print(f"  最終的に失敗: {e}\n")


# ================================================================================
# メイン実行
# ================================================================================

def main():
    """すべての例を実行"""
    print("=" * 60)
    print("リトライマネージャーとエラーハンドラーの統合例")
    print("=" * 60)
    print()
    
    # 各例を実行
    example_file_read_with_retry()
    time.sleep(0.5)
    
    example_ai_processing_with_retry()
    time.sleep(0.5)
    
    example_cloud_sync_with_retry()
    time.sleep(0.5)
    
    example_gpu_oom_with_retry()
    time.sleep(0.5)
    
    example_integrated_workflow()
    time.sleep(0.5)
    
    example_combined_statistics()
    time.sleep(0.5)
    
    example_auto_retry_based_on_error()
    
    print("=" * 60)
    print("すべての例が完了しました")
    print("=" * 60)


if __name__ == '__main__':
    main()
