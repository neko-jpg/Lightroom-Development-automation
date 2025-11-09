"""
Test Settings Widgets
設定ウィジェットのテスト

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from widgets.settings_widgets import (
    SettingsWidget,
    HotFolderSettingsWidget,
    AISettingsWidget,
    ProcessingSettingsWidget,
    NotificationSettingsWidget,
    UISettingsWidget
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit the app as it might be used by other tests


class TestHotFolderSettingsWidget:
    """Test HotFolderSettingsWidget"""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created"""
        widget = HotFolderSettingsWidget()
        assert widget is not None
        assert widget.title() == "Hot Folders"
    
    def test_add_folder(self, qapp):
        """Test adding a folder to the list"""
        widget = HotFolderSettingsWidget()
        
        # Manually add a folder (simulating dialog result)
        test_folder = "D:/Photos/Test"
        widget.folder_list.addItem(test_folder)
        
        assert widget.folder_list.count() == 1
        assert widget.folder_list.item(0).text() == test_folder
    
    def test_remove_folder(self, qapp):
        """Test removing a folder from the list"""
        widget = HotFolderSettingsWidget()
        
        # Add folders
        widget.folder_list.addItem("D:/Photos/Test1")
        widget.folder_list.addItem("D:/Photos/Test2")
        
        # Select and remove first folder
        widget.folder_list.setCurrentRow(0)
        widget.remove_folder()
        
        assert widget.folder_list.count() == 1
        assert widget.folder_list.item(0).text() == "D:/Photos/Test2"
    
    def test_set_and_get_config(self, qapp):
        """Test setting and getting configuration"""
        widget = HotFolderSettingsWidget()
        
        test_config = {
            'hot_folders': ['D:/Photos/Inbox', 'E:/SD_Card'],
            'lightroom_catalog': 'D:/Lightroom/Catalog.lrcat',
            'temp_folder': 'C:/Temp/Test',
            'log_level': 'DEBUG'
        }
        
        widget.set_config(test_config)
        
        # Verify folders were added
        assert widget.folder_list.count() == 2
        
        # Verify other fields
        assert widget.catalog_edit.text() == test_config['lightroom_catalog']
        assert widget.temp_edit.text() == test_config['temp_folder']
        assert widget.log_level_combo.currentText() == test_config['log_level']
        
        # Get config back
        retrieved_config = widget.get_config()
        assert retrieved_config == test_config


class TestAISettingsWidget:
    """Test AISettingsWidget"""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created"""
        widget = AISettingsWidget()
        assert widget is not None
        assert widget.title() == "AI Configuration"
    
    def test_set_and_get_config(self, qapp):
        """Test setting and getting configuration"""
        widget = AISettingsWidget()
        
        test_config = {
            'llm_provider': 'ollama',
            'llm_model': 'llama3.1:8b-instruct',
            'ollama_host': 'http://localhost:11434',
            'gpu_memory_limit_mb': 6144,
            'enable_quantization': True,
            'selection_threshold': 4.0
        }
        
        widget.set_config(test_config)
        
        # Verify fields
        assert widget.provider_combo.currentText() == test_config['llm_provider']
        assert widget.model_edit.text() == test_config['llm_model']
        assert widget.host_edit.text() == test_config['ollama_host']
        assert widget.gpu_memory_spin.value() == test_config['gpu_memory_limit_mb']
        assert widget.quantization_check.isChecked() == test_config['enable_quantization']
        assert widget.threshold_spin.value() == test_config['selection_threshold']
        
        # Get config back
        retrieved_config = widget.get_config()
        assert retrieved_config == test_config


class TestProcessingSettingsWidget:
    """Test ProcessingSettingsWidget"""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created"""
        widget = ProcessingSettingsWidget()
        assert widget is not None
        assert widget.title() == "Processing"
    
    def test_set_and_get_config(self, qapp):
        """Test setting and getting configuration"""
        widget = ProcessingSettingsWidget()
        
        test_config = {
            'auto_import': True,
            'auto_select': True,
            'auto_develop': False,
            'auto_export': False,
            'max_concurrent_jobs': 5,
            'cpu_limit_percent': 70,
            'gpu_temp_limit_celsius': 80
        }
        
        widget.set_config(test_config)
        
        # Verify checkboxes
        assert widget.auto_import_check.isChecked() == test_config['auto_import']
        assert widget.auto_select_check.isChecked() == test_config['auto_select']
        assert widget.auto_develop_check.isChecked() == test_config['auto_develop']
        assert widget.auto_export_check.isChecked() == test_config['auto_export']
        
        # Verify spinboxes
        assert widget.max_jobs_spin.value() == test_config['max_concurrent_jobs']
        assert widget.cpu_limit_spin.value() == test_config['cpu_limit_percent']
        assert widget.gpu_temp_spin.value() == test_config['gpu_temp_limit_celsius']
        
        # Get config back
        retrieved_config = widget.get_config()
        assert retrieved_config == test_config


class TestNotificationSettingsWidget:
    """Test NotificationSettingsWidget"""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created"""
        widget = NotificationSettingsWidget()
        assert widget is not None
        assert widget.title() == "Notifications"
    
    def test_set_and_get_config(self, qapp):
        """Test setting and getting configuration"""
        widget = NotificationSettingsWidget()
        
        test_config = {
            'desktop': True,
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.test.com',
                'smtp_port': 587,
                'use_tls': True,
                'from_address': 'test@example.com',
                'to_address': 'user@example.com'
            },
            'line': {
                'enabled': False,
                'token': 'test_token_123'
            }
        }
        
        widget.set_config(test_config)
        
        # Verify desktop
        assert widget.desktop_check.isChecked() == test_config['desktop']
        
        # Verify email
        assert widget.email_enabled_check.isChecked() == test_config['email']['enabled']
        assert widget.smtp_server_edit.text() == test_config['email']['smtp_server']
        assert widget.smtp_port_spin.value() == test_config['email']['smtp_port']
        assert widget.use_tls_check.isChecked() == test_config['email']['use_tls']
        assert widget.from_email_edit.text() == test_config['email']['from_address']
        assert widget.to_email_edit.text() == test_config['email']['to_address']
        
        # Verify LINE
        assert widget.line_enabled_check.isChecked() == test_config['line']['enabled']
        assert widget.line_token_edit.text() == test_config['line']['token']
        
        # Get config back
        retrieved_config = widget.get_config()
        assert retrieved_config == test_config


class TestUISettingsWidget:
    """Test UISettingsWidget"""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created"""
        widget = UISettingsWidget()
        assert widget is not None
        assert widget.title() == "User Interface"
    
    def test_set_and_get_config(self, qapp):
        """Test setting and getting configuration"""
        widget = UISettingsWidget()
        
        test_config = {
            'theme': 'dark',
            'language': 'ja',
            'show_advanced_settings': True
        }
        
        widget.set_config(test_config)
        
        # Verify fields
        assert widget.theme_combo.currentText() == test_config['theme']
        assert widget.language_combo.currentText() == test_config['language']
        assert widget.advanced_check.isChecked() == test_config['show_advanced_settings']
        
        # Get config back
        retrieved_config = widget.get_config()
        assert retrieved_config == test_config


class TestSettingsWidget:
    """Test main SettingsWidget"""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created"""
        widget = SettingsWidget()
        assert widget is not None
    
    def test_has_all_sub_widgets(self, qapp):
        """Test that all sub-widgets are present"""
        widget = SettingsWidget()
        
        assert hasattr(widget, 'hotfolder_widget')
        assert hasattr(widget, 'ai_widget')
        assert hasattr(widget, 'processing_widget')
        assert hasattr(widget, 'notification_widget')
        assert hasattr(widget, 'ui_widget')
        
        assert isinstance(widget.hotfolder_widget, HotFolderSettingsWidget)
        assert isinstance(widget.ai_widget, AISettingsWidget)
        assert isinstance(widget.processing_widget, ProcessingSettingsWidget)
        assert isinstance(widget.notification_widget, NotificationSettingsWidget)
        assert isinstance(widget.ui_widget, UISettingsWidget)
    
    def test_has_buttons(self, qapp):
        """Test that all buttons are present"""
        widget = SettingsWidget()
        
        assert hasattr(widget, 'save_btn')
        assert hasattr(widget, 'cancel_btn')
        assert hasattr(widget, 'reset_btn')
        
        assert widget.save_btn.text() == "Save"
        assert widget.cancel_btn.text() == "Cancel"
        assert widget.reset_btn.text() == "Reset to Default"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
