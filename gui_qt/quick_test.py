"""
Quick visual test - shows the window for 3 seconds then closes
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import MainWindow

app = QApplication(sys.argv)

# Load stylesheet
try:
    with open("resources/styles/dark_theme.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
except:
    pass

window = MainWindow()
window.show()

# Close after 3 seconds
QTimer.singleShot(3000, app.quit)

print("✓ GUI window displayed successfully!")
print("✓ Window will close automatically in 3 seconds...")

sys.exit(app.exec())
