"""Junmai AutoDev Launcher

Automates extraction, dependency checks, and application startup so that
non-technical photographers can just double-click the EXE and start editing.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict

import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = "Junmai AutoDev"
APP_VERSION = "2.0.0"
INSTALL_ROOT = Path(os.getenv("LOCALAPPDATA", Path.home())) / APP_NAME
CONFIG_ROOT = Path(os.getenv("APPDATA", Path.home())) / APP_NAME
CONFIG_PATH = CONFIG_ROOT / "config.json"
BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 5100
PAYLOADS = [
    "JunmaiAutoDev.exe",
    "JunmaiAutoDev.lrdevplugin",
    "start.ps1",
    "auto_updater.py",
    "GettingStarted.html",
]

FALLBACK_WELCOME_GUIDE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <title>Junmai AutoDev Getting Started</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 2rem; }
        h1 { color: #222; }
        section { margin-bottom: 2rem; }
        .step { margin-bottom: 1rem; }
    </style>
</head>
<body>
    <h1>Junmai AutoDev セットアップ完了</h1>
    <section>
        <p>アプリが自動で環境を準備し、Lightroomと連携する準備が整いました。</p>
        <div class="step">
            <strong>Step 1</strong> Lightroomで編集したい写真を選択し、現像モジュールを開きます。
        </div>
        <div class="step">
            <strong>Step 2</strong> Junmai AutoDevを起動し、気分に合うテンプレートを選ぶか自由に入力します。
        </div>
        <div class="step">
            <strong>Step 3</strong> 「Lightroomに送信する」をクリックすると、安全な仮想コピーに設定が適用されます。
        </div>
    </section>
    <section>
        <h2>困ったときは？</h2>
        <ul>
            <li>Bridgeステータスが「未接続」の場合は、アプリが自動で再接続を試みます。</li>
            <li>プラグインを再登録したい場合は、同梱の <code>JunmaiAutoDev.lrdevplugin</code> フォルダをLightroomに追加してください。</li>
        </ul>
    </section>
</body>
</html>
"""


def distribution_root() -> Path:
    """Return the directory containing all packaged assets."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Junmai AutoDev Launcher options.")
    parser.add_argument(
        "--force-checks",
        action="store_true",
        help="Always run dependency checks and avoid passing --skip-checks to the desktop app.",
    )
    parser.add_argument(
        "--skip-dependency-checks",
        action="store_true",
        help="Skip Redis/Ollama probing (useful for advanced troubleshooting).",
    )
    return parser.parse_args()


CLI_ARGS = parse_cli_args()


class LauncherState:
    """Persists install metadata so we can skip redundant work."""

    def __init__(self) -> None:
        self.data: Dict[str, object] = {
            "installed": False,
            "install_path": None,
            "last_launch": None,
            "guide_opened": False,
            "version": APP_VERSION,
        }
        self.load()

    def load(self) -> None:
        if CONFIG_PATH.exists():
            try:
                self.data.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                # Continue with defaults if the file is corrupted.
                pass

    def save(self) -> None:
        CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


class LauncherApp:
    """Lightweight Tkinter UI that automates the first-run experience."""

    def __init__(self, cli_args: argparse.Namespace) -> None:
        self.cli_args = cli_args
        self.state = LauncherState()
        self.source_root = distribution_root()
        self.should_open_welcome = not self.state.data.get("guide_opened", False)
        self.preexisting_install = bool(self.state.data.get("installed"))

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} Launcher")
        self.root.geometry("460x320")
        self.root.resizable(False, False)

        self.status_var = tk.StringVar(value="環境を確認しています…")
        self.detail_var = tk.StringVar(value="少々お待ちください。処理は自動で進みます。")

        self._build_ui()
        self.root.after(400, self.start_setup)

    # UI -----------------------------------------------------------------

    def _build_ui(self) -> None:
        padding = {"padx": 16, "pady": 8}

        title = tk.Label(
            self.root,
            text="Junmai AutoDev セットアップ",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(**padding)

        status_label = tk.Label(self.root, textvariable=self.status_var, font=("Segoe UI", 11))
        status_label.pack(**padding)

        detail_label = tk.Label(self.root, textvariable=self.detail_var, wraplength=400)
        detail_label.pack(padx=16)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=16, pady=16)
        self.progress.start(12)

        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill="x", padx=16, pady=16)

        self.retry_button = ttk.Button(button_frame, text="やり直す", command=self.restart_setup, state=tk.DISABLED)
        self.retry_button.pack(side=tk.LEFT)

        self.close_button = ttk.Button(button_frame, text="閉じる", command=self.root.destroy)
        self.close_button.pack(side=tk.RIGHT)

    # Workflow ------------------------------------------------------------

    def start_setup(self) -> None:
        self.retry_button.config(state=tk.DISABLED)
        worker = threading.Thread(target=self._perform_setup, daemon=True)
        worker.start()

    def restart_setup(self) -> None:
        self.status_var.set("再実行中…")
        self.detail_var.set("セットアップをやり直しています。")
        self.progress.start(12)
        self.start_setup()

    def _perform_setup(self) -> None:
        try:
            self._update_status("インストール先を準備", "フォルダと必要なファイルを配置します。")
            INSTALL_ROOT.mkdir(parents=True, exist_ok=True)

            self._copy_payloads()
            guide_path = self._ensure_welcome_guide()

            self.state.data.update(
                {
                    "installed": True,
                    "install_path": str(INSTALL_ROOT),
                    "version": APP_VERSION,
                }
            )
            self.state.save()

            if self.should_open_welcome:
                self._open_welcome_async(guide_path)
                self.state.data["guide_opened"] = True
                self.state.save()

            self._update_status("依存サービスをチェック", "Redis と Ollama の接続状況を確認中...")
            self._verify_runtime_dependencies()

            self._update_status("準備完了", "アプリを起動しています。")
            exe_path = self._launch_main_app()
            self.state.data["last_launch"] = datetime.utcnow().isoformat()
            self.state.save()

            self.root.after(
                0,
                lambda: self._on_success(exe_path),
            )
        except Exception as exc:  # noqa: BLE001 - show message to user
            self.root.after(
                0,
                lambda: self._on_failure(str(exc)),
            )

    def _copy_payloads(self) -> None:
        for item in PAYLOADS:
            src = self.source_root / item
            if not src.exists():
                if item == "GettingStarted.html":
                    continue
                raise FileNotFoundError(f"必要なファイルが見つかりません: {src}")

            dest = INSTALL_ROOT / item
            if src.is_dir():
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

    def _ensure_welcome_guide(self) -> Path:
        guide_path = INSTALL_ROOT / "GettingStarted.html"
        if not guide_path.exists():
            guide_path.write_text(FALLBACK_WELCOME_GUIDE, encoding="utf-8")
        return guide_path

    def _open_welcome_async(self, guide_path: Path) -> None:
        def _open() -> None:
            time.sleep(1)
            webbrowser.open(guide_path.as_uri())

        threading.Thread(target=_open, daemon=True).start()

    def _launch_main_app(self) -> Path:
        exe_path = INSTALL_ROOT / "JunmaiAutoDev.exe"
        if not exe_path.exists():
            raise FileNotFoundError("JunmaiAutoDev.exe が見つかりません。")

        self._ensure_port_available(BRIDGE_HOST, BRIDGE_PORT)

        creationflags = 0
        if os.name == "nt":
            creationflags = (
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                | getattr(subprocess, "DETACHED_PROCESS", 0)
            )

        launch_cmd = [str(exe_path)]
        if self.preexisting_install and not self.cli_args.force_checks:
            launch_cmd.append("--skip-checks")

        subprocess.Popen(
            launch_cmd,
            cwd=str(INSTALL_ROOT),
            creationflags=creationflags,
        )
        return exe_path

    def _ensure_port_available(self, host: str, port: int) -> None:
        """Detects bridge port conflicts before launching the desktop app."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
        except OSError as exc:  # noqa: BLE001 - converted to user-facing error
            raise RuntimeError(
                f"ポート{port}が既に使用中のためJunmai AutoDevを起動できません。"
                " 他のアプリを閉じてからもう一度お試しください。"
                f"\n詳細: {exc}"
            ) from exc
        finally:
            sock.close()

    def _verify_runtime_dependencies(self) -> None:
        """Ensures Redis and Ollama endpoints are reachable."""
        if self.cli_args.skip_dependency_checks:
            return

        missing = []
        if not self._can_connect_tcp("127.0.0.1", 6379):
            missing.append("Redis (localhost:6379)")
        if not self._can_reach_http("http://127.0.0.1:11434/api/tags"):
            missing.append("Ollama (http://127.0.0.1:11434)")

        if missing:
            raise RuntimeError(
                "以下のサービスに接続できませんでした。起動してから再実行してください。\n"
                + "\n".join(f"- {name}" for name in missing)
            )

    def _can_connect_tcp(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Returns True when a TCP connection succeeds."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def _can_reach_http(self, url: str, timeout: float = 2.0) -> bool:
        """Returns True when an HTTP GET returns 200 OK."""
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.status == 200
        except Exception:
            return False

    def _update_status(self, title: str, detail: str) -> None:
        self.root.after(0, lambda: self.status_var.set(title))
        self.root.after(0, lambda: self.detail_var.set(detail))

    def _on_success(self, exe_path: Path) -> None:
        self.progress.stop()
        self.detail_var.set(f"{exe_path.name} を起動しました。ウィンドウは自動で閉じても問題ありません。")
        self.retry_button.config(state=tk.DISABLED)
        self.root.after(1500, self.root.destroy)

    def _on_failure(self, message: str) -> None:
        self.progress.stop()
        self.status_var.set("エラーが発生しました")
        self.detail_var.set(message)
        self.retry_button.config(state=tk.NORMAL)
        messagebox.showerror("Junmai AutoDev", message)

    def run(self) -> None:
        self.root.mainloop()

def main() -> None:
    app = LauncherApp(CLI_ARGS)
    app.run()


if __name__ == "__main__":
    main()
