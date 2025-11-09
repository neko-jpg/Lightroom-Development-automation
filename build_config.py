#!/usr/bin/env python3
"""
Junmai AutoDev - Build Configuration
Version: 2.0

This module defines the build configuration for PyInstaller packaging.
"""

import os
import sys
import platform
from pathlib import Path

# Application metadata
APP_NAME = "JunmaiAutoDev"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Junmai AutoDev Team"
APP_DESCRIPTION = "Lightroom × LLM 自動現像システム"
APP_COPYRIGHT = "© 2025 Junmai AutoDev Team"

# Build configuration
BUILD_DIR = Path("dist")
WORK_DIR = Path("build")
SPEC_DIR = Path(".")

# Platform-specific settings
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Executable name
if IS_WINDOWS:
    EXE_NAME = f"{APP_NAME}.exe"
elif IS_MACOS:
    EXE_NAME = f"{APP_NAME}.app"
else:
    EXE_NAME = APP_NAME

# Icon paths
if IS_WINDOWS:
    ICON_PATH = "gui_qt/resources/icon.ico"
elif IS_MACOS:
    ICON_PATH = "gui_qt/resources/icon.icns"
else:
    ICON_PATH = None

# Data files to include
DATA_FILES = [
    ('gui_qt/resources', 'resources'),
    ('local_bridge/config', 'config'),
    ('docs', 'docs'),
    ('README.md', '.'),
    ('LICENSE', '.'),
]

# Hidden imports (modules not automatically detected)
HIDDEN_IMPORTS = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    'flask',
    'flask_cors',
    'sqlalchemy',
    'redis',
    'celery',
    'opencv-python',
    'numpy',
    'pillow',
    'requests',
    'websocket',
    'jwt',
    'bcrypt',
    'exifread',
    'piexif',
]

# Excluded modules (to reduce size)
EXCLUDED_MODULES = [
    'matplotlib',
    'scipy',
    'pandas',
    'jupyter',
    'notebook',
    'IPython',
    'tkinter',
]

# Binary excludes
EXCLUDED_BINARIES = [
    'Qt6WebEngine',
    'Qt6WebEngineCore',
    'Qt6WebEngineWidgets',
    'Qt6Pdf',
    'Qt6PdfWidgets',
]

# Runtime hooks
RUNTIME_HOOKS = []

# UPX compression (set to False if causing issues)
USE_UPX = True

# Console mode (False for GUI app)
CONSOLE_MODE = False

# One-file mode (True for single executable)
ONE_FILE = False

# Code signing (Windows)
WINDOWS_SIGN_TOOL = None  # Path to signtool.exe
WINDOWS_CERTIFICATE = None  # Path to certificate

# macOS code signing
MACOS_CODESIGN_IDENTITY = None  # Developer ID
MACOS_ENTITLEMENTS = None  # Path to entitlements file

def get_version_info():
    """Get version info for Windows executable"""
    if not IS_WINDOWS:
        return None
    
    version_parts = APP_VERSION.split('.')
    while len(version_parts) < 4:
        version_parts.append('0')
    
    return {
        'version': '.'.join(version_parts),
        'company_name': APP_AUTHOR,
        'file_description': APP_DESCRIPTION,
        'internal_name': APP_NAME,
        'legal_copyright': APP_COPYRIGHT,
        'original_filename': EXE_NAME,
        'product_name': APP_NAME,
        'product_version': APP_VERSION,
    }

def get_pyinstaller_args():
    """Get PyInstaller command-line arguments"""
    args = [
        '--name', APP_NAME,
        '--clean',
        '--noconfirm',
    ]
    
    # Add icon
    if ICON_PATH and os.path.exists(ICON_PATH):
        args.extend(['--icon', ICON_PATH])
    
    # Console mode
    if not CONSOLE_MODE:
        args.append('--windowed')
    
    # One-file mode
    if ONE_FILE:
        args.append('--onefile')
    else:
        args.append('--onedir')
    
    # UPX compression
    if not USE_UPX:
        args.append('--noupx')
    
    # Hidden imports
    for module in HIDDEN_IMPORTS:
        args.extend(['--hidden-import', module])
    
    # Excluded modules
    for module in EXCLUDED_MODULES:
        args.extend(['--exclude-module', module])
    
    # Data files
    for src, dst in DATA_FILES:
        if os.path.exists(src):
            args.extend(['--add-data', f'{src}{os.pathsep}{dst}'])
    
    # Runtime hooks
    for hook in RUNTIME_HOOKS:
        args.extend(['--runtime-hook', hook])
    
    return args

def print_build_info():
    """Print build configuration information"""
    print("=" * 60)
    print(f"Building {APP_NAME} v{APP_VERSION}")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"Architecture: {platform.machine()}")
    print(f"Build mode: {'One-file' if ONE_FILE else 'One-directory'}")
    print(f"Console: {'Yes' if CONSOLE_MODE else 'No'}")
    print(f"UPX: {'Enabled' if USE_UPX else 'Disabled'}")
    print(f"Output: {BUILD_DIR / EXE_NAME}")
    print("=" * 60)

if __name__ == "__main__":
    print_build_info()
