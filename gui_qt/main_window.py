"""
Main Window for Junmai AutoDev GUI (PyQt6)
メインウィンドウクラス - ダッシュボード、セッション管理、承認キュー等の統合UI
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QFrame, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont
import sys


class MainWindow(QMainWindow):
    """
    Junmai AutoDev メインウィンドウ
    
    Requirements: 8.1 - デスクトップGUI実装
    """
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_status_bar()
        self.setup_timers()
        
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウ設定
        self.setWindowTitle("Junmai AutoDev")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # タブの追加（プレースホルダー）
        self.add_dashboard_tab()
        self.add_sessions_tab()
        self.add_approval_tab()
        self.add_presets_tab()
        self.add_settings_tab()
        self.add_logs_tab()
        
    def add_dashboard_tab(self):
        """ダッシュボードタブ"""
        from widgets.dashboard_widgets import (
            SystemStatusWidget,
            ActiveSessionsWidget,
            RecentActivityWidget,
            QuickActionsWidget
        )
        
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # システムステータスウィジェット
        self.system_status_widget = SystemStatusWidget()
        layout.addWidget(self.system_status_widget)
        
        # アクティブセッションウィジェット
        self.active_sessions_widget = ActiveSessionsWidget()
        self.active_sessions_widget.session_clicked.connect(self.on_session_clicked)
        layout.addWidget(self.active_sessions_widget, 1)
        
        # クイックアクションウィジェット
        self.quick_actions_widget = QuickActionsWidget()
        self.quick_actions_widget.add_hotfolder_clicked.connect(self.on_add_hotfolder)
        self.quick_actions_widget.settings_clicked.connect(self.on_settings_clicked)
        self.quick_actions_widget.statistics_clicked.connect(self.on_statistics_clicked)
        self.quick_actions_widget.approval_queue_clicked.connect(self.on_approval_queue_clicked)
        self.quick_actions_widget.export_now_clicked.connect(self.on_export_now_clicked)
        layout.addWidget(self.quick_actions_widget)
        
        # 最近のアクティビティウィジェット
        self.recent_activity_widget = RecentActivityWidget()
        layout.addWidget(self.recent_activity_widget, 1)
        
        self.tab_widget.addTab(dashboard, "📊 Dashboard")
        
    def add_sessions_tab(self):
        """セッション管理タブ"""
        from widgets.session_widgets import SessionManagementWidget
        
        # セッション管理ウィジェット
        self.session_management_widget = SessionManagementWidget()
        
        self.tab_widget.addTab(self.session_management_widget, "📁 Sessions")
        
    def add_approval_tab(self):
        """承認キュータブ"""
        from widgets.approval_widgets import ApprovalQueueWidget
        
        # 承認キューウィジェット
        self.approval_queue_widget = ApprovalQueueWidget()
        
        self.tab_widget.addTab(self.approval_queue_widget, "✅ Approval")
        
    def add_presets_tab(self):
        """プリセット管理タブ"""
        presets = QWidget()
        layout = QVBoxLayout(presets)
        
        # プレースホルダー
        label = QLabel("Presets - プリセット管理とバージョン管理")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.tab_widget.addTab(presets, "🎨 Presets")
        
    def add_settings_tab(self):
        """設定タブ"""
        from widgets.settings_widgets import SettingsWidget
        
        # 設定ウィジェット
        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_saved.connect(self.on_settings_saved)
        
        self.tab_widget.addTab(self.settings_widget, "⚙️ Settings")
        
    def add_logs_tab(self):
        """ログタブ"""
        logs = QWidget()
        layout = QVBoxLayout(logs)
        
        # プレースホルダー
        label = QLabel("Logs - システムログとアクティビティ")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.tab_widget.addTab(logs, "📝 Logs")
        
    def setup_status_bar(self):
        """ステータスバーの設定"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # ステータス表示
        self.status_label = QLabel("● System: Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.status_bar.addPermanentWidget(QLabel("Lightroom: Disconnected"))
        
    def setup_timers(self):
        """定期更新タイマーの設定"""
        # システムステータス更新（5秒ごと）
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)
        
    def update_status(self):
        """ステータス更新（定期実行）"""
        # TODO: 実際のシステムステータスを取得
        pass
    
    def on_session_clicked(self, session_id: int):
        """セッションクリック時の処理"""
        # セッションタブに切り替えて該当セッションを表示
        self.tab_widget.setCurrentIndex(1)  # Sessions tab
        # TODO: セッション詳細を表示
        print(f"Session clicked: {session_id}")
    
    def on_add_hotfolder(self):
        """ホットフォルダー追加ボタンクリック時の処理"""
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Hot Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            # TODO: APIを呼び出してホットフォルダーを追加
            print(f"Add hot folder: {folder}")
    
    def on_settings_clicked(self):
        """設定ボタンクリック時の処理"""
        # 設定タブに切り替え
        self.tab_widget.setCurrentIndex(4)  # Settings tab
    
    def on_statistics_clicked(self):
        """統計ボタンクリック時の処理"""
        # 統計タブに切り替え（新しいタブを追加）
        # 既存のタブに統計タブがあるか確認
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "📊 Statistics":
                self.tab_widget.setCurrentIndex(i)
                return
        
        # 統計タブを追加
        from widgets.statistics_widgets import StatisticsWidget
        statistics_widget = StatisticsWidget()
        self.tab_widget.addTab(statistics_widget, "📊 Statistics")
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
    
    def on_approval_queue_clicked(self):
        """承認キューボタンクリック時の処理"""
        # 承認タブに切り替え
        self.tab_widget.setCurrentIndex(2)  # Approval tab
    
    def on_export_now_clicked(self):
        """今すぐ書き出しボタンクリック時の処理"""
        # TODO: 書き出し処理を実行
        print("Export now clicked")
    
    def on_settings_saved(self):
        """設定保存時の処理"""
        # システムステータスを更新
        if hasattr(self, 'system_status_widget'):
            self.system_status_widget.update_status()
        
        # ステータスバーに通知
        self.status_bar.showMessage("Settings saved successfully", 3000)
        
    def closeEvent(self, event):
        """ウィンドウクローズ時の処理"""
        # タイマー停止
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # ダッシュボードウィジェットのタイマー停止
        if hasattr(self, 'system_status_widget'):
            self.system_status_widget.update_timer.stop()
        if hasattr(self, 'active_sessions_widget'):
            self.active_sessions_widget.update_timer.stop()
        if hasattr(self, 'recent_activity_widget'):
            self.recent_activity_widget.update_timer.stop()
        if hasattr(self, 'quick_actions_widget'):
            self.quick_actions_widget.update_timer.stop()
        
        # セッション管理ウィジェットのタイマー停止
        if hasattr(self, 'session_management_widget'):
            self.session_management_widget.session_list.update_timer.stop()
        
        event.accept()
