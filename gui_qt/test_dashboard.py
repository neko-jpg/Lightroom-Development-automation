"""
Test script for dashboard widgets
ダッシュボードウィジェットのテスト

Requirements: 7.1, 7.2, 15.1, 15.2
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt6.QtCore import Qt
from widgets.dashboard_widgets import (
    SystemStatusWidget,
    ActiveSessionsWidget,
    RecentActivityWidget,
    QuickActionsWidget
)


def test_dashboard_widgets():
    """Test dashboard widgets individually"""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Dashboard Widgets Test")
    window.setGeometry(100, 100, 1000, 800)
    
    # Create central widget with tabs
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    
    tabs = QTabWidget()
    layout.addWidget(tabs)
    
    # Test System Status Widget
    system_status = SystemStatusWidget()
    tabs.addTab(system_status, "System Status")
    
    # Test Active Sessions Widget
    active_sessions = ActiveSessionsWidget()
    active_sessions.session_clicked.connect(lambda sid: print(f"Session clicked: {sid}"))
    tabs.addTab(active_sessions, "Active Sessions")
    
    # Test Recent Activity Widget
    recent_activity = RecentActivityWidget()
    tabs.addTab(recent_activity, "Recent Activity")
    
    # Test Quick Actions Widget
    quick_actions = QuickActionsWidget()
    quick_actions.add_hotfolder_clicked.connect(lambda: print("Add hotfolder clicked"))
    quick_actions.settings_clicked.connect(lambda: print("Settings clicked"))
    quick_actions.statistics_clicked.connect(lambda: print("Statistics clicked"))
    quick_actions.approval_queue_clicked.connect(lambda: print("Approval queue clicked"))
    quick_actions.export_now_clicked.connect(lambda: print("Export now clicked"))
    tabs.addTab(quick_actions, "Quick Actions")
    
    window.show()
    
    print("Dashboard widgets test window opened")
    print("Note: API endpoints may not be available, widgets will show 'Disconnected' status")
    print("This is expected behavior when backend is not running")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_dashboard_widgets()
