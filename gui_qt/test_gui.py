"""
Junmai AutoDev - GUI Test Script
GUI の動作確認用スクリプト
"""

import sys
import os

def test_imports():
    """必要なモジュールのインポートテスト"""
    print("Testing imports...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6.QtWidgets imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt6.QtWidgets: {e}")
        return False
    
    try:
        from PyQt6.QtCore import Qt, QTimer
        print("✓ PyQt6.QtCore imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt6.QtCore: {e}")
        return False
    
    try:
        from PyQt6.QtGui import QIcon, QFont
        print("✓ PyQt6.QtGui imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt6.QtGui: {e}")
        return False
    
    return True


def test_files():
    """必要なファイルの存在確認"""
    print("\nTesting file structure...")
    
    base_dir = os.path.dirname(__file__)
    required_files = [
        "main.py",
        "main_window.py",
        "__init__.py",
        "resources/styles/dark_theme.qss",
        "resources/styles/light_theme.qss",
        "resources/README.md",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} not found")
            all_exist = False
    
    return all_exist


def test_stylesheet_loading():
    """スタイルシートの読み込みテスト"""
    print("\nTesting stylesheet loading...")
    
    base_dir = os.path.dirname(__file__)
    themes = ["dark", "light"]
    
    all_loaded = True
    for theme in themes:
        stylesheet_path = os.path.join(
            base_dir,
            "resources",
            "styles",
            f"{theme}_theme.qss"
        )
        
        try:
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                content = f.read()
                if len(content) > 0:
                    print(f"✓ {theme}_theme.qss loaded ({len(content)} bytes)")
                else:
                    print(f"✗ {theme}_theme.qss is empty")
                    all_loaded = False
        except Exception as e:
            print(f"✗ Failed to load {theme}_theme.qss: {e}")
            all_loaded = False
    
    return all_loaded


def main():
    """テストメイン関数"""
    print("=" * 60)
    print("Junmai AutoDev - GUI Test Suite")
    print("=" * 60)
    
    results = []
    
    # インポートテスト
    results.append(("Import Test", test_imports()))
    
    # ファイル構造テスト
    results.append(("File Structure Test", test_files()))
    
    # スタイルシート読み込みテスト
    results.append(("Stylesheet Loading Test", test_stylesheet_loading()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! You can run the GUI with: python main.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
