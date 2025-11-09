"""
Visual Test for Settings Widget
設定ウィジェットの視覚的テスト

Run this to see the settings interface in action.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow
from widgets.settings_widgets import SettingsWidget


def main():
    """Main function to display settings widget"""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Junmai AutoDev - Settings Test")
    window.setGeometry(100, 100, 800, 600)
    
    # Create settings widget
    settings = SettingsWidget(api_base_url="http://localhost:5100")
    
    # Connect signal
    settings.settings_saved.connect(lambda: print("Settings saved!"))
    
    # Set as central widget
    window.setCentralWidget(settings)
    
    # Show window
    window.show()
    
    print("Settings widget displayed. Close window to exit.")
    print("Note: API connection may fail if server is not running.")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
