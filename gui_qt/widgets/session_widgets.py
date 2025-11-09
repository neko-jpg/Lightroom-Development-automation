"""
Session Management Widgets for Junmai AutoDev GUI
セッション管理用ウィジェット群

Requirements: 7.1, 7.2, 7.3, 7.4
- セッション一覧表示
- セッション詳細ビュー
- 進捗バーとステータス表示
- セッション操作（一時停止、再開、削除）
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QScrollArea,
    QGridLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from typing import List, Dict, Optional
import requests


class SessionListWidget(QWidget):
    """
    セッション一覧表示ウィジェット
    
    Requirements: 7.1, 7.2
    - セッション一覧をテーブル形式で表示
    - ステータス、進捗、写真数を表示
    - セッション選択時に詳細を表示
    """
    
    session_selected = pyqtSignal(int)  # session_id
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.sessions = []
        self.init_ui()
        
        # 定期更新タイマー（5秒ごと）
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_sessions)
        self.update_timer.start(5000)
        
        # 初回更新
        self.refresh_sessions()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        title = QLabel("Sessions")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # フィルターボタン
        self.filter_all_btn = QPushButton("All")
        self.filter_all_btn.setCheckable(True)
        self.filter_all_btn.setChecked(True)
        self.filter_all_btn.clicked.connect(lambda: self.set_filter(None))
        header_layout.addWidget(self.filter_all_btn)
        
        self.filter_active_btn = QPushButton("Active")
        self.filter_active_btn.setCheckable(True)
        self.filter_active_btn.clicked.connect(lambda: self.set_filter('active'))
        header_layout.addWidget(self.filter_active_btn)
        
        self.filter_completed_btn = QPushButton("Completed")
        self.filter_completed_btn.setCheckable(True)
        self.filter_completed_btn.clicked.connect(lambda: self.set_filter('completed'))
        header_layout.addWidget(self.filter_completed_btn)
        
        # リフレッシュボタン
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_sessions)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # セッションテーブル
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Status", "Photos", "Progress", "Created", "Folder"
        ])
        
        # テーブル設定
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # カラム幅調整
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Photos
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Progress
        header.resizeSection(3, 150)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Created
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Folder
        
        # 行選択イベント
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        self.current_filter = None
    
    def set_filter(self, filter_type: Optional[str]):
        """フィルターを設定"""
        self.current_filter = filter_type
        
        # ボタンの状態を更新
        self.filter_all_btn.setChecked(filter_type is None)
        self.filter_active_btn.setChecked(filter_type == 'active')
        self.filter_completed_btn.setChecked(filter_type == 'completed')
        
        # セッションを再表示
        self.display_sessions(self.sessions)
    
    def refresh_sessions(self):
        """セッション一覧を更新"""
        try:
            response = requests.get(f"{self.api_base_url}/sessions?limit=100", timeout=2)
            if response.status_code == 200:
                self.sessions = response.json()
                self.display_sessions(self.sessions)
        except Exception as e:
            print(f"Failed to refresh sessions: {e}")
    
    def display_sessions(self, sessions: List[Dict]):
        """セッションをテーブルに表示"""
        # フィルター適用
        if self.current_filter == 'active':
            filtered_sessions = [s for s in sessions if s.get('status') != 'completed']
        elif self.current_filter == 'completed':
            filtered_sessions = [s for s in sessions if s.get('status') == 'completed']
        else:
            filtered_sessions = sessions
        
        # テーブルをクリア
        self.table.setRowCount(0)
        
        # セッションを追加
        for session in filtered_sessions:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(session.get('name', 'Unknown'))
            name_item.setData(Qt.ItemDataRole.UserRole, session.get('id'))
            self.table.setItem(row, 0, name_item)
            
            # Status
            status = session.get('status', 'unknown')
            status_item = QTableWidgetItem(status.capitalize())
            status_item.setForeground(self.get_status_color(status))
            self.table.setItem(row, 1, status_item)
            
            # Photos
            total = session.get('total_photos', 0)
            processed = session.get('processed_photos', 0)
            photos_item = QTableWidgetItem(f"{processed}/{total}")
            self.table.setItem(row, 2, photos_item)
            
            # Progress
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_layout.setContentsMargins(5, 2, 5, 2)
            
            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            progress_pct = (processed / total * 100) if total > 0 else 0
            progress_bar.setValue(int(progress_pct))
            progress_bar.setTextVisible(True)
            progress_bar.setFormat(f"{progress_pct:.0f}%")
            progress_layout.addWidget(progress_bar)
            
            self.table.setCellWidget(row, 3, progress_widget)
            
            # Created
            created_at = session.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    created_str = created_at[:16]
            else:
                created_str = 'Unknown'
            created_item = QTableWidgetItem(created_str)
            self.table.setItem(row, 4, created_item)
            
            # Folder
            folder = session.get('import_folder', '')
            folder_item = QTableWidgetItem(folder)
            self.table.setItem(row, 5, folder_item)
    
    def get_status_color(self, status: str) -> QColor:
        """ステータスに応じた色を返す"""
        color_map = {
            'importing': QColor('#2196F3'),  # Blue
            'selecting': QColor('#FFC107'),  # Amber
            'developing': QColor('#FF9800'),  # Orange
            'exporting': QColor('#9C27B0'),  # Purple
            'completed': QColor('#4CAF50'),  # Green
        }
        return color_map.get(status, QColor('#9E9E9E'))  # Gray
    
    def on_selection_changed(self):
        """選択変更時の処理"""
        selected_items = self.table.selectedItems()
        if selected_items:
            # 最初のカラムからsession_idを取得
            session_id = self.table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            if session_id:
                self.session_selected.emit(session_id)
    
    def get_selected_session_id(self) -> Optional[int]:
        """選択されているセッションIDを取得"""
        selected_items = self.table.selectedItems()
        if selected_items:
            return self.table.item(selected_items[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return None


class SessionDetailWidget(QWidget):
    """
    セッション詳細表示ウィジェット
    
    Requirements: 7.2, 7.3, 7.4
    - セッション詳細情報の表示
    - 写真ステータスの内訳
    - セッション操作ボタン
    """
    
    session_paused = pyqtSignal(int)  # session_id
    session_resumed = pyqtSignal(int)  # session_id
    session_deleted = pyqtSignal(int)  # session_id
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.current_session_id = None
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("Session Details")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 詳細情報グループ
        info_group = QGroupBox("Information")
        info_layout = QGridLayout()
        info_layout.setSpacing(10)
        
        # セッション名
        info_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_label = QLabel("-")
        self.name_label.setWordWrap(True)
        info_layout.addWidget(self.name_label, 0, 1)
        
        # ステータス
        info_layout.addWidget(QLabel("Status:"), 1, 0)
        self.status_label = QLabel("-")
        info_layout.addWidget(self.status_label, 1, 1)
        
        # 作成日時
        info_layout.addWidget(QLabel("Created:"), 2, 0)
        self.created_label = QLabel("-")
        info_layout.addWidget(self.created_label, 2, 1)
        
        # インポートフォルダ
        info_layout.addWidget(QLabel("Import Folder:"), 3, 0)
        self.folder_label = QLabel("-")
        self.folder_label.setWordWrap(True)
        info_layout.addWidget(self.folder_label, 3, 1)
        
        # 写真数
        info_layout.addWidget(QLabel("Total Photos:"), 4, 0)
        self.total_photos_label = QLabel("-")
        info_layout.addWidget(self.total_photos_label, 4, 1)
        
        # 処理済み写真数
        info_layout.addWidget(QLabel("Processed:"), 5, 0)
        self.processed_photos_label = QLabel("-")
        info_layout.addWidget(self.processed_photos_label, 5, 1)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 進捗バー
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("0%")
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 写真ステータス内訳
        stats_group = QGroupBox("Photo Statistics")
        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)
        
        self.stats_labels = {}
        statuses = ['imported', 'analyzed', 'queued', 'processing', 'completed', 'failed', 'rejected']
        
        for i, status in enumerate(statuses):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(f"{status.capitalize()}:")
            stats_layout.addWidget(label, row, col)
            
            value_label = QLabel("0")
            self.stats_labels[status] = value_label
            stats_layout.addWidget(value_label, row, col + 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 操作ボタン
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.on_pause_clicked)
        self.pause_btn.setEnabled(False)
        actions_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("▶ Resume")
        self.resume_btn.clicked.connect(self.on_resume_clicked)
        self.resume_btn.setEnabled(False)
        actions_layout.addWidget(self.resume_btn)
        
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { color: #F44336; }")
        actions_layout.addWidget(self.delete_btn)
        
        actions_layout.addStretch()
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        # プレースホルダー表示
        self.placeholder = QLabel("Select a session to view details")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.placeholder)
        
        # 詳細ウィジェットを非表示
        info_group.hide()
        progress_group.hide()
        stats_group.hide()
        actions_group.hide()
    
    def load_session(self, session_id: int):
        """セッション詳細を読み込み"""
        self.current_session_id = session_id
        
        try:
            response = requests.get(f"{self.api_base_url}/sessions/{session_id}", timeout=2)
            if response.status_code == 200:
                session_data = response.json()
                self.display_session(session_data)
            else:
                self.show_error("Failed to load session details")
        except Exception as e:
            self.show_error(f"Error loading session: {e}")
    
    def display_session(self, session: Dict):
        """セッション情報を表示"""
        # プレースホルダーを非表示
        self.placeholder.hide()
        
        # 詳細ウィジェットを表示
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                widget.show()
        
        # 基本情報
        self.name_label.setText(session.get('name', 'Unknown'))
        
        status = session.get('status', 'unknown')
        self.status_label.setText(status.capitalize())
        self.status_label.setStyleSheet(f"color: {self.get_status_color_hex(status)}; font-weight: bold;")
        
        created_at = session.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                created_str = created_at
        else:
            created_str = 'Unknown'
        self.created_label.setText(created_str)
        
        self.folder_label.setText(session.get('import_folder', 'Unknown'))
        
        total = session.get('total_photos', 0)
        processed = session.get('processed_photos', 0)
        self.total_photos_label.setText(str(total))
        self.processed_photos_label.setText(str(processed))
        
        # 進捗バー
        progress_pct = (processed / total * 100) if total > 0 else 0
        self.progress_bar.setValue(int(progress_pct))
        self.progress_bar.setFormat(f"{progress_pct:.1f}%")
        
        # 写真ステータス内訳
        photo_stats = session.get('photo_stats', {})
        for status_key, label in self.stats_labels.items():
            count = photo_stats.get(status_key, 0)
            label.setText(str(count))
        
        # ボタンの有効/無効
        self.update_action_buttons(status)
    
    def update_action_buttons(self, status: str):
        """ステータスに応じてボタンを有効/無効化"""
        # 一時停止ボタン: processing中のみ有効
        self.pause_btn.setEnabled(status in ['selecting', 'developing', 'exporting'])
        
        # 再開ボタン: 一時停止中のみ有効（現在は未実装）
        self.resume_btn.setEnabled(False)
        
        # 削除ボタン: 常に有効
        self.delete_btn.setEnabled(True)
    
    def get_status_color_hex(self, status: str) -> str:
        """ステータスに応じた色を返す（16進数）"""
        color_map = {
            'importing': '#2196F3',
            'selecting': '#FFC107',
            'developing': '#FF9800',
            'exporting': '#9C27B0',
            'completed': '#4CAF50',
        }
        return color_map.get(status, '#9E9E9E')
    
    def on_pause_clicked(self):
        """一時停止ボタンクリック時の処理"""
        if self.current_session_id:
            reply = QMessageBox.question(
                self,
                "Pause Session",
                "Are you sure you want to pause this session?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # TODO: API呼び出しでセッションを一時停止
                self.session_paused.emit(self.current_session_id)
                QMessageBox.information(self, "Success", "Session paused (feature not yet implemented)")
    
    def on_resume_clicked(self):
        """再開ボタンクリック時の処理"""
        if self.current_session_id:
            # TODO: API呼び出しでセッションを再開
            self.session_resumed.emit(self.current_session_id)
            QMessageBox.information(self, "Success", "Session resumed (feature not yet implemented)")
    
    def on_delete_clicked(self):
        """削除ボタンクリック時の処理"""
        if self.current_session_id:
            reply = QMessageBox.warning(
                self,
                "Delete Session",
                "Are you sure you want to delete this session?\n\n"
                "This will remove all associated photos and jobs from the database.\n"
                "This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    response = requests.delete(
                        f"{self.api_base_url}/sessions/{self.current_session_id}",
                        timeout=2
                    )
                    if response.status_code == 200:
                        self.session_deleted.emit(self.current_session_id)
                        QMessageBox.information(self, "Success", "Session deleted successfully")
                        self.clear_display()
                    else:
                        QMessageBox.warning(self, "Error", "Failed to delete session")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error deleting session: {e}")
    
    def clear_display(self):
        """表示をクリア"""
        self.current_session_id = None
        
        # 詳細ウィジェットを非表示
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                widget.hide()
        
        # プレースホルダーを表示
        self.placeholder.show()
    
    def show_error(self, message: str):
        """エラーメッセージを表示"""
        QMessageBox.warning(self, "Error", message)


class SessionManagementWidget(QWidget):
    """
    セッション管理メインウィジェット
    
    Requirements: 7.1, 7.2, 7.3, 7.4
    - セッション一覧と詳細を統合
    - スプリッターで分割表示
    """
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # スプリッター（左: 一覧、右: 詳細）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # セッション一覧
        self.session_list = SessionListWidget(self.api_base_url)
        self.session_list.session_selected.connect(self.on_session_selected)
        splitter.addWidget(self.session_list)
        
        # セッション詳細
        self.session_detail = SessionDetailWidget(self.api_base_url)
        self.session_detail.session_deleted.connect(self.on_session_deleted)
        splitter.addWidget(self.session_detail)
        
        # スプリッターの初期サイズ（60:40）
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
    
    def on_session_selected(self, session_id: int):
        """セッション選択時の処理"""
        self.session_detail.load_session(session_id)
    
    def on_session_deleted(self, session_id: int):
        """セッション削除時の処理"""
        # セッション一覧を更新
        self.session_list.refresh_sessions()
