"""
Junmai AutoDev - Desktop GUI Application Entry Point
アプリケーションエントリーポイント

Requirements: 8.1 - デスクトップGUI実装
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from main_window import MainWindow


def load_stylesheet(theme="dark"):
    """
    スタイルシートを読み込む
    
    Args:
        theme: "dark" または "light"
    
    Returns:
        str: スタイルシート文字列
    """
    stylesheet_path = os.path.join(
        os.path.dirname(__file__),
        "resources",
        "styles",
        f"{theme}_theme.qss"
    )
    
    try:
        with open(stylesheet_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Stylesheet not found: {stylesheet_path}")
        return ""


def main():
    """
    アプリケーションのメインエントリーポイント
    """
    # アプリケーション作成
    app = QApplication(sys.argv)
    
    # アプリケーション情報設定
    app.setApplicationName("Junmai AutoDev")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Junmai AutoDev")
    
    # High DPI対応
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # スタイルシート適用（デフォルト: ダークテーマ）
    stylesheet = load_stylesheet("dark")
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # アイコン設定（存在する場合）
    icon_path = os.path.join(
        os.path.dirname(__file__),
        "resources",
        "icons",
        "app_icon.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # メインウィンドウ作成・表示
    window = MainWindow()
    window.show()
    
    # イベントループ開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
