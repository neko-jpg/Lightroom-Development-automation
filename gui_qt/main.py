"""
Junmai AutoDev - Desktop GUI Application Entry Point
アプリケーションのエントリー・ポイント

Requirements: Desktop GUI with Guided Flow experience.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from main_window import MainWindow

DEFAULT_THEME = "dark"


def resource_path(*parts: str) -> Path:
    base_dir = Path(__file__).resolve().parent
    return base_dir.joinpath(*parts)


def load_stylesheet(theme: str = DEFAULT_THEME) -> str:
    """
    Load the requested stylesheet.

    Args:
        theme: "dark" or "light"
    """

    stylesheet_path = resource_path("resources", "styles", f"{theme}_theme.qss")

    try:
        return stylesheet_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Warning: Stylesheet not found: {stylesheet_path}")
        return ""


def configure_application(app: QApplication, theme: str = DEFAULT_THEME) -> None:
    """Applies shared configuration to the QApplication instance."""
    app.setApplicationName("Junmai AutoDev")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Junmai AutoDev")

    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    stylesheet = load_stylesheet(theme)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    icon_path = resource_path("resources", "icons", "app_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))


def create_application(theme: str = DEFAULT_THEME) -> QApplication:
    """Initializes QApplication with shared configuration."""
    app = QApplication(sys.argv)
    configure_application(app, theme=theme)
    return app


def launch(theme: str = DEFAULT_THEME, guided_mode: bool = True) -> int:
    """
    Launch the Junmai AutoDev desktop application.

    Args:
        theme: Which stylesheet to apply ("dark" or "light").
        guided_mode: If True, show the simplified Guided Flow tab by default.
    """
    app = create_application(theme=theme)
    window = MainWindow(guided_mode=guided_mode)
    window.show()
    return app.exec()


def main() -> int:
    """Maintains backwards compatibility with python gui_qt/main.py."""
    return launch()


if __name__ == "__main__":
    raise SystemExit(main())
