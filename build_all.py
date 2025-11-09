#!/usr/bin/env python3
"""
Junmai AutoDev - Complete Build Script
Version: 2.0

This script performs the complete build process:
1. Build executable with PyInstaller
2. Create installer package
3. Generate checksums
4. Create release notes
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
import build
import create_installer
import build_config

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def create_checksums_file(installer_dir: Path):
    """Create checksums file for all installers"""
    print("Generating checksums...")
    
    checksums = []
    
    for file_path in installer_dir.glob("*"):
        if file_path.is_file() and file_path.suffix in ['.exe', '.dmg', '.tar.gz', '.zip']:
            checksum = calculate_checksum(file_path)
            checksums.append(f"{checksum}  {file_path.name}")
            print(f"  {file_path.name}: {checksum}")
    
    if checksums:
        checksums_file = installer_dir / "SHA256SUMS.txt"
        checksums_file.write_text('\n'.join(checksums) + '\n')
        print(f"✓ Checksums saved to: {checksums_file}")
        return True
    
    return False

def create_release_notes(output_dir: Path):
    """Create release notes file"""
    print("Creating release notes...")
    
    release_notes = f"""# {build_config.APP_NAME} v{build_config.APP_VERSION}

Release Date: {datetime.now().strftime('%Y-%m-%d')}

## What's New

### Features
- Complete PyQt6 GUI with modern interface
- AI-powered photo selection using local LLM (Ollama + Llama 3.1)
- Context-aware automatic development presets
- Background job queue with priority management
- Real-time WebSocket communication with Lightroom
- Mobile web UI (PWA) for remote monitoring and approval
- Auto-export pipeline with cloud sync support
- Desktop, email, and LINE notifications
- GPU optimization for RTX 4060 and similar cards
- Multi-model support with quantization options
- Comprehensive error handling and failsafe mechanisms
- Performance metrics and statistics dashboard
- User acceptance testing framework

### Improvements
- Enhanced hot folder monitoring with 5-second detection
- Improved EXIF analysis with GPS and context detection
- Optimized AI evaluation with 70:30 technical/LLM weighting
- Better resource management with CPU/GPU monitoring
- Faster processing with Redis caching
- More reliable WebSocket connections with fallback
- Improved learning system for preset optimization

### Bug Fixes
- Fixed database initialization issues
- Resolved WebSocket connection stability
- Corrected GPU memory management
- Fixed export preset application
- Improved error recovery mechanisms

## Installation

### Windows
1. Download `{build_config.APP_NAME}-{build_config.APP_VERSION}-Setup.exe`
2. Run the installer and follow the wizard
3. Install Ollama from https://ollama.ai
4. Pull the Llama model: `ollama pull llama3.1:8b-instruct`
5. Launch {build_config.APP_NAME} from the Start Menu

### macOS
1. Download `{build_config.APP_NAME}-{build_config.APP_VERSION}.dmg`
2. Open the DMG and drag the app to Applications
3. Install Ollama: `brew install ollama`
4. Pull the Llama model: `ollama pull llama3.1:8b-instruct`
5. Launch {build_config.APP_NAME} from Applications

### Linux
1. Download `{build_config.APP_NAME}-{build_config.APP_VERSION}-linux.tar.gz`
2. Extract: `tar -xzf {build_config.APP_NAME}-{build_config.APP_VERSION}-linux.tar.gz`
3. Install Ollama: Follow instructions at https://ollama.ai
4. Pull the Llama model: `ollama pull llama3.1:8b-instruct`
5. Run: `./{build_config.APP_NAME}/{build_config.APP_NAME}`

## System Requirements

### Minimum
- OS: Windows 10/11, macOS 12+, or Linux (Ubuntu 20.04+)
- CPU: Intel Core i5 or AMD Ryzen 5 (4 cores)
- RAM: 8 GB
- Storage: 50 GB free space
- GPU: NVIDIA GTX 1060 6GB or better (for AI features)

### Recommended
- OS: Windows 11 or macOS 13+
- CPU: Intel Core i7 or AMD Ryzen 7 (8 cores)
- RAM: 16 GB
- Storage: 100 GB free space (SSD recommended)
- GPU: NVIDIA RTX 4060 8GB or better

### Software
- Python 3.9-3.11
- Lightroom Classic 13.0 or later
- Redis (for background processing)
- Ollama (for AI features)

## Configuration

After installation, run the setup wizard:
```bash
cd /path/to/{build_config.APP_NAME}
python setup_wizard.py
```

The wizard will guide you through:
- Hot folder configuration
- Lightroom catalog selection
- AI model selection
- Processing settings
- Export presets
- Notification preferences

## Documentation

- User Manual: `docs/USER_MANUAL.md`
- Installation Guide: `docs/INSTALLATION_GUIDE.md`
- API Reference: `docs/API_REFERENCE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- FAQ: `docs/FAQ.md`

## Support

- GitHub Issues: https://github.com/junmai/autodev/issues
- Documentation: https://github.com/junmai/autodev/wiki
- Email: support@junmai-autodev.com

## License

This software is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- Ollama team for the excellent local LLM runtime
- Meta AI for the Llama models
- Adobe for the Lightroom SDK
- All contributors and testers

---

**Note**: This is a major release with significant new features. Please backup your Lightroom catalog before using.

For detailed changelog, see CHANGELOG.md
"""
    
    release_notes_file = output_dir / "RELEASE_NOTES.md"
    release_notes_file.write_text(release_notes)
    print(f"✓ Release notes saved to: {release_notes_file}")
    
    return True

def create_changelog(output_dir: Path):
    """Create changelog file"""
    print("Creating changelog...")
    
    changelog = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [{build_config.APP_VERSION}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- PyQt6 GUI with modern interface
- AI-powered photo selection
- Context-aware automatic development
- Background job queue system
- Real-time WebSocket communication
- Mobile web UI (PWA)
- Auto-export pipeline
- Multi-channel notifications
- GPU optimization
- Auto-update functionality
- Comprehensive testing framework

### Changed
- Migrated from Tkinter to PyQt6
- Improved AI evaluation algorithm
- Enhanced resource management
- Optimized database schema
- Better error handling

### Fixed
- Database initialization issues
- WebSocket stability problems
- GPU memory leaks
- Export preset bugs
- Various UI glitches

### Security
- Added JWT authentication for API
- Implemented rate limiting
- Enhanced input validation
- Secure credential storage

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Basic Lightroom integration
- Simple GUI
- Manual job queue
- Basic preset application

---

For more details, see the full commit history on GitHub.
"""
    
    changelog_file = output_dir / "CHANGELOG.md"
    changelog_file.write_text(changelog)
    print(f"✓ Changelog saved to: {changelog_file}")
    
    return True

def print_build_summary(installer_dir: Path):
    """Print build summary"""
    print()
    print("=" * 70)
    print("BUILD SUMMARY")
    print("=" * 70)
    print(f"Application: {build_config.APP_NAME}")
    print(f"Version: {build_config.APP_VERSION}")
    print(f"Platform: {sys.platform}")
    print(f"Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Output Files:")
    print("-" * 70)
    
    total_size = 0
    for file_path in sorted(installer_dir.glob("*")):
        if file_path.is_file():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            total_size += size_mb
            print(f"  {file_path.name:<50} {size_mb:>10.2f} MB")
    
    print("-" * 70)
    print(f"  {'Total:':<50} {total_size:>10.2f} MB")
    print("=" * 70)

def main():
    """Main build function"""
    parser = argparse.ArgumentParser(description='Complete build process for Junmai AutoDev')
    parser.add_argument('--skip-build', action='store_true', help='Skip PyInstaller build')
    parser.add_argument('--skip-installer', action='store_true', help='Skip installer creation')
    parser.add_argument('--clean', action='store_true', help='Clean before building')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"COMPLETE BUILD PROCESS - {build_config.APP_NAME} v{build_config.APP_VERSION}")
    print("=" * 70)
    print()
    
    # Step 1: Build executable
    if not args.skip_build:
        print("STEP 1: Building executable with PyInstaller")
        print("-" * 70)
        
        build_args = ['--no-archive']
        if args.clean:
            build_args.append('--clean')
        
        sys.argv = ['build.py'] + build_args
        result = build.main()
        
        if result != 0:
            print("\n✗ Build failed!")
            return 1
        
        print()
    else:
        print("STEP 1: Skipping executable build")
        print()
    
    # Step 2: Create installer
    if not args.skip_installer:
        print("STEP 2: Creating installer package")
        print("-" * 70)
        
        result = create_installer.main()
        
        if result != 0:
            print("\n✗ Installer creation failed!")
            return 1
        
        print()
    else:
        print("STEP 2: Skipping installer creation")
        print()
    
    # Step 3: Generate checksums
    print("STEP 3: Generating checksums")
    print("-" * 70)
    
    installer_dir = Path("installers")
    if not create_checksums_file(installer_dir):
        print("⚠ No installer files found for checksum generation")
    
    print()
    
    # Step 4: Create release notes
    print("STEP 4: Creating release documentation")
    print("-" * 70)
    
    create_release_notes(installer_dir)
    create_changelog(installer_dir)
    
    print()
    
    # Print summary
    print_build_summary(installer_dir)
    
    print()
    print("=" * 70)
    print("✓ COMPLETE BUILD PROCESS FINISHED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Test the installer on a clean system")
    print("  2. Verify all features work correctly")
    print("  3. Create GitHub release with installers")
    print("  4. Update documentation website")
    print("  5. Announce release to users")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
