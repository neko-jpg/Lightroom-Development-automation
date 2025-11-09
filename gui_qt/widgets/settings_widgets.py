"""
Settings Widgets for Junmai AutoDev GUI
設定画面用ウィジェット群

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QListWidget, QListWidgetItem,
    QFileDialog, QGroupBox, QScrollArea, QTabWidget,
    QMessageBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any, List
import requests
import pathlib


class SettingsWidget(QWidget):
    """
    メイン設定ウィジェット
    
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
    - ホットフォルダー管理
    - AI設定
    - 処理設定
    - 通知設定
    - 設定の保存・読み込み
    """
    
    settings_saved = pyqtSignal()
    
    def __init__(self, api_base_url: str = "http://localhost:5100", parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url
        self.config = {}
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # タイトル
        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # コンテンツウィジェット
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        # 各設定セクション
        self.hotfolder_widget = HotFolderSettingsWidget()
        content_layout.addWidget(self.hotfolder_widget)
        
        self.ai_widget = AISettingsWidget()
        content_layout.addWidget(self.ai_widget)
        
        self.processing_widget = ProcessingSettingsWidget()
        content_layout.addWidget(self.processing_widget)
        
        self.notification_widget = NotificationSettingsWidget()
        content_layout.addWidget(self.notification_widget)
        
        self.ui_widget = UISettingsWidget()
        content_layout.addWidget(self.ui_widget)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(self.reset_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.load_config)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_config(self):
        """設定を読み込み"""
        try:
            response = requests.get(f"{self.api_base_url}/config", timeout=5)
            if response.status_code == 200:
                self.config = response.json()
                self.apply_config_to_ui()
            else:
                QMessageBox.warning(
                    self,
                    "Load Error",
                    f"Failed to load configuration: {response.status_code}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to server: {str(e)}"
            )
    
    def save_config(self):
        """設定を保存"""
        # UIから設定を収集
        self.collect_config_from_ui()
        
        try:
            response = requests.post(
                f"{self.api_base_url}/config",
                json=self.config,
                timeout=5
            )
            if response.status_code == 200:
                QMessageBox.information(
                    self,
                    "Success",
                    "Configuration saved successfully!"
                )
                self.settings_saved.emit()
            else:
                error_msg = response.json().get('error', 'Unknown error')
                QMessageBox.warning(
                    self,
                    "Save Error",
                    f"Failed to save configuration: {error_msg}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to server: {str(e)}"
            )
    
    def reset_to_default(self):
        """デフォルト設定にリセット"""
        reply = QMessageBox.question(
            self,
            "Reset to Default",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                response = requests.post(
                    f"{self.api_base_url}/config/reset",
                    timeout=5
                )
                if response.status_code == 200:
                    self.load_config()
                    QMessageBox.information(
                        self,
                        "Success",
                        "Configuration reset to default values!"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Reset Error",
                        "Failed to reset configuration"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Connection Error",
                    f"Failed to connect to server: {str(e)}"
                )
    
    def apply_config_to_ui(self):
        """設定をUIに適用"""
        self.hotfolder_widget.set_config(self.config.get('system', {}))
        self.ai_widget.set_config(self.config.get('ai', {}))
        self.processing_widget.set_config(self.config.get('processing', {}))
        self.notification_widget.set_config(self.config.get('notifications', {}))
        self.ui_widget.set_config(self.config.get('ui', {}))
    
    def collect_config_from_ui(self):
        """UIから設定を収集"""
        self.config['system'] = self.hotfolder_widget.get_config()
        self.config['ai'] = self.ai_widget.get_config()
        self.config['processing'] = self.processing_widget.get_config()
        self.config['notifications'] = self.notification_widget.get_config()
        self.config['ui'] = self.ui_widget.get_config()


class HotFolderSettingsWidget(QGroupBox):
    """
    ホットフォルダー管理ウィジェット
    
    Requirements: 8.2
    """
    
    def __init__(self, parent=None):
        super().__init__("Hot Folders", parent)
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        
        # 説明
        desc = QLabel("Folders to monitor for new photos (automatic import)")
        desc.setStyleSheet("color: #888;")
        layout.addWidget(desc)
        
        # フォルダーリスト
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(150)
        layout.addWidget(self.folder_list)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Folder")
        self.add_btn.clicked.connect(self.add_folder)
        button_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_folder)
        button_layout.addWidget(self.remove_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Lightroomカタログパス
        catalog_layout = QFormLayout()
        
        self.catalog_edit = QLineEdit()
        catalog_browse_btn = QPushButton("Browse")
        catalog_browse_btn.clicked.connect(self.browse_catalog)
        
        catalog_row = QHBoxLayout()
        catalog_row.addWidget(self.catalog_edit, 1)
        catalog_row.addWidget(catalog_browse_btn)
        
        catalog_layout.addRow("Lightroom Catalog:", catalog_row)
        
        # 一時フォルダー
        self.temp_edit = QLineEdit()
        temp_browse_btn = QPushButton("Browse")
        temp_browse_btn.clicked.connect(self.browse_temp)
        
        temp_row = QHBoxLayout()
        temp_row.addWidget(self.temp_edit, 1)
        temp_row.addWidget(temp_browse_btn)
        
        catalog_layout.addRow("Temp Folder:", temp_row)
        
        # ログレベル
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        catalog_layout.addRow("Log Level:", self.log_level_combo)
        
        layout.addLayout(catalog_layout)
    
    def add_folder(self):
        """フォルダーを追加"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Hot Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            # 重複チェック
            for i in range(self.folder_list.count()):
                if self.folder_list.item(i).text() == folder:
                    QMessageBox.warning(
                        self,
                        "Duplicate",
                        "This folder is already in the list"
                    )
                    return
            
            self.folder_list.addItem(folder)
    
    def remove_folder(self):
        """選択されたフォルダーを削除"""
        current_item = self.folder_list.currentItem()
        if current_item:
            self.folder_list.takeItem(self.folder_list.row(current_item))
    
    def browse_catalog(self):
        """Lightroomカタログを選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Lightroom Catalog",
            "",
            "Lightroom Catalog (*.lrcat);;All Files (*.*)"
        )
        if file_path:
            self.catalog_edit.setText(file_path)
    
    def browse_temp(self):
        """一時フォルダーを選択"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Temp Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.temp_edit.setText(folder)
    
    def set_config(self, config: Dict[str, Any]):
        """設定を適用"""
        # ホットフォルダー
        self.folder_list.clear()
        for folder in config.get('hot_folders', []):
            self.folder_list.addItem(folder)
        
        # Lightroomカタログ
        self.catalog_edit.setText(config.get('lightroom_catalog', ''))
        
        # 一時フォルダー
        self.temp_edit.setText(config.get('temp_folder', 'C:/Temp/JunmaiAutoDev'))
        
        # ログレベル
        log_level = config.get('log_level', 'INFO')
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
    
    def get_config(self) -> Dict[str, Any]:
        """設定を取得"""
        folders = []
        for i in range(self.folder_list.count()):
            folders.append(self.folder_list.item(i).text())
        
        return {
            'hot_folders': folders,
            'lightroom_catalog': self.catalog_edit.text(),
            'temp_folder': self.temp_edit.text(),
            'log_level': self.log_level_combo.currentText()
        }


class AISettingsWidget(QGroupBox):
    """
    AI設定ウィジェット
    
    Requirements: 8.3
    """
    
    def __init__(self, parent=None):
        super().__init__("AI Configuration", parent)
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QFormLayout(self)
        
        # LLMプロバイダー
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama", "lm_studio", "llama_cpp"])
        layout.addRow("LLM Provider:", self.provider_combo)
        
        # LLMモデル
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g., llama3.1:8b-instruct")
        layout.addRow("Model:", self.model_edit)
        
        # Ollamaホスト
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("http://localhost:11434")
        layout.addRow("Ollama Host:", self.host_edit)
        
        # GPUメモリ制限
        self.gpu_memory_spin = QSpinBox()
        self.gpu_memory_spin.setRange(1024, 24576)
        self.gpu_memory_spin.setSingleStep(512)
        self.gpu_memory_spin.setSuffix(" MB")
        layout.addRow("GPU Memory Limit:", self.gpu_memory_spin)
        
        # 量子化
        self.quantization_check = QCheckBox("Enable Quantization (4-bit/8-bit)")
        layout.addRow("", self.quantization_check)
        
        # 選別閾値
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(1.0, 5.0)
        self.threshold_spin.setSingleStep(0.1)
        self.threshold_spin.setDecimals(1)
        self.threshold_spin.setSuffix(" ★")
        layout.addRow("Selection Threshold:", self.threshold_spin)
        
        # 説明
        desc = QLabel("Photos with AI score above threshold will be auto-selected")
        desc.setStyleSheet("color: #888; font-size: 10px;")
        layout.addRow("", desc)
    
    def set_config(self, config: Dict[str, Any]):
        """設定を適用"""
        # プロバイダー
        provider = config.get('llm_provider', 'ollama')
        index = self.provider_combo.findText(provider)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)
        
        # モデル
        self.model_edit.setText(config.get('llm_model', 'llama3.1:8b-instruct'))
        
        # ホスト
        self.host_edit.setText(config.get('ollama_host', 'http://localhost:11434'))
        
        # GPUメモリ
        self.gpu_memory_spin.setValue(config.get('gpu_memory_limit_mb', 6144))
        
        # 量子化
        self.quantization_check.setChecked(config.get('enable_quantization', False))
        
        # 閾値
        self.threshold_spin.setValue(config.get('selection_threshold', 3.5))
    
    def get_config(self) -> Dict[str, Any]:
        """設定を取得"""
        return {
            'llm_provider': self.provider_combo.currentText(),
            'llm_model': self.model_edit.text(),
            'ollama_host': self.host_edit.text(),
            'gpu_memory_limit_mb': self.gpu_memory_spin.value(),
            'enable_quantization': self.quantization_check.isChecked(),
            'selection_threshold': self.threshold_spin.value()
        }


class ProcessingSettingsWidget(QGroupBox):
    """
    処理設定ウィジェット
    
    Requirements: 8.4
    """
    
    def __init__(self, parent=None):
        super().__init__("Processing", parent)
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        
        # 自動処理オプション
        self.auto_import_check = QCheckBox("Auto Import")
        self.auto_import_check.setToolTip("Automatically import detected photos")
        layout.addWidget(self.auto_import_check)
        
        self.auto_select_check = QCheckBox("Auto Select")
        self.auto_select_check.setToolTip("Automatically select photos based on AI evaluation")
        layout.addWidget(self.auto_select_check)
        
        self.auto_develop_check = QCheckBox("Auto Develop")
        self.auto_develop_check.setToolTip("Automatically develop selected photos")
        layout.addWidget(self.auto_develop_check)
        
        self.auto_export_check = QCheckBox("Auto Export")
        self.auto_export_check.setToolTip("Automatically export developed photos")
        layout.addWidget(self.auto_export_check)
        
        # リソース制限
        form_layout = QFormLayout()
        
        self.max_jobs_spin = QSpinBox()
        self.max_jobs_spin.setRange(1, 10)
        form_layout.addRow("Max Concurrent Jobs:", self.max_jobs_spin)
        
        self.cpu_limit_spin = QSpinBox()
        self.cpu_limit_spin.setRange(10, 100)
        self.cpu_limit_spin.setSingleStep(5)
        self.cpu_limit_spin.setSuffix(" %")
        form_layout.addRow("CPU Limit:", self.cpu_limit_spin)
        
        self.gpu_temp_spin = QSpinBox()
        self.gpu_temp_spin.setRange(60, 90)
        self.gpu_temp_spin.setSuffix(" °C")
        form_layout.addRow("GPU Temp Limit:", self.gpu_temp_spin)
        
        layout.addLayout(form_layout)
        
        # 説明
        desc = QLabel("Processing will slow down or pause when limits are reached")
        desc.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(desc)
    
    def set_config(self, config: Dict[str, Any]):
        """設定を適用"""
        self.auto_import_check.setChecked(config.get('auto_import', True))
        self.auto_select_check.setChecked(config.get('auto_select', True))
        self.auto_develop_check.setChecked(config.get('auto_develop', True))
        self.auto_export_check.setChecked(config.get('auto_export', False))
        
        self.max_jobs_spin.setValue(config.get('max_concurrent_jobs', 3))
        self.cpu_limit_spin.setValue(config.get('cpu_limit_percent', 80))
        self.gpu_temp_spin.setValue(config.get('gpu_temp_limit_celsius', 75))
    
    def get_config(self) -> Dict[str, Any]:
        """設定を取得"""
        return {
            'auto_import': self.auto_import_check.isChecked(),
            'auto_select': self.auto_select_check.isChecked(),
            'auto_develop': self.auto_develop_check.isChecked(),
            'auto_export': self.auto_export_check.isChecked(),
            'max_concurrent_jobs': self.max_jobs_spin.value(),
            'cpu_limit_percent': self.cpu_limit_spin.value(),
            'gpu_temp_limit_celsius': self.gpu_temp_spin.value()
        }


class NotificationSettingsWidget(QGroupBox):
    """
    通知設定ウィジェット
    
    Requirements: 8.5
    """
    
    def __init__(self, parent=None):
        super().__init__("Notifications", parent)
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        
        # デスクトップ通知
        self.desktop_check = QCheckBox("Desktop Notifications")
        layout.addWidget(self.desktop_check)
        
        # メール通知
        email_group = QGroupBox("Email Notifications")
        email_layout = QFormLayout(email_group)
        
        self.email_enabled_check = QCheckBox("Enable Email")
        email_layout.addRow("", self.email_enabled_check)
        
        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText("smtp.gmail.com")
        email_layout.addRow("SMTP Server:", self.smtp_server_edit)
        
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        email_layout.addRow("SMTP Port:", self.smtp_port_spin)
        
        self.use_tls_check = QCheckBox("Use TLS")
        email_layout.addRow("", self.use_tls_check)
        
        self.from_email_edit = QLineEdit()
        self.from_email_edit.setPlaceholderText("your-email@example.com")
        email_layout.addRow("From Address:", self.from_email_edit)
        
        self.to_email_edit = QLineEdit()
        self.to_email_edit.setPlaceholderText("recipient@example.com")
        email_layout.addRow("To Address:", self.to_email_edit)
        
        layout.addWidget(email_group)
        
        # LINE通知
        line_group = QGroupBox("LINE Notify")
        line_layout = QFormLayout(line_group)
        
        self.line_enabled_check = QCheckBox("Enable LINE Notify")
        line_layout.addRow("", self.line_enabled_check)
        
        self.line_token_edit = QLineEdit()
        self.line_token_edit.setPlaceholderText("Your LINE Notify token")
        self.line_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        line_layout.addRow("Token:", self.line_token_edit)
        
        layout.addWidget(line_group)
    
    def set_config(self, config: Dict[str, Any]):
        """設定を適用"""
        # デスクトップ
        self.desktop_check.setChecked(config.get('desktop', True))
        
        # メール
        email_config = config.get('email', {})
        self.email_enabled_check.setChecked(email_config.get('enabled', False))
        self.smtp_server_edit.setText(email_config.get('smtp_server', 'smtp.gmail.com'))
        self.smtp_port_spin.setValue(email_config.get('smtp_port', 587))
        self.use_tls_check.setChecked(email_config.get('use_tls', True))
        self.from_email_edit.setText(email_config.get('from_address', ''))
        self.to_email_edit.setText(email_config.get('to_address', ''))
        
        # LINE
        line_config = config.get('line', {})
        self.line_enabled_check.setChecked(line_config.get('enabled', False))
        self.line_token_edit.setText(line_config.get('token', ''))
    
    def get_config(self) -> Dict[str, Any]:
        """設定を取得"""
        return {
            'desktop': self.desktop_check.isChecked(),
            'email': {
                'enabled': self.email_enabled_check.isChecked(),
                'smtp_server': self.smtp_server_edit.text(),
                'smtp_port': self.smtp_port_spin.value(),
                'use_tls': self.use_tls_check.isChecked(),
                'from_address': self.from_email_edit.text(),
                'to_address': self.to_email_edit.text()
            },
            'line': {
                'enabled': self.line_enabled_check.isChecked(),
                'token': self.line_token_edit.text()
            }
        }


class UISettingsWidget(QGroupBox):
    """
    UI設定ウィジェット
    
    Requirements: 8.1
    """
    
    def __init__(self, parent=None):
        super().__init__("User Interface", parent)
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QFormLayout(self)
        
        # テーマ
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "auto"])
        layout.addRow("Theme:", self.theme_combo)
        
        # 言語
        self.language_combo = QComboBox()
        self.language_combo.addItems(["ja", "en"])
        layout.addRow("Language:", self.language_combo)
        
        # 高度な設定表示
        self.advanced_check = QCheckBox("Show Advanced Settings")
        layout.addRow("", self.advanced_check)
    
    def set_config(self, config: Dict[str, Any]):
        """設定を適用"""
        # テーマ
        theme = config.get('theme', 'dark')
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # 言語
        language = config.get('language', 'ja')
        index = self.language_combo.findText(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # 高度な設定
        self.advanced_check.setChecked(config.get('show_advanced_settings', False))
    
    def get_config(self) -> Dict[str, Any]:
        """設定を取得"""
        return {
            'theme': self.theme_combo.currentText(),
            'language': self.language_combo.currentText(),
            'show_advanced_settings': self.advanced_check.isChecked()
        }
