"""
Test script for Approval Queue Widget
承認キュー画面のテスト

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1
"""

import sys
from PyQt6.QtWidgets import QApplication
from widgets.approval_widgets import ApprovalQueueWidget


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # ダークテーマ設定
    app.setStyle('Fusion')
    
    # 承認キューウィジェットを作成
    window = ApprovalQueueWidget()
    window.setWindowTitle("Approval Queue Test")
    window.resize(1400, 900)
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
