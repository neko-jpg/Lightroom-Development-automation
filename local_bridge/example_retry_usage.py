"""
リトライマネージャーの使用例

このファイルは、retry_manager.pyの実践的な使用方法を示します。

Requirements: 14.1
"""

import time
import random
from retry_manager import (
    RetryManager,
    RetryConfig,
    RetryStrategy,
    retry,
    retry_operation,
    get_retry_manager
)


# ================================================================================
# 例1: 基本的なリトライ
# ================================================================================

def example_basic_retry():
    """基本的なリトライの例"""
    print("=== 例1: 基本的なリトライ ===\n")
    
    manager = RetryManager()
    
    # 不安定な操作をシミュレート
    attempt_count = 0
    
    def unstable_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"試行 {attempt_count}")
        
        if attempt_count < 3:
            raise ValueError(f"失敗 {attempt_count}")
        
        return "成功!"
    
    try:
        result = manager.retry_with_backoff(
            operation=unstable_operation,
            operation_name="unstable_operation"
        )
        print(f"結果: {result}\n")
    except Exception as e:
        print(f"エラー: {e}\n")


# ================================================================================
# 例2: カスタム設定でのリトライ
# ================================================================================

def example_custom_config():
    """カスタム設定でのリトライの例"""
    print("=== 例2: カスタム設定でのリトライ ===\n")
    
    manager = RetryManager()
    
    # カスタム設定
    config = RetryConfig(
        max_retries=5,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        initial_delay=0.5,
        max_delay=5.0,
        jitter=False
    )
    
    attempt_count = 0
    
    def operation_with_custom_config():
        nonlocal attempt_count
        attempt_count += 1
        print(f"試行 {attempt_count}")
        
        if attempt_count < 4:
            raise ConnectionError(f"接続失敗 {attempt_count}")
        
        return "接続成功!"
    
    try:
        result = manager.retry_with_backoff(
            operation=operation_with_custom_config,
            operation_name="custom_config_operation",
            config=config
        )
        print(f"結果: {result}\n")
    except Exception as e:
        print(f"エラー: {e}\n")


# ================================================================================
# 例3: デコレーターを使用したリトライ
# ================================================================================

def example_decorator():
    """デコレーターを使用したリトライの例"""
    print("=== 例3: デコレーターを使用したリトライ ===\n")
    
    attempt_count = 0
    
    @retry(max_retries=3, initial_delay=0.5, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
    def fetch_data_from_api():
        nonlocal attempt_count
        attempt_count += 1
        print(f"API呼び出し試行 {attempt_count}")
        
        # ランダムに失敗
        if random.random() < 0.6:
            raise ConnectionError("API接続失敗")
        
        return {"status": "success", "data": [1, 2, 3]}
    
    try:
        result = fetch_data_from_api()
        print(f"結果: {result}\n")
    except Exception as e:
        print(f"エラー: {e}\n")


# ================================================================================
# 例4: ファイル読み込みのリトライ
# ================================================================================

def example_file_read_retry():
    """ファイル読み込みのリトライの例"""
    print("=== 例4: ファイル読み込みのリトライ ===\n")
    
    manager = RetryManager()
    
    # ファイルが一時的にロックされている状況をシミュレート
    attempt_count = 0
    
    def read_locked_file():
        nonlocal attempt_count
        attempt_count += 1
        print(f"ファイル読み込み試行 {attempt_count}")
        
        if attempt_count < 3:
            raise PermissionError("ファイルがロックされています")
        
        return "ファイル内容: サンプルデータ"
    
    config = RetryConfig(
        max_retries=5,
        initial_delay=1.0,
        retry_on_exceptions=(PermissionError, IOError)
    )
    
    try:
        result = manager.retry_with_backoff(
            operation=read_locked_file,
            operation_name="read_locked_file",
            config=config
        )
        print(f"結果: {result}\n")
    except Exception as e:
        print(f"エラー: {e}\n")


# ================================================================================
# 例5: AI処理のリトライ（LLMタイムアウト）
# ================================================================================

def example_ai_processing_retry():
    """AI処理のリトライの例"""
    print("=== 例5: AI処理のリトライ（LLMタイムアウト） ===\n")
    
    manager = RetryManager()
    
    attempt_count = 0
    
    def llm_inference():
        nonlocal attempt_count
        attempt_count += 1
        print(f"LLM推論試行 {attempt_count}")
        
        # タイムアウトをシミュレート
        if attempt_count < 2:
            raise TimeoutError("LLM応答タイムアウト")
        
        return {
            "score": 4.5,
            "recommendation": "この写真は良好です"
        }
    
    config = RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        initial_delay=2.0,
        max_delay=10.0,
        retry_on_exceptions=(TimeoutError,)
    )
    
    try:
        result = manager.retry_with_backoff(
            operation=llm_inference,
            operation_name="llm_inference",
            config=config
        )
        print(f"結果: {result}\n")
    except Exception as e:
        print(f"エラー: {e}\n")


# ================================================================================
# 例6: クラウド同期のリトライ
# ================================================================================

def example_cloud_sync_retry():
    """クラウド同期のリトライの例"""
    print("=== 例6: クラウド同期のリトライ ===\n")
    
    attempt_count = 0
    
    @retry(
        max_retries=5,
        initial_delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_on_exceptions=(ConnectionError, TimeoutError)
    )
    def upload_to_cloud(file_path: str):
        nonlocal attempt_count
        attempt_count += 1
        print(f"クラウドアップロード試行 {attempt_count}: {file_path}")
        
        # ネットワークエラーをシミュレート
        if attempt_count < 3:
            raise ConnectionError("ネットワーク接続失敗")
        
        return f"アップロード成功: {file_path}"
    
    try:
        result = upload_to_cloud("/photos/image001.jpg")
        print(f"結果: {result}\n")
    except Exception as e:
        print(f"エラー: {e}\n")


# ================================================================================
# 例7: リトライ統計の取得
# ================================================================================

def example_retry_statistics():
    """リトライ統計の取得の例"""
    print("=== 例7: リトライ統計の取得 ===\n")
    
    manager = get_retry_manager()
    manager.clear_history()  # 履歴をクリア
    
    # 複数の操作を実行
    for i in range(5):
        attempt_count = 0
        
        def operation():
            nonlocal attempt_count
            attempt_count += 1
            
            # ランダムに成功/失敗
            if random.random() < 0.7:
                return f"成功 {i}"
            raise ValueError(f"失敗 {i}")
        
        config = RetryConfig(max_retries=2, initial_delay=0.1)
        
        try:
            manager.retry_with_backoff(
                operation=operation,
                operation_name=f"operation_{i}",
                operation_id=f"op_{i}",
                config=config
            )
        except Exception:
            pass
    
    # 統計を取得
    stats = manager.get_retry_statistics()
    
    print("リトライ統計:")
    print(f"  総操作数: {stats['total_operations']}")
    print(f"  成功操作数: {stats['successful_operations']}")
    print(f"  失敗操作数: {stats['failed_operations']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  平均試行回数: {stats['avg_attempts']:.2f}")
    print(f"  総リトライ回数: {stats['total_retries']}\n")


# ================================================================================
# 例8: リトライ履歴のエクスポート
# ================================================================================

def example_export_retry_log():
    """リトライ履歴のエクスポートの例"""
    print("=== 例8: リトライ履歴のエクスポート ===\n")
    
    manager = get_retry_manager()
    
    # いくつかの操作を実行
    for i in range(3):
        def operation():
            if i == 1:
                raise ValueError("エラー")
            return f"成功 {i}"
        
        config = RetryConfig(max_retries=2, initial_delay=0.1)
        
        try:
            manager.retry_with_backoff(
                operation=operation,
                operation_name=f"export_test_{i}",
                operation_id=f"export_op_{i}",
                config=config
            )
        except Exception:
            pass
    
    # ログをエクスポート
    output_file = "retry_log_export.json"
    manager.export_retry_log(output_file)
    print(f"リトライログを {output_file} にエクスポートしました\n")


# ================================================================================
# 例9: 便利関数retry_operationの使用
# ================================================================================

def example_retry_operation_function():
    """retry_operation便利関数の使用例"""
    print("=== 例9: retry_operation便利関数の使用 ===\n")
    
    attempt_count = 0
    
    def simple_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"簡単な操作試行 {attempt_count}")
        
        if attempt_count < 2:
            raise RuntimeError("一時的なエラー")
        
        return "完了!"
    
    try:
        result = retry_operation(
            operation=simple_operation,
            operation_name="simple_operation",
            max_retries=3,
            initial_delay=0.5
        )
        print(f"結果: {result}\n")
    except Exception as e:
        print(f"エラー: {e}\n")


# ================================================================================
# 例10: 実践的なワークフロー統合
# ================================================================================

def example_practical_workflow():
    """実践的なワークフロー統合の例"""
    print("=== 例10: 実践的なワークフロー統合 ===\n")
    
    manager = RetryManager()
    
    # ステップ1: ファイル読み込み
    @retry(max_retries=3, initial_delay=0.5)
    def read_photo_file(file_path: str):
        print(f"写真ファイル読み込み: {file_path}")
        # 実際の処理をシミュレート
        if random.random() < 0.3:
            raise IOError("ファイル読み込みエラー")
        return f"Photo data from {file_path}"
    
    # ステップ2: AI評価
    @retry(max_retries=3, initial_delay=1.0, retry_on_exceptions=(TimeoutError,))
    def evaluate_photo(photo_data: str):
        print(f"AI評価実行: {photo_data}")
        if random.random() < 0.3:
            raise TimeoutError("AI評価タイムアウト")
        return {"score": 4.2, "quality": "good"}
    
    # ステップ3: 結果保存
    @retry(max_retries=3, initial_delay=0.5)
    def save_result(result: dict):
        print(f"結果保存: {result}")
        if random.random() < 0.2:
            raise IOError("保存エラー")
        return "保存完了"
    
    # ワークフロー実行
    try:
        photo_data = read_photo_file("/photos/IMG_001.jpg")
        evaluation = evaluate_photo(photo_data)
        save_status = save_result(evaluation)
        
        print(f"\nワークフロー完了: {save_status}\n")
    except Exception as e:
        print(f"\nワークフローエラー: {e}\n")


# ================================================================================
# メイン実行
# ================================================================================

def main():
    """すべての例を実行"""
    print("=" * 60)
    print("リトライマネージャー使用例")
    print("=" * 60)
    print()
    
    # 各例を実行
    example_basic_retry()
    time.sleep(0.5)
    
    example_custom_config()
    time.sleep(0.5)
    
    example_decorator()
    time.sleep(0.5)
    
    example_file_read_retry()
    time.sleep(0.5)
    
    example_ai_processing_retry()
    time.sleep(0.5)
    
    example_cloud_sync_retry()
    time.sleep(0.5)
    
    example_retry_statistics()
    time.sleep(0.5)
    
    example_export_retry_log()
    time.sleep(0.5)
    
    example_retry_operation_function()
    time.sleep(0.5)
    
    example_practical_workflow()
    
    print("=" * 60)
    print("すべての例が完了しました")
    print("=" * 60)


if __name__ == '__main__':
    main()
