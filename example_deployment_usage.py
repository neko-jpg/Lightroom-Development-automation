#!/usr/bin/env python3
"""
Junmai AutoDev - Deployment Usage Examples
Version: 2.0

This file demonstrates how to use the deployment system.
"""

import sys
from pathlib import Path

# Example 1: Check build configuration
def example_check_config():
    """Check current build configuration"""
    print("=" * 60)
    print("Example 1: Check Build Configuration")
    print("=" * 60)
    
    import build_config
    
    print(f"Application: {build_config.APP_NAME}")
    print(f"Version: {build_config.APP_VERSION}")
    print(f"Platform: {build_config.IS_WINDOWS and 'Windows' or build_config.IS_MACOS and 'macOS' or 'Linux'}")
    print(f"Build mode: {'One-file' if build_config.ONE_FILE else 'One-directory'}")
    print(f"Console: {'Yes' if build_config.CONSOLE_MODE else 'No'}")
    print(f"Icon: {build_config.ICON_PATH}")
    print(f"Hidden imports: {len(build_config.HIDDEN_IMPORTS)} modules")
    print(f"Excluded modules: {len(build_config.EXCLUDED_MODULES)} modules")
    print()


# Example 2: Programmatic build
def example_programmatic_build():
    """Build application programmatically"""
    print("=" * 60)
    print("Example 2: Programmatic Build")
    print("=" * 60)
    
    import build
    
    # Simulate command-line arguments
    sys.argv = ['build.py', '--no-archive']
    
    print("Building application...")
    print("(This is a dry run - actual build not executed)")
    print()
    print("To actually build, run:")
    print("  python build.py")
    print()


# Example 3: Check for updates
def example_check_updates():
    """Check for application updates"""
    print("=" * 60)
    print("Example 3: Check for Updates")
    print("=" * 60)
    
    from auto_updater import AutoUpdater
    
    updater = AutoUpdater("2.0.0")
    
    print("Checking for updates...")
    print(f"Current version: {updater.current_version}")
    print(f"Update URL: {updater.update_url}")
    print()
    
    # Note: This will make an actual API call
    # update_info = updater.check_for_updates()
    # if update_info:
    #     print(f"Update available: {update_info['version']}")
    # else:
    #     print("No updates available")
    
    print("(Actual update check commented out to avoid API calls)")
    print()


# Example 4: Integrate auto-update in GUI
def example_gui_integration():
    """Show how to integrate auto-update in GUI"""
    print("=" * 60)
    print("Example 4: GUI Integration")
    print("=" * 60)
    
    print("To integrate auto-update in your PyQt6 GUI:")
    print()
    print("```python")
    print("from PyQt6.QtCore import QTimer")
    print("from auto_updater import check_and_prompt_update")
    print()
    print("class MainWindow(QMainWindow):")
    print("    def __init__(self):")
    print("        super().__init__()")
    print("        # ... your initialization ...")
    print()
    print("        # Check for updates 5 seconds after startup")
    print("        QTimer.singleShot(5000, self.check_updates)")
    print()
    print("    def check_updates(self):")
    print("        check_and_prompt_update('2.0.0', parent_widget=self)")
    print("```")
    print()


# Example 5: Create installer
def example_create_installer():
    """Create platform-specific installer"""
    print("=" * 60)
    print("Example 5: Create Installer")
    print("=" * 60)
    
    import platform
    
    print(f"Current platform: {platform.system()}")
    print()
    print("To create installer:")
    print("  python create_installer.py")
    print()
    print("Output will be:")
    if platform.system() == "Windows":
        print("  installers/JunmaiAutoDev-2.0.0-Setup.exe")
    elif platform.system() == "Darwin":
        print("  installers/JunmaiAutoDev-2.0.0.dmg")
    else:
        print("  installers/JunmaiAutoDev-2.0.0-linux.tar.gz")
    print()


# Example 6: Complete build process
def example_complete_build():
    """Complete build process"""
    print("=" * 60)
    print("Example 6: Complete Build Process")
    print("=" * 60)
    
    print("For a complete build with all steps:")
    print()
    print("  python build_all.py")
    print()
    print("This will:")
    print("  1. Build executable with PyInstaller")
    print("  2. Create platform-specific installer")
    print("  3. Generate SHA256 checksums")
    print("  4. Create release notes and changelog")
    print("  5. Print build summary")
    print()
    print("Options:")
    print("  --clean           Clean build directories first")
    print("  --skip-build      Skip executable build")
    print("  --skip-installer  Skip installer creation")
    print()


# Example 7: Version management
def example_version_management():
    """Version management workflow"""
    print("=" * 60)
    print("Example 7: Version Management")
    print("=" * 60)
    
    print("To release a new version:")
    print()
    print("1. Update version in build_config.py:")
    print("   APP_VERSION = '2.1.0'")
    print()
    print("2. Update CHANGELOG.md with changes")
    print()
    print("3. Commit changes:")
    print("   git commit -am 'Bump version to 2.1.0'")
    print()
    print("4. Build release:")
    print("   python build_all.py --clean")
    print()
    print("5. Create git tag:")
    print("   git tag -a v2.1.0 -m 'Release 2.1.0'")
    print("   git push origin v2.1.0")
    print()
    print("6. Upload installers to GitHub releases")
    print()


# Example 8: Testing before release
def example_testing():
    """Testing workflow before release"""
    print("=" * 60)
    print("Example 8: Testing Before Release")
    print("=" * 60)
    
    print("Run tests before building release:")
    print()
    print("1. Unit tests:")
    print("   cd local_bridge")
    print("   py -m pytest test_*.py")
    print()
    print("2. Integration tests:")
    print("   py run_integration_tests.py")
    print()
    print("3. Performance tests:")
    print("   py test_performance_benchmark.py")
    print()
    print("4. Build and test installer:")
    print("   python build_all.py")
    print("   # Install on clean system and test")
    print()


# Example 9: Troubleshooting
def example_troubleshooting():
    """Common troubleshooting scenarios"""
    print("=" * 60)
    print("Example 9: Troubleshooting")
    print("=" * 60)
    
    print("Common issues and solutions:")
    print()
    print("1. PyInstaller fails:")
    print("   pip install --upgrade PyInstaller")
    print()
    print("2. Large executable size:")
    print("   Add modules to EXCLUDED_MODULES in build_config.py")
    print()
    print("3. Missing DLLs:")
    print("   Add to hidden imports or binaries in spec file")
    print()
    print("4. Inno Setup not found (Windows):")
    print("   Install from https://jrsoftware.org/isdl.php")
    print()
    print("5. Build fails with import errors:")
    print("   Check all dependencies are installed:")
    print("   pip install -r requirements.txt")
    print()


# Example 10: Deployment checklist
def example_deployment_checklist():
    """Pre-deployment checklist"""
    print("=" * 60)
    print("Example 10: Deployment Checklist")
    print("=" * 60)
    
    print("Before releasing:")
    print()
    print("[ ] Version bumped in build_config.py")
    print("[ ] CHANGELOG.md updated")
    print("[ ] All tests passing")
    print("[ ] Documentation updated")
    print("[ ] Clean build completed")
    print("[ ] Installer tested on clean system")
    print("[ ] Code signed (if applicable)")
    print("[ ] Checksums generated")
    print("[ ] Release notes created")
    print("[ ] Git tag created")
    print("[ ] GitHub release created")
    print("[ ] Installers uploaded")
    print("[ ] Release announced")
    print()


def main():
    """Run all examples"""
    examples = [
        ("Check Configuration", example_check_config),
        ("Programmatic Build", example_programmatic_build),
        ("Check for Updates", example_check_updates),
        ("GUI Integration", example_gui_integration),
        ("Create Installer", example_create_installer),
        ("Complete Build", example_complete_build),
        ("Version Management", example_version_management),
        ("Testing", example_testing),
        ("Troubleshooting", example_troubleshooting),
        ("Deployment Checklist", example_deployment_checklist),
    ]
    
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Junmai AutoDev - Deployment Usage Examples".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    for i, (name, func) in enumerate(examples, 1):
        func()
        if i < len(examples):
            input("Press Enter to continue...")
            print()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print()
    print("For more information:")
    print("  - Full guide: DEPLOYMENT_GUIDE.md")
    print("  - Quick reference: BUILD_QUICK_REFERENCE.md")
    print("  - Task summary: TASK_55_COMPLETION_SUMMARY.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
