"""
Test script for Statistics Widget
統計・レポート画面のテスト

Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
"""

import sys
from PyQt6.QtWidgets import QApplication
from widgets.statistics_widgets import StatisticsWidget


def test_statistics_widget():
    """統計ウィジェットのテスト"""
    app = QApplication(sys.argv)
    
    # 統計ウィジェットを作成
    widget = StatisticsWidget(api_base_url="http://localhost:5100")
    widget.setWindowTitle("Statistics Widget Test")
    widget.resize(1000, 700)
    widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_statistics_widget()
