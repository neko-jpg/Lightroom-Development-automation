"""Build Junmai AutoDev distribution with launcher + desktop app."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent

import requests

VERSION = "2.0.0"
APP_NAME = "JunmaiAutoDev"
LAUNCHER_NAME = f"{APP_NAME}Launcher"
OUTPUT_DIR = Path(f"{APP_NAME}_v{VERSION}")
OUTPUT_ZIP = OUTPUT_DIR.with_suffix(".zip")
PLUGIN_DIR = Path(f"{APP_NAME}.lrdevplugin")
PACKAGES_DIR = Path("packages")
OLLAMA_CACHE = PACKAGES_DIR / "ollama" / "ollama-windows-amd64.zip"
OLLAMA_URL = (
    "https://github.com/ollama/ollama/releases/download/v0.12.10/"
    "ollama-windows-amd64.zip"
)

DATA_MAPPINGS = [
    ("gui_qt/resources", "gui_qt/resources"),
    ("local_bridge/config", "local_bridge/config"),
]
DATA_SEPARATOR = ";" if os.name == "nt" else ":"

WELCOME_GUIDE_HTML = dedent(
    """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="utf-8" />
        <title>Junmai AutoDev Getting Started</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 2.5rem; line-height: 1.6; background: #f6f7fb; }
            h1 { color: #202124; }
            section { background: #fff; border-radius: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.08); padding: 1.8rem; margin-bottom: 1.6rem; }
            .steps li { margin-bottom: 0.8rem; }
            code { background: #eef0f4; padding: 0.2rem 0.4rem; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Junmai AutoDev セットアップ完了</h1>
        <section>
            <h2>すぐに始める3ステップ</h2>
            <ol class="steps">
                <li>Lightroom Classicで写真を選び、現像モジュールを開きます。</li>
                <li>Junmai AutoDevを起動し、Guided Flowで雰囲気を選ぶか自由に入力します。</li>
                <li>「Lightroomに送信」をクリックすると、安全な仮想コピー上で自動現像が走ります。</li>
            </ol>
        </section>
        <section>
            <h2>プラグインを再登録したい場合</h2>
            <p><code>JunmaiAutoDev.lrdevplugin</code> フォルダーを Lightroom の
            [ファイル] → [プラグインマネージャー] から追加してください。</p>
        </section>
        <section>
            <h2>トラブルシューティング</h2>
            <ul>
                <li>Bridgeステータスが「未接続」の場合でも、アプリが数秒ごとに再接続を試みます。</li>
                <li>OllamaやRedisを別途導入している場合は、先にサービスを起動しておくと安定します。</li>
            </ul>
        </section>
    </body>
    </html>
    """
).strip()


def clean_artifacts() -> None:
    print("1/6: Cleaning previous build artifacts")
    for item in ["build", "dist", OUTPUT_DIR, OUTPUT_ZIP, f"{APP_NAME}.spec", f"{LAUNCHER_NAME}.spec"]:
        path = Path(item)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def run_pyinstaller(entry_point: str, name: str) -> None:
    print(f"2/6: Running PyInstaller for {name}")
    cmd = [
        "pyinstaller",
        entry_point,
        "--name",
        name,
        "--onefile",
        "--windowed",
        "--hidden-import=engineio.async_drivers.gevent",
        "--hidden-import=eventlet",
        "--hidden-import=gunicorn",
    ]

    for src, dest in DATA_MAPPINGS:
        data_arg = f"{src}{DATA_SEPARATOR}{dest}"
        cmd.extend(["--add-data", data_arg])

    subprocess.run(cmd, check=True)


def assemble_distribution() -> None:
    print("3/6: Assembling distribution folder")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(Path("dist") / f"{APP_NAME}.exe", OUTPUT_DIR / f"{APP_NAME}.exe")
    shutil.copy2(Path("dist") / f"{LAUNCHER_NAME}.exe", OUTPUT_DIR / f"{LAUNCHER_NAME}.exe")

    shutil.copytree(PLUGIN_DIR, OUTPUT_DIR / PLUGIN_DIR.name, dirs_exist_ok=True)
    shutil.copy2("start.ps1", OUTPUT_DIR / "start.ps1")
    shutil.copy2("auto_updater.py", OUTPUT_DIR / "auto_updater.py")

    guide_path = OUTPUT_DIR / "GettingStarted.html"
    guide_path.write_text(WELCOME_GUIDE_HTML, encoding="utf-8")
    write_version_manifest()


def bundle_ollama() -> None:
    print("4/6: Bundling Ollama binaries")
    target_dir = OUTPUT_DIR / "ollama"
    target_dir.mkdir(parents=True, exist_ok=True)

    if OLLAMA_CACHE.exists():
        print(f"   Using cached archive at {OLLAMA_CACHE}")
        source_path = OLLAMA_CACHE
    else:
        print(f"   Downloading Ollama from {OLLAMA_URL}")
        response = requests.get(OLLAMA_URL, timeout=60)
        response.raise_for_status()
        PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
        OLLAMA_CACHE.parent.mkdir(parents=True, exist_ok=True)
        OLLAMA_CACHE.write_bytes(response.content)
        source_path = OLLAMA_CACHE

    with zipfile.ZipFile(source_path, "r") as archive:
        archive.extractall(target_dir)


def create_archive() -> None:
    print("5/6: Creating zip archive")
    shutil.make_archive(OUTPUT_DIR.name, "zip", root_dir=".", base_dir=OUTPUT_DIR)


def tidy_workspace() -> None:
    print("6/6: Tidying workspace")
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    for spec in [f"{APP_NAME}.spec", f"{LAUNCHER_NAME}.spec"]:
        Path(spec).unlink(missing_ok=True)


def write_version_manifest() -> None:
    """Writes version.json for the auto-updater to consume."""
    manifest = {
        "name": APP_NAME,
        "version": VERSION,
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "launcher": f"{LAUNCHER_NAME}.exe",
            "desktop": f"{APP_NAME}.exe",
            "plugin_dir": PLUGIN_DIR.name,
        },
    }
    (OUTPUT_DIR / "version.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def main() -> None:
    print("--- Starting Junmai AutoDev build ---")
    clean_artifacts()
    run_pyinstaller("main.py", APP_NAME)
    run_pyinstaller("setup_wizard.py", LAUNCHER_NAME)
    assemble_distribution()
    bundle_ollama()
    create_archive()
    tidy_workspace()
    print(f"Build complete: {OUTPUT_ZIP.resolve()}")


if __name__ == "__main__":
    main()
