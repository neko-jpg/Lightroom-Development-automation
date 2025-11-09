"""
Dashboard Widgets for Junmai AutoDev GUI
ダッシュボード用ウィジェット群

Requirements: 7.1, 7.2, 15.1, 15.2
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QScrollArea,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from datetime import datetime
from typing import List, Dict, Optional
import requests


class SystemStatusWidget(QWidget):
    """
    システムステータス表示ウィジェット
    
    Requirements: 7.1, 7.2
    - システム稼働状態
    - LLMモデル情報
    - Lightroom接続状態
    - GPU使用状況
    """
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.init_ui()
        
        # 定期更新タイマー（5秒ごと）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)
        
        # 初回更新
        self.update_status()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("System Status")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # ステータスグリッド
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # システム状態
        self.system_status_label = QLabel("● System:")
        self.system_status_value = QLabel("Checking...")
        grid.addWidget(self.system_status_label, 0, 0)
        grid.addWidget(self.system_status_value, 0, 1)
        
        # LLMモデル
        self.llm_label = QLabel("● LLM:")
        self.llm_value = QLabel("Checking...")
        grid.addWidget(self.llm_label, 0, 2)
        grid.addWidget(self.llm_value, 0, 3)
        
        # Lightroom接続
        self.lr_label = QLabel("● Lightroom:")
        self.lr_value = QLabel("Checking...")
        grid.addWidget(self.lr_label, 1, 0)
        grid.addWidget(self.lr_value, 1, 1)
        
        # GPU状態
        self.gpu_label = QLabel("● GPU:")
        self.gpu_value = QLabel("Checking...")
        grid.addWidget(self.gpu_label, 1, 2)
        grid.addWidget(self.gpu_value, 1, 3)
        
        layout.addLayout(grid)
        
        # 統計情報
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Today: -- photos processed | --% success | --s avg")
        stats_layout.addWidget(self.stats_label)
        layout.addLayout(stats_layout)
        
        layout.addStretch()
    
    def update_status(self):
        """ステータス情報を更新"""
        try:
            # システムヘルスチェック
            response = requests.get(f"{self.api_base_url}/system/health", timeout=2)
            if response.status_code == 200:
                self.system_status_value.setText("Running")
                self.system_status_label.setText("● System:")
                self.set_status_color(self.system_status_label, "green")
            else:
                self.system_status_value.setText("Error")
                self.set_status_color(self.system_status_label, "red")
        except:
            self.system_status_value.setText("Disconnected")
            self.set_status_color(self.system_status_label, "red")
        
        try:
            # 設定情報取得（LLM情報含む）
            response = requests.get(f"{self.api_base_url}/config", timeout=2)
            if response.status_code == 200:
                config = response.json()
                llm_model = config.get('ai', {}).get('llm_model', 'Unknown')
                self.llm_value.setText(f"Ollama ({llm_model})")
                self.set_status_color(self.llm_label, "green")
            else:
                self.llm_value.setText("Unknown")
                self.set_status_color(self.llm_label, "yellow")
        except:
            self.llm_value.setText("Disconnected")
            self.set_status_color(self.llm_label, "red")
        
        try:
            # WebSocketステータス（Lightroom接続の代理）
            response = requests.get(f"{self.api_base_url}/websocket/status", timeout=2)
            if response.status_code == 200:
                ws_status = response.json()
                if ws_status.get('connected_clients', 0) > 0:
                    self.lr_value.setText("Connected")
                    self.set_status_color(self.lr_label, "green")
                else:
                    self.lr_value.setText("Disconnected")
                    self.set_status_color(self.lr_label, "yellow")
            else:
                self.lr_value.setText("Unknown")
                self.set_status_color(self.lr_label, "yellow")
        except:
            self.lr_value.setText("Disconnected")
            self.set_status_color(self.lr_label, "yellow")
        
        try:
            # GPU情報（リソースマネージャーから）
            response = requests.get(f"{self.api_base_url}/resource/status", timeout=2)
            if response.status_code == 200:
                resource_status = response.json()
                gpu_temp = resource_status.get('gpu_temperature', 0)
                gpu_memory = resource_status.get('gpu_memory_used_mb', 0)
                gpu_memory_total = resource_status.get('gpu_memory_total_mb', 8192)
                self.gpu_value.setText(f"{gpu_temp}°C ({gpu_memory:.1f}GB/{gpu_memory_total/1024:.1f}GB)")
                
                # 温度に応じて色を変更
                if gpu_temp > 75:
                    self.set_status_color(self.gpu_label, "red")
                elif gpu_temp > 65:
                    self.set_status_color(self.gpu_label, "yellow")
                else:
                    self.set_status_color(self.gpu_label, "green")
            else:
                self.gpu_value.setText("Unknown")
                self.set_status_color(self.gpu_label, "yellow")
        except:
            self.gpu_value.setText("N/A")
            self.set_status_color(self.gpu_label, "gray")
        
        # 今日の統計情報を更新
        self.update_today_stats()
    
    def update_today_stats(self):
        """今日の統計情報を更新"""
        try:
            response = requests.get(f"{self.api_base_url}/statistics/daily", timeout=2)
            if response.status_code == 200:
                stats = response.json()
                today_stats = stats.get('today', {})
                
                total_processed = today_stats.get('total_processed', 0)
                success_rate = today_stats.get('success_rate', 0) * 100
                avg_time = today_stats.get('avg_processing_time', 0)
                
                self.stats_label.setText(
                    f"Today: {total_processed} photos processed | "
                    f"{success_rate:.0f}% success | {avg_time:.1f}s avg"
                )
        except:
            pass
    
    def set_status_color(self, label: QLabel, color: str):
        """ステータスラベルの色を設定"""
        color_map = {
            "green": "#4CAF50",
            "yellow": "#FFC107",
            "red": "#F44336",
            "gray": "#9E9E9E"
        }
        
        hex_color = color_map.get(color, "#9E9E9E")
        label.setStyleSheet(f"color: {hex_color};")


class ActiveSessionsWidget(QWidget):
    """
    アクティブセッション一覧ウィジェット
    
    Requirements: 7.1, 7.2, 7.3
    - セッション一覧表示
    - 進捗バー
    - ステータス表示
    """
    
    session_clicked = pyqtSignal(int)  # session_id
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.init_ui()
        
        # 定期更新タイマー（3秒ごと）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_sessions)
        self.update_timer.start(3000)
        
        # 初回更新
        self.update_sessions()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("Active Sessions")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # セッションコンテナ
        self.sessions_container = QWidget()
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setSpacing(10)
        self.sessions_layout.addStretch()
        
        scroll.setWidget(self.sessions_container)
        layout.addWidget(scroll)
    
    def update_sessions(self):
        """セッション一覧を更新"""
        try:
            response = requests.get(f"{self.api_base_url}/sessions", timeout=2)
            if response.status_code == 200:
                sessions = response.json()
                self.display_sessions(sessions)
        except:
            pass
    
    def display_sessions(self, sessions: List[Dict]):
        """セッションを表示"""
        # 既存のウィジェットをクリア
        while self.sessions_layout.count() > 1:  # Keep stretch
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # アクティブなセッションのみ表示（完了以外）
        active_sessions = [s for s in sessions if s.get('status') != 'completed']
        
        if not active_sessions:
            no_sessions = QLabel("No active sessions")
            no_sessions.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_sessions.setStyleSheet("color: #888;")
            self.sessions_layout.insertWidget(0, no_sessions)
            return
        
        for session in active_sessions:
            session_widget = self.create_session_widget(session)
            self.sessions_layout.insertWidget(self.sessions_layout.count() - 1, session_widget)
    
    def create_session_widget(self, session: Dict) -> QWidget:
        """個別セッションウィジェットを作成"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.StyledPanel)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        # セッション名とステータス
        header_layout = QHBoxLayout()
        
        name_label = QLabel(f"📁 {session.get('name', 'Unknown')}")
        name_font = QFont()
        name_font.setBold(True)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # 進捗情報
        total = session.get('total_photos', 0)
        processed = session.get('processed_photos', 0)
        progress_pct = (processed / total * 100) if total > 0 else 0
        
        progress_text = QLabel(f"({processed}/{total} photos)")
        header_layout.addWidget(progress_text)
        
        layout.addLayout(header_layout)
        
        # プログレスバー
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(progress_pct))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{progress_pct:.0f}%")
        layout.addWidget(progress_bar)
        
        # ステータスとETA
        status_layout = QHBoxLayout()
        
        status = session.get('status', 'unknown')
        status_label = QLabel(f"Status: {status.capitalize()}")
        status_layout.addWidget(status_label)
        
        status_layout.addStretch()
        
        # ETA計算（簡易版）
        if processed > 0 and processed < total:
            # 仮の計算（実際は処理速度から算出）
            remaining = total - processed
            eta_min = remaining * 0.2  # 1枚あたり約12秒と仮定
            eta_label = QLabel(f"ETA: {int(eta_min)} min")
            status_layout.addWidget(eta_label)
        
        layout.addLayout(status_layout)
        
        # クリックイベント
        widget.mousePressEvent = lambda e: self.session_clicked.emit(session.get('id', 0))
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        return widget


class RecentActivityWidget(QWidget):
    """
    最近のアクティビティログ表示ウィジェット
    
    Requirements: 7.2, 15.2
    - 処理ログの表示
    - リアルタイム更新
    """
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.init_ui()
        
        # 定期更新タイマー（2秒ごと）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_activity)
        self.update_timer.start(2000)
        
        # 初回更新
        self.update_activity()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("Recent Activity")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # アクティビティコンテナ
        self.activity_container = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setSpacing(5)
        self.activity_layout.addStretch()
        
        scroll.setWidget(self.activity_container)
        layout.addWidget(scroll)
    
    def update_activity(self):
        """アクティビティログを更新"""
        try:
            response = requests.get(
                f"{self.api_base_url}/logs?category=main&lines=20",
                timeout=2
            )
            if response.status_code == 200:
                log_data = response.json()
                entries = log_data.get('entries', [])
                self.display_activity(entries)
        except:
            pass
    
    def display_activity(self, entries: List[Dict]):
        """アクティビティを表示"""
        # 既存のウィジェットをクリア
        while self.activity_layout.count() > 1:  # Keep stretch
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not entries:
            no_activity = QLabel("No recent activity")
            no_activity.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_activity.setStyleSheet("color: #888;")
            self.activity_layout.insertWidget(0, no_activity)
            return
        
        # 最新20件を表示（逆順）
        for entry in reversed(entries[-20:]):
            activity_widget = self.create_activity_widget(entry)
            self.activity_layout.insertWidget(0, activity_widget)
    
    def create_activity_widget(self, entry: Dict) -> QWidget:
        """個別アクティビティウィジェットを作成"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # タイムスタンプ
        timestamp = entry.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            except:
                time_str = timestamp[:5]
        else:
            time_str = '--:--'
        
        time_label = QLabel(time_str)
        time_label.setFixedWidth(50)
        time_label.setStyleSheet("color: #888;")
        layout.addWidget(time_label)
        
        # アイコンとメッセージ
        level = entry.get('level', 'INFO')
        message = entry.get('message', '')
        
        # レベルに応じたアイコン
        icon_map = {
            'INFO': '✓',
            'WARNING': '⚠',
            'ERROR': '✗',
            'DEBUG': '●'
        }
        icon = icon_map.get(level, '●')
        
        # 色設定
        color_map = {
            'INFO': '#4CAF50',
            'WARNING': '#FFC107',
            'ERROR': '#F44336',
            'DEBUG': '#2196F3'
        }
        color = color_map.get(level, '#888')
        
        message_label = QLabel(f"{icon} {message}")
        message_label.setStyleSheet(f"color: {color};")
        layout.addWidget(message_label, 1)
        
        return widget


class QuickActionsWidget(QWidget):
    """
    クイックアクションボタンウィジェット
    
    Requirements: 7.1
    - よく使う操作へのショートカット
    """
    
    add_hotfolder_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    statistics_clicked = pyqtSignal()
    approval_queue_clicked = pyqtSignal()
    export_now_clicked = pyqtSignal()
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.init_ui()
        
        # 承認キュー数の定期更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_approval_count)
        self.update_timer.start(5000)
        
        # 初回更新
        self.update_approval_count()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("Quick Actions")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # ボタングリッド
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # ホットフォルダー追加
        self.add_hotfolder_btn = QPushButton("📂 Add Hot Folder")
        self.add_hotfolder_btn.clicked.connect(self.add_hotfolder_clicked.emit)
        grid.addWidget(self.add_hotfolder_btn, 0, 0)
        
        # 設定
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        grid.addWidget(self.settings_btn, 0, 1)
        
        # 統計
        self.statistics_btn = QPushButton("📊 Statistics")
        self.statistics_btn.clicked.connect(self.statistics_clicked.emit)
        grid.addWidget(self.statistics_btn, 0, 2)
        
        # 承認キュー
        self.approval_queue_btn = QPushButton("✅ Approval Queue (--)")
        self.approval_queue_btn.clicked.connect(self.approval_queue_clicked.emit)
        grid.addWidget(self.approval_queue_btn, 1, 0)
        
        # 今すぐ書き出し
        self.export_now_btn = QPushButton("📤 Export Now")
        self.export_now_btn.clicked.connect(self.export_now_clicked.emit)
        grid.addWidget(self.export_now_btn, 1, 1)
        
        layout.addLayout(grid)
        layout.addStretch()
    
    def update_approval_count(self):
        """承認待ち写真数を更新"""
        try:
            response = requests.get(f"{self.api_base_url}/approval/queue", timeout=2)
            if response.status_code == 200:
                queue_data = response.json()
                count = len(queue_data.get('photos', []))
                self.approval_queue_btn.setText(f"✅ Approval Queue ({count})")
        except:
            pass
