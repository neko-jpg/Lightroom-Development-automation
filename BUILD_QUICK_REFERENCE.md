# Build Quick Reference

Quick commands for building and deploying Junmai AutoDev.

## Prerequisites

```bash
pip install -r requirements.txt
```

## Complete Build (Recommended)

```bash
# Build everything: executable + installer + checksums + docs
python build_all.py

# With clean build
python build_all.py --clean
```

## Individual Steps

### 1. Build Executable Only

```bash
# Standard build
python build.py

# Clean build
python build.py --clean

# Skip archive creation
python build.py --no-archive

# With code signing
python build.py --sign
```

**Output**: `dist/JunmaiAutoDev/`

### 2. Create Installer Only

```bash
python create_installer.py
```

**Output**: 
- Windows: `installers/JunmaiAutoDev-2.0.0-Setup.exe`
- macOS: `installers/JunmaiAutoDev-2.0.0.dmg`
- Linux: `installers/JunmaiAutoDev-2.0.0-linux.tar.gz`

### 3. Test Auto-Updater

```bash
python auto_updater.py
```

## Configuration

### Edit Build Settings

```python
# build_config.py
APP_VERSION = "2.0.0"
APP_NAME = "JunmaiAutoDev"
ONE_FILE = False  # True for single executable
CONSOLE_MODE = False  # True to show console
```

### Add Hidden Imports

```python
# build_config.py
HIDDEN_IMPORTS = [
    'your_module',
    # ...
]
```

### Exclude Modules

```python
# build_config.py
EXCLUDED_MODULES = [
    'matplotlib',
    'scipy',
    # ...
]
```

## Platform-Specific

### Windows

```powershell
# Install Inno Setup first
# https://jrsoftware.org/isdl.php

# Build
python build_all.py

# Output
# installers/JunmaiAutoDev-2.0.0-Setup.exe
```

### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Build
python build_all.py

# Output
# installers/JunmaiAutoDev-2.0.0.dmg

# Optional: Code sign
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  dist/JunmaiAutoDev.app
```

### Linux

```bash
# Build
python build_all.py

# Output
# installers/JunmaiAutoDev-2.0.0-linux.tar.gz

# Optional: Create .deb package
# (requires additional setup)
```

## Testing

```bash
# Run all tests
cd local_bridge
py -m pytest test_*.py

# Integration tests
py run_integration_tests.py

# Performance tests
py test_performance_benchmark.py
```

## Distribution

### Create GitHub Release

```bash
# Tag version
git tag -a v2.0.0 -m "Release version 2.0.0"
git push origin v2.0.0

# Upload files from installers/ directory:
# - JunmaiAutoDev-2.0.0-Setup.exe (Windows)
# - JunmaiAutoDev-2.0.0.dmg (macOS)
# - JunmaiAutoDev-2.0.0-linux.tar.gz (Linux)
# - SHA256SUMS.txt (checksums)
# - RELEASE_NOTES.md (release notes)
```

## Troubleshooting

### Build Fails

```bash
# Clean everything
python build.py --clean

# Check dependencies
pip install --upgrade PyInstaller packaging

# Verify Python version
python --version  # Should be 3.9-3.11
```

### Installer Creation Fails

**Windows**: Install Inno Setup  
**macOS**: Check Xcode Command Line Tools  
**Linux**: Check build-essential package

### Large Executable Size

Add modules to exclude in `build_config.py`:

```python
EXCLUDED_MODULES = [
    'matplotlib',
    'scipy',
    'pandas',
    # Add more...
]
```

## File Structure

```
.
├── build_config.py          # Build configuration
├── build.py                 # PyInstaller build script
├── create_installer.py      # Installer creation script
├── build_all.py            # Complete build script
├── auto_updater.py         # Auto-update functionality
├── dist/                   # Build output
│   └── JunmaiAutoDev/     # Executable and files
├── build/                  # Temporary build files
├── installers/             # Installer packages
│   ├── *.exe / *.dmg / *.tar.gz
│   ├── SHA256SUMS.txt
│   ├── RELEASE_NOTES.md
│   └── CHANGELOG.md
└── JunmaiAutoDev.spec     # PyInstaller spec file
```

## Common Commands

```bash
# Full build with clean
python build_all.py --clean

# Build without installer
python build_all.py --skip-installer

# Build without executable (installer only)
python build_all.py --skip-build

# Just create checksums
cd installers
sha256sum * > SHA256SUMS.txt
```

## Version Management

1. Update version in `build_config.py`:
   ```python
   APP_VERSION = "2.1.0"
   ```

2. Update `CHANGELOG.md`

3. Commit changes:
   ```bash
   git commit -am "Bump version to 2.1.0"
   ```

4. Build and release:
   ```bash
   python build_all.py
   git tag -a v2.1.0 -m "Release 2.1.0"
   git push origin v2.1.0
   ```

## Support

- Full Guide: `DEPLOYMENT_GUIDE.md`
- Issues: https://github.com/junmai/autodev/issues
- Docs: https://github.com/junmai/autodev/wiki

---

**Quick Tip**: For most cases, just run `python build_all.py` and you're done!
