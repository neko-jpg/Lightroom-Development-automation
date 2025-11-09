#!/usr/bin/env python3
"""
Junmai AutoDev - Initial Setup Wizard
Version: 2.0

This wizard guides users through the initial configuration of Junmai AutoDev.
"""

import os
import sys
import json
import platform
from pathlib import Path
from typing import Dict, List, Optional

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_banner():
    """Print welcome banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         Junmai AutoDev - 初期設定ウィザード               ║
║                                                           ║
║     Lightroom × LLM 自動現像システム                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(f"{Colors.OKCYAN}{banner}{Colors.ENDC}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {message}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ{Colors.ENDC} {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠{Colors.ENDC} {message}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗{Colors.ENDC} {message}")


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default value"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(prompt).strip()
    return value if value else (default or "")


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    response = get_input(f"{prompt} ({default_str})", "y" if default else "n").lower()
    return response in ['y', 'yes', ''] if default else response in ['y', 'yes']


def validate_path(path: str, must_exist: bool = False) -> bool:
    """Validate a file system path"""
    if not path:
        return False
    
    path_obj = Path(path)
    
    if must_exist:
        return path_obj.exists()
    else:
        # Check if parent directory exists
        return path_obj.parent.exists() or path_obj.exists()


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed"""
    print_info("依存関係を確認中...")
    
    dependencies = {}
    
    # Check Python version
    python_version = sys.version_info
    dependencies['python'] = python_version >= (3, 9) and python_version < (3, 12)
    if dependencies['python']:
        print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print_error(f"Python バージョンが不適切です: {python_version.major}.{python_version.minor}")
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        dependencies['redis'] = True
        print_success("Redis 接続確認")
    except Exception:
        dependencies['redis'] = False
        print_warning("Redis に接続できません（バックグラウンド処理が制限されます）")
    
    # Check Ollama
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        dependencies['ollama'] = response.status_code == 200
        if dependencies['ollama']:
            print_success("Ollama 接続確認")
        else:
            print_warning("Ollama に接続できません（AI機能が制限されます）")
    except Exception:
        dependencies['ollama'] = False
        print_warning("Ollama に接続できません（AI機能が制限されます）")
    
    # Check required Python packages
    required_packages = ['flask', 'sqlalchemy', 'opencv-python', 'PyQt6']
    all_packages_installed = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').lower())
        except ImportError:
            all_packages_installed = False
            print_warning(f"パッケージが見つかりません: {package}")
    
    dependencies['packages'] = all_packages_installed
    if all_packages_installed:
        print_success("必要なパッケージがインストール済み")
    
    return dependencies


def configure_system_settings() -> Dict:
    """Configure system settings"""
    print(f"\n{Colors.BOLD}=== システム設定 ==={Colors.ENDC}\n")
    
    settings = {}
    
    # Hot folders
    print_info("ホットフォルダー（自動監視フォルダ）を設定します")
    print_info("写真をコピーするだけで自動的に処理が開始されます")
    
    hot_folders = []
    while True:
        folder = get_input("ホットフォルダーのパス（空白で終了）")
        if not folder:
            break
        
        if validate_path(folder, must_exist=False):
            # Create folder if it doesn't exist
            Path(folder).mkdir(parents=True, exist_ok=True)
            hot_folders.append(folder)
            print_success(f"追加: {folder}")
        else:
            print_error("無効なパスです")
    
    if not hot_folders:
        # Set default hot folder
        if platform.system() == "Windows":
            default_folder = "D:\\Photos\\Inbox"
        else:
            default_folder = os.path.expanduser("~/Pictures/Inbox")
        
        if get_yes_no(f"デフォルトのホットフォルダーを使用しますか？ ({default_folder})", True):
            Path(default_folder).mkdir(parents=True, exist_ok=True)
            hot_folders.append(default_folder)
    
    settings['hot_folders'] = hot_folders
    
    # Lightroom catalog
    print()
    print_info("Lightroom カタログファイルを指定します")
    catalog_path = get_input("Lightroom カタログのパス (.lrcat)")
    
    if catalog_path and validate_path(catalog_path, must_exist=True):
        settings['lightroom_catalog'] = catalog_path
        print_success(f"カタログ: {catalog_path}")
    else:
        print_warning("カタログパスが無効です。後で設定してください")
        settings['lightroom_catalog'] = ""
    
    # Temp folder
    print()
    if platform.system() == "Windows":
        default_temp = "C:\\Temp\\JunmaiAutoDev"
    else:
        default_temp = "/tmp/JunmaiAutoDev"
    
    temp_folder = get_input("一時フォルダー", default_temp)
    Path(temp_folder).mkdir(parents=True, exist_ok=True)
    settings['temp_folder'] = temp_folder
    
    # Log level
    print()
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    print_info("ログレベルを選択してください:")
    for i, level in enumerate(log_levels, 1):
        print(f"  {i}. {level}")
    
    log_choice = get_input("選択 (1-4)", "2")
    try:
        settings['log_level'] = log_levels[int(log_choice) - 1]
    except (ValueError, IndexError):
        settings['log_level'] = "INFO"
    
    return settings


def configure_ai_settings() -> Dict:
    """Configure AI settings"""
    print(f"\n{Colors.BOLD}=== AI 設定 ==={Colors.ENDC}\n")
    
    settings = {}
    
    # LLM provider
    settings['llm_provider'] = "ollama"
    
    # LLM model
    print_info("使用する LLM モデルを選択してください:")
    models = [
        "llama3.1:8b-instruct (推奨: バランス型)",
        "llama3.1:11b-instruct (高品質)",
        "llama3.2:3b-instruct (高速)"
    ]
    
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    
    model_choice = get_input("選択 (1-3)", "1")
    model_map = {
        "1": "llama3.1:8b-instruct",
        "2": "llama3.1:11b-instruct",
        "3": "llama3.2:3b-instruct"
    }
    settings['llm_model'] = model_map.get(model_choice, "llama3.1:8b-instruct")
    
    # Ollama host
    settings['ollama_host'] = get_input("Ollama ホスト", "http://localhost:11434")
    
    # GPU memory limit
    print()
    print_info("GPU メモリ制限を設定します（MB単位）")
    print_info("RTX 4060 8GB の場合: 6144 MB を推奨")
    gpu_limit = get_input("GPU メモリ制限 (MB)", "6144")
    try:
        settings['gpu_memory_limit_mb'] = int(gpu_limit)
    except ValueError:
        settings['gpu_memory_limit_mb'] = 6144
    
    # Quantization
    print()
    settings['enable_quantization'] = get_yes_no(
        "モデル量子化を有効にしますか？（メモリ使用量削減）", False
    )
    
    # Selection threshold
    print()
    print_info("AI 選別の閾値を設定します（1-5星）")
    print_info("この値以上の写真が自動現像されます")
    threshold = get_input("選別閾値", "3.5")
    try:
        settings['selection_threshold'] = float(threshold)
    except ValueError:
        settings['selection_threshold'] = 3.5
    
    return settings


def configure_processing_settings() -> Dict:
    """Configure processing settings"""
    print(f"\n{Colors.BOLD}=== 処理設定 ==={Colors.ENDC}\n")
    
    settings = {}
    
    # Auto processing flags
    settings['auto_import'] = get_yes_no("自動取り込みを有効にしますか？", True)
    settings['auto_select'] = get_yes_no("AI 自動選別を有効にしますか？", True)
    settings['auto_develop'] = get_yes_no("自動現像を有効にしますか？", True)
    settings['auto_export'] = get_yes_no("自動書き出しを有効にしますか？", False)
    
    # Concurrent jobs
    print()
    print_info("同時処理ジョブ数を設定します")
    print_info("CPU/GPU 性能に応じて調整してください")
    max_jobs = get_input("最大同時ジョブ数", "3")
    try:
        settings['max_concurrent_jobs'] = int(max_jobs)
    except ValueError:
        settings['max_concurrent_jobs'] = 3
    
    # CPU limit
    print()
    cpu_limit = get_input("CPU 使用率制限 (%)", "80")
    try:
        settings['cpu_limit_percent'] = int(cpu_limit)
    except ValueError:
        settings['cpu_limit_percent'] = 80
    
    # GPU temp limit
    print()
    gpu_temp = get_input("GPU 温度制限 (°C)", "75")
    try:
        settings['gpu_temp_limit_celsius'] = int(gpu_temp)
    except ValueError:
        settings['gpu_temp_limit_celsius'] = 75
    
    return settings


def configure_export_settings() -> Dict:
    """Configure export settings"""
    print(f"\n{Colors.BOLD}=== 書き出し設定 ==={Colors.ENDC}\n")
    
    settings = {}
    
    # Export presets
    presets = []
    
    if get_yes_no("SNS 用プリセットを追加しますか？", True):
        sns_dest = get_input("SNS 用書き出し先", "")
        if sns_dest:
            Path(sns_dest).mkdir(parents=True, exist_ok=True)
            presets.append({
                "name": "SNS",
                "enabled": True,
                "format": "JPEG",
                "quality": 85,
                "max_dimension": 2048,
                "color_space": "sRGB",
                "destination": sns_dest
            })
    
    if get_yes_no("印刷用プリセットを追加しますか？", False):
        print_dest = get_input("印刷用書き出し先", "")
        if print_dest:
            Path(print_dest).mkdir(parents=True, exist_ok=True)
            presets.append({
                "name": "Print",
                "enabled": True,
                "format": "JPEG",
                "quality": 95,
                "max_dimension": 4096,
                "color_space": "AdobeRGB",
                "destination": print_dest
            })
    
    settings['presets'] = presets
    
    # Cloud sync
    print()
    settings['cloud_sync'] = {
        "enabled": get_yes_no("クラウド同期を有効にしますか？", False),
        "provider": "dropbox",
        "remote_path": "/Photos/Processed"
    }
    
    return settings


def configure_notifications() -> Dict:
    """Configure notification settings"""
    print(f"\n{Colors.BOLD}=== 通知設定 ==={Colors.ENDC}\n")
    
    settings = {}
    
    # Desktop notifications
    settings['desktop'] = get_yes_no("デスクトップ通知を有効にしますか？", True)
    
    # Email notifications
    print()
    email_enabled = get_yes_no("メール通知を有効にしますか？", False)
    
    if email_enabled:
        settings['email'] = {
            "enabled": True,
            "smtp_server": get_input("SMTP サーバー", "smtp.gmail.com"),
            "smtp_port": int(get_input("SMTP ポート", "587")),
            "from_address": get_input("送信元アドレス"),
            "to_address": get_input("送信先アドレス"),
            "username": get_input("SMTP ユーザー名"),
            "password": ""  # Password should be set separately for security
        }
        print_warning("パスワードは後で設定ファイルに追加してください")
    else:
        settings['email'] = {"enabled": False}
    
    # LINE Notify
    print()
    line_enabled = get_yes_no("LINE Notify を有効にしますか？", False)
    
    if line_enabled:
        settings['line'] = {
            "enabled": True,
            "token": get_input("LINE Notify トークン")
        }
    else:
        settings['line'] = {"enabled": False}
    
    return settings


def configure_ui_settings() -> Dict:
    """Configure UI settings"""
    print(f"\n{Colors.BOLD}=== UI 設定 ==={Colors.ENDC}\n")
    
    settings = {}
    
    # Theme
    print_info("テーマを選択してください:")
    print("  1. ダーク")
    print("  2. ライト")
    
    theme_choice = get_input("選択 (1-2)", "1")
    settings['theme'] = "dark" if theme_choice == "1" else "light"
    
    # Language
    settings['language'] = "ja"
    
    # Advanced settings
    settings['show_advanced_settings'] = get_yes_no(
        "詳細設定を表示しますか？", False
    )
    
    return settings


def save_config(config: Dict, config_path: str):
    """Save configuration to file"""
    try:
        # Ensure config directory exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print_success(f"設定を保存しました: {config_path}")
        return True
    except Exception as e:
        print_error(f"設定の保存に失敗しました: {e}")
        return False


def main():
    """Main setup wizard function"""
    print_banner()
    
    print_info("このウィザードは Junmai AutoDev の初期設定を行います")
    print_info("各項目について質問しますので、適切な値を入力してください")
    print()
    
    if not get_yes_no("セットアップを開始しますか？", True):
        print_info("セットアップをキャンセルしました")
        return
    
    # Check dependencies
    print()
    dependencies = check_dependencies()
    
    if not dependencies.get('python', False):
        print_error("Python のバージョンが要件を満たしていません")
        return
    
    # Build configuration
    config = {
        "version": "2.0",
        "system": configure_system_settings(),
        "ai": configure_ai_settings(),
        "processing": configure_processing_settings(),
        "export": configure_export_settings(),
        "notifications": configure_notifications(),
        "ui": configure_ui_settings()
    }
    
    # Show summary
    print(f"\n{Colors.BOLD}=== 設定サマリー ==={Colors.ENDC}\n")
    print(f"ホットフォルダー: {len(config['system']['hot_folders'])} 個")
    print(f"LLM モデル: {config['ai']['llm_model']}")
    print(f"自動処理: {'有効' if config['processing']['auto_develop'] else '無効'}")
    print(f"通知: {'有効' if config['notifications']['desktop'] else '無効'}")
    print()
    
    if not get_yes_no("この設定で保存しますか？", True):
        print_info("設定を破棄しました")
        return
    
    # Determine config path
    if os.path.exists('local_bridge'):
        config_path = 'local_bridge/config/config.json'
    else:
        config_path = 'config/config.json'
    
    # Save configuration
    if save_config(config, config_path):
        print()
        print(f"{Colors.OKGREEN}╔═══════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.OKGREEN}║                                                           ║{Colors.ENDC}")
        print(f"{Colors.OKGREEN}║              セットアップが完了しました！                  ║{Colors.ENDC}")
        print(f"{Colors.OKGREEN}║                                                           ║{Colors.ENDC}")
        print(f"{Colors.OKGREEN}╚═══════════════════════════════════════════════════════════╝{Colors.ENDC}")
        print()
        
        print_info("次のステップ:")
        print("  1. Lightroom Classic でプラグインを有効化")
        print("  2. アプリケーションを起動:")
        if os.path.exists('gui_qt'):
            print("     cd gui_qt")
            print("     python main.py")
        else:
            print("     python gui.py")
        print()
        print_info("詳細は docs/USER_MANUAL.md を参照してください")
    else:
        print_error("セットアップに失敗しました")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_info("セットアップを中断しました")
        sys.exit(0)
    except Exception as e:
        print_error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)
