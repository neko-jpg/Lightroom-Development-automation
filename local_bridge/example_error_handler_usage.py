"""
エラーハンドラーの使用例

このスクリプトは、エラー分類システムの使用方法を示します。

Requirements: 14.1, 14.2
"""

import time
from error_handler import (
    # エラークラス
    FileReadError,
    FileWriteError,
    DiskSpaceError,
    LLMTimeoutError,
    GPUOutOfMemoryError,
    CatalogLockError,
    ExportFailedError,
    CloudSyncError,
    CPUOverloadError,
    GPUOverheatError,
    
    # エラーハンドラー
    ErrorHandler,
    get_error_handler,
    handle_error,
    
    # エラータイプ
    ErrorSeverity,
    ErrorRecoveryStrategy
)


def example_1_basic_error_handling():
    """例1: 基本的なエラーハンドリング"""
    print("=" * 60)
    print("例1: 基本的なエラーハンドリング")
    print("=" * 60)
    
    handler = ErrorHandler(log_file='logs/example_errors.log')
    
    try:
        # ファイル読み込みエラーをシミュレート
        raise FileReadError("/path/to/missing_file.jpg", "File not found")
    except Exception as e:
        context = handler.handle_error(e)
        print(f"エラーコード: {context.error_code}")
        print(f"カテゴリ: {context.category.value}")
        print(f"重要度: {context.severity.value}")
        print(f"回復戦略: {context.recovery_strategy.value}")
        print(f"メッセージ: {context.message}")
        print()


def example_2_multiple_error_types():
    """例2: 複数のエラータイプの処理"""
    print("=" * 60)
    print("例2: 複数のエラータイプの処理")
    print("=" * 60)
    
    handler = ErrorHandler(log_file='logs/example_errors.log')
    
    # 様々なエラーを処理
    errors = [
        FileReadError("/photo1.jpg", "Permission denied"),
        LLMTimeoutError("llama3.1:8b", 30),
        GPUOutOfMemoryError(8000, 6000),
        CatalogLockError("/catalog.lrcat", 300),
        ExportFailedError("photo_123", "JPEG", "Codec error"),
    ]
    
    for error in errors:
        context = handler.handle_error(error)
        print(f"処理: {context.error_code} - {context.message}")
    
    print()
    print("エラー統計:")
    stats = handler.get_error_statistics()
    print(f"  総エラー数: {stats['total_errors']}")
    print(f"  カテゴリ別: {stats['by_category']}")
    print(f"  コード別: {stats['by_code']}")
    print()


def example_3_error_recovery_strategies():
    """例3: エラー回復戦略の実装"""
    print("=" * 60)
    print("例3: エラー回復戦略の実装")
    print("=" * 60)
    
    handler = ErrorHandler(log_file='logs/example_errors.log')
    
    def process_with_retry(file_path: str, max_retries: int = 3):
        """リトライ付きファイル処理"""
        for attempt in range(max_retries):
            try:
                # ファイル処理をシミュレート
                if attempt < 2:  # 最初の2回は失敗
                    raise FileReadError(file_path, f"Attempt {attempt + 1} failed")
                
                print(f"✓ ファイル処理成功: {file_path} (試行 {attempt + 1})")
                return True
                
            except FileReadError as e:
                context = handler.handle_error(e)
                
                if context.recovery_strategy == ErrorRecoveryStrategy.RETRY_WITH_BACKOFF:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数バックオフ
                        print(f"  リトライ待機: {wait_time}秒...")
                        time.sleep(wait_time)
                    else:
                        print(f"✗ 最大リトライ回数に達しました: {file_path}")
                        return False
    
    # テスト実行
    process_with_retry("/test/photo.jpg")
    print()


def example_4_resource_monitoring():
    """例4: リソース監視とエラー処理"""
    print("=" * 60)
    print("例4: リソース監視とエラー処理")
    print("=" * 60)
    
    handler = ErrorHandler(log_file='logs/example_errors.log')
    
    def check_system_resources():
        """システムリソースをチェック"""
        # CPU使用率をシミュレート
        cpu_usage = 95.5
        cpu_threshold = 80.0
        
        if cpu_usage > cpu_threshold:
            error = CPUOverloadError(cpu_usage, cpu_threshold)
            context = handler.handle_error(error)
            print(f"⚠ CPU過負荷検知: {context.message}")
            print(f"  回復戦略: {context.recovery_strategy.value}")
            print("  → 処理速度を50%に制限")
        
        # GPU温度をシミュレート
        gpu_temp = 82.0
        gpu_threshold = 75.0
        
        if gpu_temp > gpu_threshold:
            error = GPUOverheatError(gpu_temp, gpu_threshold)
            context = handler.handle_error(error)
            print(f"⚠ GPU過熱検知: {context.message}")
            print(f"  回復戦略: {context.recovery_strategy.value}")
            print("  → 処理を一時停止")
        
        # ディスク容量をシミュレート
        required_mb = 1000
        available_mb = 500
        
        if available_mb < required_mb:
            error = DiskSpaceError(required_mb, available_mb)
            context = handler.handle_error(error)
            print(f"🛑 ディスク容量不足: {context.message}")
            print(f"  重要度: {context.severity.value}")
            print(f"  回復戦略: {context.recovery_strategy.value}")
            print("  → システム停止が必要")
    
    check_system_resources()
    print()


def example_5_error_statistics_and_export():
    """例5: エラー統計とエクスポート"""
    print("=" * 60)
    print("例5: エラー統計とエクスポート")
    print("=" * 60)
    
    handler = ErrorHandler(log_file='logs/example_errors.log')
    
    # 複数のエラーを生成
    print("エラーを生成中...")
    for i in range(5):
        handler.handle_error(FileReadError(f"/photo{i}.jpg"))
    
    for i in range(3):
        handler.handle_error(LLMTimeoutError("llama3.1", 30))
    
    handler.handle_error(GPUOverheatError(80.0, 75.0))
    handler.handle_error(CloudSyncError("Dropbox", "/photo.jpg"))
    
    # 統計を表示
    print("\n📊 エラー統計:")
    stats = handler.get_error_statistics()
    
    print(f"\n総エラー数: {stats['total_errors']}")
    
    print("\nカテゴリ別:")
    for category, count in stats['by_category'].items():
        print(f"  {category}: {count}")
    
    print("\n重要度別:")
    for severity, count in stats['by_severity'].items():
        print(f"  {severity}: {count}")
    
    print("\nエラーコード別:")
    for code, count in stats['by_code'].items():
        print(f"  {code}: {count}")
    
    # エラーログをエクスポート
    export_file = 'logs/error_export.json'
    handler.export_error_log(export_file)
    print(f"\n✓ エラーログをエクスポート: {export_file}")
    print()


def example_6_global_error_handler():
    """例6: グローバルエラーハンドラーの使用"""
    print("=" * 60)
    print("例6: グローバルエラーハンドラーの使用")
    print("=" * 60)
    
    # グローバルハンドラーを使用
    try:
        raise FileWriteError("/output/photo.jpg", "Disk full")
    except Exception as e:
        context = handle_error(e, {'user_id': 'user123', 'session_id': 'session456'})
        print(f"エラー処理完了: {context.error_code}")
        print(f"追加コンテキスト: {context.details}")
    
    # 統計を確認
    handler = get_error_handler()
    stats = handler.get_error_statistics()
    print(f"\nグローバルハンドラーの総エラー数: {stats['total_errors']}")
    print()


def example_7_custom_error_context():
    """例7: カスタムエラーコンテキストの追加"""
    print("=" * 60)
    print("例7: カスタムエラーコンテキストの追加")
    print("=" * 60)
    
    handler = ErrorHandler(log_file='logs/example_errors.log')
    
    # カスタムコンテキストを含むエラー処理
    try:
        raise ExportFailedError("photo_789", "TIFF", "Compression error")
    except Exception as e:
        context = handler.handle_error(e, {
            'user_id': 'photographer_001',
            'session_name': '2025-11-08_Wedding',
            'photo_count': 120,
            'export_preset': 'Print_4096',
            'timestamp': '2025-11-08T14:30:00'
        })
        
        print(f"エラー: {context.message}")
        print(f"\nカスタムコンテキスト:")
        for key, value in context.details.items():
            print(f"  {key}: {value}")
    
    print()


def main():
    """メイン実行関数"""
    print("\n" + "=" * 60)
    print("エラーハンドラー使用例")
    print("=" * 60 + "\n")
    
    # 各例を実行
    example_1_basic_error_handling()
    example_2_multiple_error_types()
    example_3_error_recovery_strategies()
    example_4_resource_monitoring()
    example_5_error_statistics_and_export()
    example_6_global_error_handler()
    example_7_custom_error_context()
    
    print("=" * 60)
    print("すべての例が完了しました")
    print("=" * 60)


if __name__ == '__main__':
    main()
