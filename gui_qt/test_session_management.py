"""
Test script for Session Management Widget
セッション管理ウィジェットのテスト

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import sys
from PyQt6.QtWidgets import QApplication
from widgets.session_widgets import SessionManagementWidget


def main():
    """メインテスト関数"""
    app = QApplication(sys.argv)
    
    # ダークテーマ適用（オプション）
    try:
        with open('resources/styles/dark_theme.qss', 'r') as f:
            app.setStyleSheet(f.read())
    except:
        print("Warning: Could not load dark theme")
    
    # セッション管理ウィジェットを作成
    widget = SessionManagementWidget()
    widget.setWindowTitle("Session Management Test")
    widget.resize(1200, 800)
    widget.show()
    
    print("Session Management Widget Test")
    print("=" * 50)
    print("Testing features:")
    print("- Session list display")
    print("- Session detail view")
    print("- Progress bars and status display")
    print("- Session operations (pause, resume, delete)")
    print("=" * 50)
    print("\nNote: Make sure the API server is running at http://localhost:5100")
    print("      and the database has some test sessions.")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
