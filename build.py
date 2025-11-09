#!/usr/bin/env python3
"""
Junmai AutoDev - Build Script
Version: 2.0

This script builds the application using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
import build_config

def clean_build_dirs():
    """Clean build and dist directories"""
    print("Cleaning build directories...")
    
    dirs_to_clean = [build_config.BUILD_DIR, build_config.WORK_DIR]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")
    
    print("✓ Build directories cleaned")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = ['PyInstaller', 'PyQt6']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ✗ {package} (missing)")
    
    if missing_packages:
        print(f"\nError: Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("✓ All dependencies installed")
    return True

def create_spec_file():
    """Create PyInstaller spec file"""
    print("Creating spec file...")
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect data files
datas = []
"""
    
    # Add data files
    for src, dst in build_config.DATA_FILES:
        if os.path.exists(src):
            spec_content += f"datas.append(('{src}', '{dst}'))\n"
    
    spec_content += f"""
# Hidden imports
hiddenimports = {build_config.HIDDEN_IMPORTS}

# Analysis
a = Analysis(
    ['gui_qt/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks={build_config.RUNTIME_HOOKS},
    excludes={build_config.EXCLUDED_MODULES},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove excluded binaries
for binary in {build_config.EXCLUDED_BINARIES}:
    a.binaries = [x for x in a.binaries if not x[0].startswith(binary)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

"""
    
    if build_config.ONE_FILE:
        spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{build_config.APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={build_config.USE_UPX},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={build_config.CONSOLE_MODE},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
"""
        
        if build_config.ICON_PATH and os.path.exists(build_config.ICON_PATH):
            spec_content += f"    icon='{build_config.ICON_PATH}',\n"
        
        spec_content += ")\n"
    
    else:
        spec_content += f"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{build_config.APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={build_config.USE_UPX},
    console={build_config.CONSOLE_MODE},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
"""
        
        if build_config.ICON_PATH and os.path.exists(build_config.ICON_PATH):
            spec_content += f"    icon='{build_config.ICON_PATH}',\n"
        
        spec_content += f""")

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx={build_config.USE_UPX},
    upx_exclude=[],
    name='{build_config.APP_NAME}',
)
"""
    
    # Add macOS app bundle
    if build_config.IS_MACOS:
        spec_content += f"""
app = BUNDLE(
    coll,
    name='{build_config.APP_NAME}.app',
    icon='{build_config.ICON_PATH}' if os.path.exists('{build_config.ICON_PATH}') else None,
    bundle_identifier='com.junmai.autodev',
    info_plist={{
        'CFBundleName': '{build_config.APP_NAME}',
        'CFBundleDisplayName': '{build_config.APP_NAME}',
        'CFBundleVersion': '{build_config.APP_VERSION}',
        'CFBundleShortVersionString': '{build_config.APP_VERSION}',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '12.0',
    }},
)
"""
    
    spec_file = Path(f"{build_config.APP_NAME}.spec")
    spec_file.write_text(spec_content)
    
    print(f"✓ Spec file created: {spec_file}")
    return spec_file

def run_pyinstaller(spec_file):
    """Run PyInstaller with the spec file"""
    print("Running PyInstaller...")
    
    cmd = ['pyinstaller', str(spec_file), '--clean', '--noconfirm']
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✓ PyInstaller completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller failed:")
        print(e.stdout)
        print(e.stderr)
        return False

def copy_additional_files():
    """Copy additional files to dist directory"""
    print("Copying additional files...")
    
    dist_dir = build_config.BUILD_DIR / build_config.APP_NAME
    
    # Copy configuration templates
    config_src = Path("local_bridge/config")
    if config_src.exists():
        config_dst = dist_dir / "config"
        if not config_dst.exists():
            shutil.copytree(config_src, config_dst)
            print(f"  ✓ Copied: config")
    
    # Copy Lightroom plugin
    plugin_src = Path("JunmaiAutoDev.lrdevplugin")
    if plugin_src.exists():
        plugin_dst = dist_dir / "plugins" / "JunmaiAutoDev.lrdevplugin"
        plugin_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plugin_src, plugin_dst)
        print(f"  ✓ Copied: Lightroom plugin")
    
    # Copy startup scripts
    if build_config.IS_WINDOWS:
        startup_script = Path("start.ps1")
        if startup_script.exists():
            shutil.copy(startup_script, dist_dir / "start.ps1")
            print(f"  ✓ Copied: start.ps1")
    else:
        startup_script = Path("start.sh")
        if startup_script.exists():
            shutil.copy(startup_script, dist_dir / "start.sh")
            os.chmod(dist_dir / "start.sh", 0o755)
            print(f"  ✓ Copied: start.sh")
    
    # Create data directories
    for dir_name in ['data', 'logs', 'data/cache', 'data/backups']:
        dir_path = dist_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("✓ Additional files copied")

def create_version_file():
    """Create version file for auto-update"""
    print("Creating version file...")
    
    import json
    
    version_info = {
        "version": build_config.APP_VERSION,
        "build_date": __import__('datetime').datetime.now().isoformat(),
        "platform": sys.platform,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    
    dist_dir = build_config.BUILD_DIR / build_config.APP_NAME
    version_file = dist_dir / "version.json"
    
    with open(version_file, 'w') as f:
        json.dump(version_info, f, indent=2)
    
    print(f"✓ Version file created: {version_file}")

def sign_executable():
    """Sign the executable (Windows/macOS)"""
    if build_config.IS_WINDOWS and build_config.WINDOWS_SIGN_TOOL:
        print("Signing Windows executable...")
        # Implement Windows code signing
        print("  (Code signing not configured)")
    
    elif build_config.IS_MACOS and build_config.MACOS_CODESIGN_IDENTITY:
        print("Signing macOS application...")
        # Implement macOS code signing
        print("  (Code signing not configured)")
    
    else:
        print("Skipping code signing (not configured)")

def create_archive():
    """Create distribution archive"""
    print("Creating distribution archive...")
    
    dist_dir = build_config.BUILD_DIR / build_config.APP_NAME
    
    if not dist_dir.exists():
        print("  ✗ Distribution directory not found")
        return False
    
    # Determine archive format
    if build_config.IS_WINDOWS:
        archive_format = 'zip'
        archive_ext = 'zip'
    else:
        archive_format = 'gztar'
        archive_ext = 'tar.gz'
    
    archive_name = f"{build_config.APP_NAME}-{build_config.APP_VERSION}-{sys.platform}"
    archive_path = build_config.BUILD_DIR / archive_name
    
    shutil.make_archive(str(archive_path), archive_format, build_config.BUILD_DIR, build_config.APP_NAME)
    
    final_archive = Path(f"{archive_path}.{archive_ext}")
    print(f"✓ Archive created: {final_archive}")
    print(f"  Size: {final_archive.stat().st_size / (1024*1024):.2f} MB")
    
    return True

def main():
    """Main build function"""
    parser = argparse.ArgumentParser(description='Build Junmai AutoDev')
    parser.add_argument('--clean', action='store_true', help='Clean build directories before building')
    parser.add_argument('--no-archive', action='store_true', help='Skip creating distribution archive')
    parser.add_argument('--sign', action='store_true', help='Sign the executable')
    
    args = parser.parse_args()
    
    # Print build info
    build_config.print_build_info()
    print()
    
    # Clean if requested
    if args.clean:
        clean_build_dirs()
        print()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    print()
    
    # Create spec file
    spec_file = create_spec_file()
    print()
    
    # Run PyInstaller
    if not run_pyinstaller(spec_file):
        return 1
    print()
    
    # Copy additional files
    copy_additional_files()
    print()
    
    # Create version file
    create_version_file()
    print()
    
    # Sign executable
    if args.sign:
        sign_executable()
        print()
    
    # Create archive
    if not args.no_archive:
        create_archive()
        print()
    
    # Success
    print("=" * 60)
    print("✓ Build completed successfully!")
    print("=" * 60)
    print(f"Output directory: {build_config.BUILD_DIR / build_config.APP_NAME}")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
