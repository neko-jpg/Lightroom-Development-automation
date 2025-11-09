#!/usr/bin/env python3
"""
Junmai AutoDev - Auto Updater
Version: 2.0

This module handles automatic updates for the application.
"""

import os
import sys
import json
import shutil
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
import requests
from packaging import version

class AutoUpdater:
    """Handles automatic application updates"""
    
    def __init__(self, current_version: str, update_url: str = None):
        """
        Initialize auto updater
        
        Args:
            current_version: Current application version
            update_url: URL to check for updates (optional)
        """
        self.current_version = current_version
        self.update_url = update_url or "https://api.github.com/repos/junmai/autodev/releases/latest"
        self.temp_dir = Path(tempfile.gettempdir()) / "junmai_autodev_update"
        self.app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
        
    def check_for_updates(self) -> Optional[Dict]:
        """
        Check if updates are available
        
        Returns:
            Update information dict if available, None otherwise
        """
        try:
            response = requests.get(self.update_url, timeout=10)
            response.raise_for_status()
            
            release_info = response.json()
            latest_version = release_info.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                return None
            
            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                return {
                    'version': latest_version,
                    'release_notes': release_info.get('body', ''),
                    'download_url': self._get_download_url(release_info),
                    'published_at': release_info.get('published_at'),
                }
            
            return None
            
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None
    
    def _get_download_url(self, release_info: Dict) -> Optional[str]:
        """Get appropriate download URL for current platform"""
        assets = release_info.get('assets', [])
        
        # Determine platform-specific asset name
        if sys.platform == 'win32':
            pattern = 'windows'
        elif sys.platform == 'darwin':
            pattern = 'macos'
        else:
            pattern = 'linux'
        
        for asset in assets:
            name = asset.get('name', '').lower()
            if pattern in name and (name.endswith('.zip') or name.endswith('.tar.gz')):
                return asset.get('browser_download_url')
        
        return None
    
    def download_update(self, download_url: str, progress_callback=None) -> Optional[Path]:
        """
        Download update package
        
        Args:
            download_url: URL to download from
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to downloaded file, or None on failure
        """
        try:
            # Create temp directory
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine filename
            filename = download_url.split('/')[-1]
            download_path = self.temp_dir / filename
            
            # Download with progress
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
            
            return download_path
            
        except Exception as e:
            print(f"Error downloading update: {e}")
            return None
    
    def verify_download(self, file_path: Path, expected_hash: str = None) -> bool:
        """
        Verify downloaded file integrity
        
        Args:
            file_path: Path to downloaded file
            expected_hash: Expected SHA256 hash (optional)
            
        Returns:
            True if verification passed
        """
        if not file_path.exists():
            return False
        
        if expected_hash:
            # Calculate SHA256 hash
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            calculated_hash = sha256_hash.hexdigest()
            return calculated_hash == expected_hash
        
        # If no hash provided, just check file exists and has content
        return file_path.stat().st_size > 0
    
    def extract_update(self, archive_path: Path) -> Optional[Path]:
        """
        Extract update archive
        
        Args:
            archive_path: Path to archive file
            
        Returns:
            Path to extracted directory
        """
        try:
            extract_dir = self.temp_dir / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract based on file type
            if archive_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            
            elif archive_path.suffix == '.gz' and archive_path.stem.endswith('.tar'):
                import tarfile
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)
            
            else:
                print(f"Unsupported archive format: {archive_path.suffix}")
                return None
            
            return extract_dir
            
        except Exception as e:
            print(f"Error extracting update: {e}")
            return None
    
    def apply_update(self, extracted_dir: Path) -> bool:
        """
        Apply the update by replacing application files
        
        Args:
            extracted_dir: Path to extracted update files
            
        Returns:
            True if update applied successfully
        """
        try:
            # Create backup of current installation
            backup_dir = self.app_dir.parent / f"{self.app_dir.name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            shutil.copytree(self.app_dir, backup_dir)
            print(f"Backup created: {backup_dir}")
            
            # Find the actual app directory in extracted files
            app_dirs = list(extracted_dir.glob("*"))
            if len(app_dirs) == 1 and app_dirs[0].is_dir():
                source_dir = app_dirs[0]
            else:
                source_dir = extracted_dir
            
            # Copy new files
            for item in source_dir.iterdir():
                dest = self.app_dir / item.name
                
                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
            
            print("Update applied successfully")
            return True
            
        except Exception as e:
            print(f"Error applying update: {e}")
            
            # Restore from backup
            if backup_dir.exists():
                print("Restoring from backup...")
                try:
                    shutil.rmtree(self.app_dir)
                    shutil.copytree(backup_dir, self.app_dir)
                    print("Backup restored")
                except Exception as restore_error:
                    print(f"Error restoring backup: {restore_error}")
            
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print("Temporary files cleaned up")
        except Exception as e:
            print(f"Error cleaning up: {e}")
    
    def restart_application(self):
        """Restart the application after update"""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                executable = sys.executable
            else:
                # Running as script
                executable = sys.executable
                args = [sys.argv[0]]
            
            # Start new process
            if sys.platform == 'win32':
                subprocess.Popen([executable] + sys.argv[1:], 
                               creationflags=subprocess.DETACHED_PROCESS)
            else:
                subprocess.Popen([executable] + sys.argv[1:],
                               start_new_session=True)
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            print(f"Error restarting application: {e}")
    
    def perform_update(self, update_info: Dict, progress_callback=None) -> bool:
        """
        Perform complete update process
        
        Args:
            update_info: Update information from check_for_updates()
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if update completed successfully
        """
        try:
            download_url = update_info.get('download_url')
            if not download_url:
                print("No download URL available")
                return False
            
            # Download
            if progress_callback:
                progress_callback(0, "Downloading update...")
            
            archive_path = self.download_update(download_url, 
                                               lambda p: progress_callback(p * 0.5, "Downloading...") if progress_callback else None)
            
            if not archive_path:
                return False
            
            # Verify
            if progress_callback:
                progress_callback(50, "Verifying download...")
            
            if not self.verify_download(archive_path):
                print("Download verification failed")
                return False
            
            # Extract
            if progress_callback:
                progress_callback(60, "Extracting update...")
            
            extracted_dir = self.extract_update(archive_path)
            if not extracted_dir:
                return False
            
            # Apply
            if progress_callback:
                progress_callback(80, "Applying update...")
            
            if not self.apply_update(extracted_dir):
                return False
            
            # Cleanup
            if progress_callback:
                progress_callback(95, "Cleaning up...")
            
            self.cleanup()
            
            if progress_callback:
                progress_callback(100, "Update complete!")
            
            return True
            
        except Exception as e:
            print(f"Error performing update: {e}")
            return False


def check_and_prompt_update(current_version: str, parent_widget=None) -> bool:
    """
    Check for updates and prompt user
    
    Args:
        current_version: Current application version
        parent_widget: Parent Qt widget for dialogs (optional)
        
    Returns:
        True if update was performed
    """
    updater = AutoUpdater(current_version)
    
    # Check for updates
    update_info = updater.check_for_updates()
    
    if not update_info:
        return False
    
    # Prompt user
    if parent_widget:
        from PyQt6.QtWidgets import QMessageBox
        
        msg = QMessageBox(parent_widget)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Update Available")
        msg.setText(f"Version {update_info['version']} is available!")
        msg.setInformativeText("Would you like to download and install it now?")
        msg.setDetailedText(update_info.get('release_notes', ''))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return False
    else:
        # Console prompt
        print(f"\nUpdate available: {update_info['version']}")
        print(f"Release notes:\n{update_info.get('release_notes', 'No release notes')}")
        response = input("\nDownload and install? (y/n): ").lower()
        
        if response != 'y':
            return False
    
    # Perform update
    success = updater.perform_update(update_info)
    
    if success:
        if parent_widget:
            QMessageBox.information(parent_widget, "Update Complete",
                                   "Update installed successfully. The application will now restart.")
        else:
            print("\nUpdate installed successfully. Restarting...")
        
        updater.restart_application()
        return True
    else:
        if parent_widget:
            QMessageBox.critical(parent_widget, "Update Failed",
                               "Failed to install update. Please try again later.")
        else:
            print("\nUpdate failed. Please try again later.")
        
        return False


if __name__ == "__main__":
    # Test update check
    updater = AutoUpdater("2.0.0")
    update_info = updater.check_for_updates()
    
    if update_info:
        print(f"Update available: {update_info['version']}")
        print(f"Download URL: {update_info['download_url']}")
    else:
        print("No updates available")
