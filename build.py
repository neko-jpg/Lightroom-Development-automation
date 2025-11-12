# build.py - PyInstaller build script for Junmai AutoDev
#
# This script packages the entire Python application into a single executable
# for Windows and a macOS app bundle. It handles hidden imports, data files,
# and platform-specific options.
#
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__

# --- Configuration ---
APP_NAME = "JunmaiAutoDev"
ENTRY_POINT = "main.py"

# Directories
REPO_ROOT = Path(__file__).resolve().parent
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = REPO_ROOT / "build"
ICON_DIR = REPO_ROOT / "gui_qt" / "resources" / "icons"


def get_platform_specific_opts() -> list[str]:
    """Return platform-specific options for PyInstaller."""
    if platform.system() == "Windows":
        return [
            "--windowed",  # No console window
            f"--icon={ICON_DIR / 'app_icon.ico'}",
        ]
    if platform.system() == "Darwin":  # macOS
        return [
            "--windowed",  # App bundle without a terminal
            f"--icon={ICON_DIR / 'app_icon.icns'}",
            # Other macOS-specific options can be added here
        ]
    return []


def get_pyinstaller_opts() -> list[str]:
    """Assemble the full list of PyInstaller options."""
    opts = [
        "--noconfirm",
        "--onefile",
        f"--name={APP_NAME}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        # Hidden imports are crucial for modules that are not explicitly
        # imported in a way that PyInstaller's static analysis can detect.
        # Our main.py uses lazy imports, so we must specify them here.
        "--hidden-import=local_bridge",
        "--hidden-import=gui_qt",
        # Add data files (e.g., icons, stylesheets) so they are
        # included in the final executable.
        f"--add-data={REPO_ROOT / 'gui_qt' / 'resources'}:gui_qt/resources",
    ]
    opts.extend(get_platform_specific_opts())
    return opts


def main() -> int:
    """Clean up previous builds and run PyInstaller."""
    print("--- Starting Junmai AutoDev Build ---")
    
    # 1. Clean up previous build artifacts
    print("1. Cleaning up previous build artifacts...")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    # 2. Assemble PyInstaller command
    command = [ENTRY_POINT]
    command.extend(get_pyinstaller_opts())

    print(f"2. Running PyInstaller with command:\npyinstaller {' '.join(command)}")

    # 3. Run PyInstaller
    try:
        PyInstaller.__main__.run(command)
        print("\n3. PyInstaller build completed successfully!")
    except Exception as e:
        print(f"\n3. PyInstaller build failed: {e}", file=sys.stderr)
        return 1

    # 4. Final verification
    print("4. Verifying build output...")
    output_path = DIST_DIR / APP_NAME
    if platform.system() == "Windows":
        output_path = output_path.with_suffix(".exe")

    if output_path.exists():
        print(f"   Success! Executable created at: {output_path}")
        print("--- Build Finished ---")
        return 0
    else:
        print(f"   Error! Expected executable not found at: {output_path}", file=sys.stderr)
        print("--- Build Finished with Errors ---")
        return 1


if __name__ == "__main__":
    sys.exit(main())
