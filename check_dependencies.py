#!/usr/bin/env python3
"""
Junmai AutoDev - Dependency Checker
Version: 2.0

This script checks if all required dependencies are installed and properly configured.
"""

import sys
import platform
import subprocess
from typing import Dict, List, Tuple

# Color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.ENDC} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.ENDC} {text}")


def check_python_version() -> Tuple[bool, str]:
    """Check Python version"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major == 3 and 9 <= version.minor <= 11:
        return True, version_str
    else:
        return False, version_str


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name.replace('-', '_').lower()
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, "not installed"


def check_redis() -> Tuple[bool, str]:
    """Check Redis connection"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
        r.ping()
        info = r.info()
        version = info.get('redis_version', 'unknown')
        return True, version
    except Exception as e:
        return False, str(e)


def check_ollama() -> Tuple[bool, str]:
    """Check Ollama connection"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            return True, f"{len(models)} models available"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def check_gpu() -> Tuple[bool, str]:
    """Check GPU availability"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return True, f"{gpu_name} ({gpu_memory:.1f} GB)"
        else:
            return False, "CUDA not available"
    except ImportError:
        return False, "PyTorch not installed"
    except Exception as e:
        return False, str(e)


def check_lightroom() -> Tuple[bool, str]:
    """Check if Lightroom Classic is installed"""
    system = platform.system()
    
    if system == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Adobe\Lightroom",
                0,
                winreg.KEY_READ
            )
            version = winreg.QueryValueEx(key, "Version")[0]
            winreg.CloseKey(key)
            return True, version
        except:
            return False, "not found in registry"
    
    elif system == "Darwin":  # macOS
        import os
        lr_path = "/Applications/Adobe Lightroom Classic/Adobe Lightroom Classic.app"
        if os.path.exists(lr_path):
            return True, "installed"
        else:
            return False, "not found"
    
    else:
        return False, "unsupported OS"


def check_disk_space() -> Tuple[bool, str]:
    """Check available disk space"""
    import shutil
    
    try:
        if platform.system() == "Windows":
            path = "C:\\"
        else:
            path = "/"
        
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)
        
        if free_gb >= 50:
            return True, f"{free_gb:.1f} GB free"
        else:
            return False, f"{free_gb:.1f} GB free (< 50 GB required)"
    except Exception as e:
        return False, str(e)


def main():
    """Main dependency check function"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                                                           ║")
    print("║         Junmai AutoDev - Dependency Checker              ║")
    print("║                                                           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    all_checks_passed = True
    
    # System Information
    print_header("System Information")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {platform.python_version()}")
    
    # Python Version
    print_header("Python Version")
    success, version = check_python_version()
    if success:
        print_success(f"Python {version} (compatible)")
    else:
        print_error(f"Python {version} (requires 3.9-3.11)")
        all_checks_passed = False
    
    # Core Dependencies
    print_header("Core Python Packages")
    
    core_packages = [
        ('flask', 'flask'),
        ('sqlalchemy', 'sqlalchemy'),
        ('redis', 'redis'),
        ('celery', 'celery'),
        ('opencv-python', 'cv2'),
        ('pillow', 'PIL'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
    ]
    
    for package_name, import_name in core_packages:
        success, version = check_package(package_name, import_name)
        if success:
            print_success(f"{package_name}: {version}")
        else:
            print_error(f"{package_name}: {version}")
            all_checks_passed = False
    
    # GUI Dependencies
    print_header("GUI Dependencies")
    
    gui_packages = [
        ('PyQt6', 'PyQt6'),
        ('PyQt6-WebEngine', 'PyQt6.QtWebEngineWidgets'),
    ]
    
    for package_name, import_name in gui_packages:
        success, version = check_package(package_name, import_name)
        if success:
            print_success(f"{package_name}: {version}")
        else:
            print_warning(f"{package_name}: {version} (GUI will not work)")
    
    # AI/ML Dependencies
    print_header("AI/ML Dependencies")
    
    ai_packages = [
        ('torch', 'torch'),
        ('transformers', 'transformers'),
        ('exifread', 'exifread'),
    ]
    
    for package_name, import_name in ai_packages:
        success, version = check_package(package_name, import_name)
        if success:
            print_success(f"{package_name}: {version}")
        else:
            print_warning(f"{package_name}: {version} (AI features may be limited)")
    
    # External Services
    print_header("External Services")
    
    # Redis
    success, info = check_redis()
    if success:
        print_success(f"Redis: {info}")
    else:
        print_warning(f"Redis: {info} (background processing will be limited)")
    
    # Ollama
    success, info = check_ollama()
    if success:
        print_success(f"Ollama: {info}")
    else:
        print_warning(f"Ollama: {info} (AI features will not work)")
    
    # Hardware
    print_header("Hardware")
    
    # GPU
    success, info = check_gpu()
    if success:
        print_success(f"GPU: {info}")
    else:
        print_warning(f"GPU: {info} (will use CPU mode)")
    
    # Disk Space
    success, info = check_disk_space()
    if success:
        print_success(f"Disk Space: {info}")
    else:
        print_error(f"Disk Space: {info}")
        all_checks_passed = False
    
    # Software
    print_header("Required Software")
    
    # Lightroom
    success, info = check_lightroom()
    if success:
        print_success(f"Lightroom Classic: {info}")
    else:
        print_warning(f"Lightroom Classic: {info}")
    
    # Summary
    print_header("Summary")
    
    if all_checks_passed:
        print_success("All critical dependencies are satisfied!")
        print("\nYou can proceed with running Junmai AutoDev.")
        return 0
    else:
        print_error("Some critical dependencies are missing.")
        print("\nPlease install missing dependencies and run this check again.")
        print("\nTo install Python packages:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.ENDC}")
        sys.exit(1)
