"""
Visual Test for Statistics Widget
統計ウィジェットのビジュアルテスト

This script demonstrates all features of the statistics widget.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import QTimer
from widgets.statistics_widgets import StatisticsWidget, PresetUsageWidget


class StatisticsTestWindow(QMainWindow):
    """統計ウィジェットのテストウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("Statistics Widget - Visual Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # タブウィジェット
        tab_widget = QTabWidget()
        self.setCentralWidget(tab_widget)
        
        # 統計ウィジェット（フル機能）
        self.statistics_widget = StatisticsWidget(api_base_url="http://localhost:5100")
        tab_widget.addTab(self.statistics_widget, "📊 Full Statistics")
        
        # プリセット使用ウィジェット（単体）
        self.preset_widget = PresetUsageWidget(api_base_url="http://localhost:5100")
        tab_widget.addTab(self.preset_widget, "🎨 Preset Usage Only")
        
        # ステータスバー
        self.statusBar().showMessage("Statistics Widget Test - Ready")
        
        # テスト情報を表示
        QTimer.singleShot(1000, self.show_test_info)
    
    def show_test_info(self):
        """テスト情報を表示"""
        info = """
        Statistics Widget Visual Test
        
        Features to Test:
        1. Period Selection (Daily/Weekly/Monthly)
        2. Summary Metrics Display
        3. Processing Statistics
        4. Quality Statistics
        5. Chart Generation (requires matplotlib)
        6. Preset Usage Visualization
        7. CSV Export
        8. PDF Export (requires reportlab)
        9. Real-time Updates
        10. Error Handling
        
        Instructions:
        - Switch between tabs to see different views
        - Change period selection to see data updates
        - Click export buttons to test CSV/PDF generation
        - Click chart buttons to test visualization
        - Wait 30-60 seconds to see auto-refresh
        
        Note: Make sure the API server is running at http://localhost:5100
        """
        
        self.statusBar().showMessage("Test Info: See console for details")
        print(info)


def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # ダークテーマを適用（オプション）
    app.setStyle("Fusion")
    
    # テストウィンドウを作成
    window = StatisticsTestWindow()
    window.show()
    
    print("\n" + "="*60)
    print("Statistics Widget Visual Test Started")
    print("="*60)
    print("\nMake sure the API server is running:")
    print("  cd local_bridge")
    print("  python app.py")
    print("\nThen interact with the GUI to test all features.")
    print("="*60 + "\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
