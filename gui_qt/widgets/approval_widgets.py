"""
Approval Queue Widgets for Junmai AutoDev GUI
承認キュー画面のウィジェット群

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSplitter, QTextEdit, QGroupBox,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QKeySequence, QShortcut, QImage
import requests
from datetime import datetime
from typing import Optional, Dict, List


class PhotoComparisonWidget(QWidget):
    """
    Before/After写真比較表示ウィジェット
    
    Requirements: 5.2 - 承認画面で現像前後の比較表示を提供する
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_photo = None
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Before画像
        before_container = QFrame()
        before_container.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        before_layout = QVBoxLayout(before_container)
        
        before_label = QLabel("Before (Original)")
        before_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        before_label.setStyleSheet("font-weight: bold; padding: 5px;")
        before_layout.addWidget(before_label)
        
        self.before_image = QLabel()
        self.before_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.before_image.setMinimumSize(400, 400)
        self.before_image.setStyleSheet("background-color: #2b2b2b;")
        self.before_image.setScaledContents(False)
        before_layout.addWidget(self.before_image, 1)
        
        layout.addWidget(before_container, 1)
        
        # After画像
        after_container = QFrame()
        after_container.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        after_layout = QVBoxLayout(after_container)
        
        after_label = QLabel("After (Processed)")
        after_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        after_label.setStyleSheet("font-weight: bold; padding: 5px;")
        after_layout.addWidget(after_label)
        
        self.after_image = QLabel()
        self.after_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.after_image.setMinimumSize(400, 400)
        self.after_image.setStyleSheet("background-color: #2b2b2b;")
        self.after_image.setScaledContents(False)
        after_layout.addWidget(self.after_image, 1)
        
        layout.addWidget(after_container, 1)
    
    def load_photo(self, photo_data: Dict):
        """
        写真データを読み込んで表示
        
        Args:
            photo_data: 写真データ辞書
        """
        self.current_photo = photo_data
        
        # TODO: 実際の画像ファイルを読み込む
        # プレースホルダー画像を表示
        self.before_image.setText(f"Before\n{photo_data.get('file_name', 'N/A')}")
        self.after_image.setText(f"After\n{photo_data.get('file_name', 'N/A')}")


class AIEvaluationWidget(QWidget):
    """
    AI評価スコア表示ウィジェット
    
    Requirements: 5.2 - AI評価スコア表示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("AI Evaluation")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 総合スコア
        score_layout = QHBoxLayout()
        score_label = QLabel("Overall Score:")
        self.score_value = QLabel("★★★★☆ 4.2")
        self.score_value.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffa500;")
        score_layout.addWidget(score_label)
        score_layout.addWidget(self.score_value)
        score_layout.addStretch()
        layout.addLayout(score_layout)
        
        # 詳細スコア
        self.focus_score = self._create_score_row("Focus:", "4.5")
        self.exposure_score = self._create_score_row("Exposure:", "4.0")
        self.composition_score = self._create_score_row("Composition:", "4.3")
        
        layout.addLayout(self.focus_score)
        layout.addLayout(self.exposure_score)
        layout.addLayout(self.composition_score)
        
        # 被写体情報
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Subject:")
        self.subject_value = QLabel("Portrait")
        subject_layout.addWidget(subject_label)
        subject_layout.addWidget(self.subject_value)
        subject_layout.addStretch()
        layout.addLayout(subject_layout)
        
        # 顔検出
        faces_layout = QHBoxLayout()
        faces_label = QLabel("Detected Faces:")
        self.faces_value = QLabel("2")
        faces_layout.addWidget(faces_label)
        faces_layout.addWidget(self.faces_value)
        faces_layout.addStretch()
        layout.addLayout(faces_layout)
        
        layout.addStretch()
    
    def _create_score_row(self, label_text: str, default_value: str) -> QHBoxLayout:
        """スコア行を作成"""
        layout = QHBoxLayout()
        label = QLabel(label_text)
        value = QLabel(default_value)
        value.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        layout.addWidget(value)
        layout.addStretch()
        return layout
    
    def update_scores(self, photo_data: Dict):
        """
        AI評価スコアを更新
        
        Args:
            photo_data: 写真データ辞書
        """
        ai_score = photo_data.get('ai_score', 0)
        stars = self._score_to_stars(ai_score)
        self.score_value.setText(f"{stars} {ai_score:.1f}")
        
        # 詳細スコア更新
        focus = photo_data.get('focus_score', 0)
        exposure = photo_data.get('exposure_score', 0)
        composition = photo_data.get('composition_score', 0)
        
        self.focus_score.itemAt(1).widget().setText(f"{focus:.1f}")
        self.exposure_score.itemAt(1).widget().setText(f"{exposure:.1f}")
        self.composition_score.itemAt(1).widget().setText(f"{composition:.1f}")
        
        # 被写体情報
        self.subject_value.setText(photo_data.get('subject_type', 'Unknown'))
        self.faces_value.setText(str(photo_data.get('detected_faces', 0)))
    
    def _score_to_stars(self, score: float) -> str:
        """スコアを星表示に変換"""
        full_stars = int(score)
        half_star = (score - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        stars = "★" * full_stars
        if half_star:
            stars += "⯨"
        stars += "☆" * empty_stars
        
        return stars


class ParameterDetailsWidget(QWidget):
    """
    適用パラメータ詳細表示ウィジェット
    
    Requirements: 5.2 - 適用パラメータ詳細表示を実装
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("Applied Parameters")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # コンテキスト
        context_layout = QHBoxLayout()
        context_label = QLabel("Context:")
        self.context_value = QLabel("Backlit Portrait")
        self.context_value.setStyleSheet("font-weight: bold; color: #4a9eff;")
        context_layout.addWidget(context_label)
        context_layout.addWidget(self.context_value)
        context_layout.addStretch()
        layout.addLayout(context_layout)
        
        # プリセット
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        self.preset_value = QLabel("WhiteLayer_Transparency_v4 (60% blend)")
        self.preset_value.setStyleSheet("font-weight: bold;")
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_value)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)
        
        # 調整パラメータ
        adjustments_label = QLabel("Adjustments:")
        adjustments_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(adjustments_label)
        
        # パラメータリスト（スクロール可能）
        self.params_text = QTextEdit()
        self.params_text.setReadOnly(True)
        self.params_text.setMaximumHeight(200)
        self.params_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.params_text)
        
        layout.addStretch()
    
    def update_parameters(self, photo_data: Dict):
        """
        適用パラメータを更新
        
        Args:
            photo_data: 写真データ辞書
        """
        # コンテキスト
        context = photo_data.get('context_tag', 'Unknown')
        self.context_value.setText(context)
        
        # プリセット
        preset = photo_data.get('selected_preset', 'None')
        self.preset_value.setText(preset)
        
        # パラメータ詳細（サンプル）
        params_text = """• Exposure: -0.15 EV
• Highlights: -18
• Shadows: +12
• Whites: +5
• Blacks: -3
• Clarity: +8
• Vibrance: +10
• Saturation: +2

HSL Adjustments:
• Orange Hue: -4
• Orange Sat: -6
• Orange Lum: +4
• Blue Sat: -8
• Blue Lum: -6

Tone Curve:
• Custom curve applied
"""
        self.params_text.setPlainText(params_text)


class ApprovalActionsWidget(QWidget):
    """
    承認・却下・修正ボタンウィジェット
    
    Requirements: 5.3, 5.4 - 承認・却下・修正ボタンを追加
    """
    
    approved = pyqtSignal(int)  # photo_id
    rejected = pyqtSignal(int)  # photo_id
    modify_requested = pyqtSignal(int)  # photo_id
    skipped = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_photo_id = None
        self.init_ui()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 承認ボタン
        self.approve_btn = QPushButton("✓ Approve")
        self.approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.approve_btn.clicked.connect(self.on_approve)
        layout.addWidget(self.approve_btn)
        
        # 却下ボタン
        self.reject_btn = QPushButton("✗ Reject")
        self.reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.reject_btn.clicked.connect(self.on_reject)
        layout.addWidget(self.reject_btn)
        
        # 修正ボタン
        self.modify_btn = QPushButton("✏️ Modify")
        self.modify_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #d39e00;
            }
        """)
        self.modify_btn.clicked.connect(self.on_modify)
        layout.addWidget(self.modify_btn)
        
        # スキップボタン
        self.skip_btn = QPushButton("⏭️ Skip")
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.skip_btn.clicked.connect(self.on_skip)
        layout.addWidget(self.skip_btn)
        
        layout.addStretch()
    
    def set_photo_id(self, photo_id: int):
        """現在の写真IDを設定"""
        self.current_photo_id = photo_id
    
    def on_approve(self):
        """承認ボタンクリック"""
        if self.current_photo_id:
            self.approved.emit(self.current_photo_id)
    
    def on_reject(self):
        """却下ボタンクリック"""
        if self.current_photo_id:
            self.rejected.emit(self.current_photo_id)
    
    def on_modify(self):
        """修正ボタンクリック"""
        if self.current_photo_id:
            self.modify_requested.emit(self.current_photo_id)
    
    def on_skip(self):
        """スキップボタンクリック"""
        self.skipped.emit()


class ApprovalQueueWidget(QWidget):
    """
    承認キュー統合ウィジェット
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.1
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_base_url = "http://localhost:5100/api"
        self.current_index = 0
        self.photos = []
        self.init_ui()
        self.setup_keyboard_shortcuts()
        self.load_approval_queue()
        
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Approval Queue (0 photos pending)")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # 進捗表示
        self.progress_label = QLabel("Photo 0 of 0")
        header_layout.addWidget(self.progress_label)
        
        # リフレッシュボタン
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_approval_queue)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # メインコンテンツ（スプリッター）
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側: 写真比較
        self.comparison_widget = PhotoComparisonWidget()
        splitter.addWidget(self.comparison_widget)
        
        # 右側: 評価とパラメータ
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # AI評価
        self.evaluation_widget = AIEvaluationWidget()
        right_layout.addWidget(self.evaluation_widget)
        
        # パラメータ詳細
        self.parameters_widget = ParameterDetailsWidget()
        right_layout.addWidget(self.parameters_widget)
        
        splitter.addWidget(right_panel)
        
        # スプリッターの比率設定（左:右 = 2:1）
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter, 1)
        
        # アクションボタン
        self.actions_widget = ApprovalActionsWidget()
        self.actions_widget.approved.connect(self.on_approve)
        self.actions_widget.rejected.connect(self.on_reject)
        self.actions_widget.modify_requested.connect(self.on_modify)
        self.actions_widget.skipped.connect(self.on_skip)
        layout.addWidget(self.actions_widget)
        
        # キーボードショートカットヘルプ
        help_label = QLabel("Keyboard: ← Previous | → Next | Enter Approve | Delete Reject | M Modify | S Skip")
        help_label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(help_label)
    
    def setup_keyboard_shortcuts(self):
        """
        キーボードショートカットの設定
        
        Requirements: 5.5 - キーボードショートカット対応を実装
        """
        # 前の写真: ←
        prev_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        prev_shortcut.activated.connect(self.previous_photo)
        
        # 次の写真: →
        next_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        next_shortcut.activated.connect(self.next_photo)
        
        # 承認: Enter
        approve_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        approve_shortcut.activated.connect(lambda: self.on_approve(self.get_current_photo_id()))
        
        # 却下: Delete
        reject_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        reject_shortcut.activated.connect(lambda: self.on_reject(self.get_current_photo_id()))
        
        # 修正: M
        modify_shortcut = QShortcut(QKeySequence(Qt.Key.Key_M), self)
        modify_shortcut.activated.connect(lambda: self.on_modify(self.get_current_photo_id()))
        
        # スキップ: S
        skip_shortcut = QShortcut(QKeySequence(Qt.Key.Key_S), self)
        skip_shortcut.activated.connect(self.on_skip)
    
    def load_approval_queue(self):
        """
        承認キューを読み込む
        
        Requirements: 9.1 - REST APIエンドポイント統合
        """
        try:
            response = requests.get(f"{self.api_base_url}/approval/queue", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.photos = data.get('photos', [])
                self.current_index = 0
                
                # ヘッダー更新
                count = len(self.photos)
                self.title_label.setText(f"Approval Queue ({count} photos pending)")
                
                # 最初の写真を表示
                if self.photos:
                    self.display_current_photo()
                else:
                    self.clear_display()
                    
        except Exception as e:
            print(f"Failed to load approval queue: {e}")
            self.photos = []
            self.clear_display()
    
    def display_current_photo(self):
        """現在の写真を表示"""
        if not self.photos or self.current_index >= len(self.photos):
            self.clear_display()
            return
        
        photo = self.photos[self.current_index]
        
        # 進捗更新
        self.progress_label.setText(f"Photo {self.current_index + 1} of {len(self.photos)}")
        
        # 写真比較表示
        self.comparison_widget.load_photo(photo)
        
        # AI評価表示
        self.evaluation_widget.update_scores(photo)
        
        # パラメータ表示
        self.parameters_widget.update_parameters(photo)
        
        # アクションボタンに写真IDを設定
        self.actions_widget.set_photo_id(photo.get('id'))
    
    def clear_display(self):
        """表示をクリア"""
        self.progress_label.setText("Photo 0 of 0")
        self.comparison_widget.before_image.setText("No photos in queue")
        self.comparison_widget.after_image.setText("No photos in queue")
    
    def get_current_photo_id(self) -> Optional[int]:
        """現在の写真IDを取得"""
        if self.photos and self.current_index < len(self.photos):
            return self.photos[self.current_index].get('id')
        return None
    
    def previous_photo(self):
        """前の写真に移動"""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_photo()
    
    def next_photo(self):
        """次の写真に移動"""
        if self.current_index < len(self.photos) - 1:
            self.current_index += 1
            self.display_current_photo()
    
    def on_approve(self, photo_id: int):
        """
        写真を承認
        
        Requirements: 5.3 - 承認ボタンをクリックした場合、写真を「書き出し待機」ステータスに移行する
        """
        if not photo_id:
            return
        
        try:
            response = requests.post(
                f"{self.api_base_url}/approval/{photo_id}/approve",
                timeout=5
            )
            
            if response.status_code == 200:
                # 成功メッセージ
                QMessageBox.information(
                    self,
                    "Approved",
                    f"Photo {photo_id} approved successfully!"
                )
                
                # キューから削除して次の写真へ
                self.remove_current_photo()
                self.display_current_photo()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to approve photo: {response.text}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to approve photo: {e}"
            )
    
    def on_reject(self, photo_id: int):
        """
        写真を却下
        
        Requirements: 5.4 - 却下ボタンをクリックした場合、代替プリセットを提案する
        """
        if not photo_id:
            return
        
        # 却下理由を入力（簡易版）
        try:
            response = requests.post(
                f"{self.api_base_url}/approval/{photo_id}/reject",
                json={"reason": "User rejected"},
                timeout=5
            )
            
            if response.status_code == 200:
                # 成功メッセージ
                QMessageBox.information(
                    self,
                    "Rejected",
                    f"Photo {photo_id} rejected. Alternative presets can be suggested."
                )
                
                # キューから削除して次の写真へ
                self.remove_current_photo()
                self.display_current_photo()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to reject photo: {response.text}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to reject photo: {e}"
            )
    
    def on_modify(self, photo_id: int):
        """写真の修正をリクエスト"""
        if not photo_id:
            return
        
        QMessageBox.information(
            self,
            "Modify",
            f"Modification interface for photo {photo_id} will be implemented in future version."
        )
    
    def on_skip(self):
        """現在の写真をスキップ"""
        self.next_photo()
    
    def remove_current_photo(self):
        """現在の写真をキューから削除"""
        if self.photos and self.current_index < len(self.photos):
            self.photos.pop(self.current_index)
            
            # インデックス調整
            if self.current_index >= len(self.photos) and self.current_index > 0:
                self.current_index -= 1
            
            # ヘッダー更新
            count = len(self.photos)
            self.title_label.setText(f"Approval Queue ({count} photos pending)")
