# build_package.py
import os
import shutil
import subprocess
import requests
import zipfile
import io

# --- Configuration ---
VERSION = "1.0"
APP_NAME = "JunmaiAutoDev"
OLLAMA_URL = "https://github.com/ollama/ollama/releases/download/v0.12.10/ollama-windows-amd64.zip" # A specific older version for stability, can be updated.
OUTPUT_DIR = f"{APP_NAME}_v{VERSION}"
OUTPUT_ZIP = f"{OUTPUT_DIR}.zip"
PLUGIN_DIR = f"{APP_NAME}.lrdevplugin"

# PyInstaller command
PYINSTALLER_CMD = [
    'pyinstaller',
    'main.py',
    '--name', APP_NAME,
    '--onefile',
    '--windowed',
    '--hidden-import=engineio.async_drivers.gevent',
    '--hidden-import=eventlet',
    '--hidden-import=gunicorn'
]

# README content
README_CONTENT = f"""
# {APP_NAME} v{VERSION} - セットアップガイド

この度は {APP_NAME} をご利用いただきありがとうございます。
このアプリケーションは、自然言語の指示からAIが最適な現像設定を生成し、Lightroom Classicの写真を自動で編集するシステムです。

## セットアップ手順

1. **Lightroomプラグインのインストール**
   - Adobe Lightroom Classicを起動します。
   - メニューから [ファイル] > [プラグインマネージャー] を選択します。
   - 左下の [追加] ボタンをクリックします。
   - このフォルダ内にある `{PLUGIN_DIR}` フォルダを選択し、[プラグインを追加] をクリックします。
   - 右側のペインに「{APP_NAME}」が表示され、緑色の丸印がついて有効になっていることを確認し、[完了] をクリックします。

2. **AIモデルのダウンロード (初回のみ)**
   - このフォルダにある `{APP_NAME}.exe` をダブルクリックして起動します。
   - GUIが起動したら、一度GUIは閉じずにそのままにして、コマンドプロンプト（またはPowerShell）を開きます。
   - 以下のコマンドをコピー＆ペーストして実行し、写真の現像に使用するAIモデルをダウンロードします。これには数分かかります。
     ```
     .\\ollama\\ollama.exe pull llama3.1:8b-instruct
     ```
   - "success" というメッセージが表示されたら、ダウンロードは完了です。コマンドプロンプトは閉じて構いません。

## 使い方

1. `{APP_NAME}.exe` をダブルクリックして、GUIアプリケーションを起動します。
2. Lightroom Classicで、現像したい写真を選択し、現像（Develop）モジュールを開きます。
3. `{APP_NAME}` のGUIに、実現したい写真のイメージを文章で入力します。（例：「夕焼けの風景です。ドラマチックで感動的な雰囲気にしてください」）
4. [Submit to Lightroom] ボタンをクリックします。
5. Lightroom内で自動的に写真の仮想コピーが作成され、現像処理が実行されます。
"""

def main():
    """Main build process orchestrator."""
    print("--- Starting Junmai AutoDev Package Build ---")

    # 1. Cleanup old build artifacts
    print("1/7: Cleaning up old artifacts...")
    for item in ['build', 'dist', OUTPUT_DIR, OUTPUT_ZIP, f'{APP_NAME}.spec']:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
    print("   Cleanup complete.")

    # 2. Run PyInstaller
    print(f"2/7: Running PyInstaller to create {APP_NAME}.exe...")
    try:
        subprocess.run(PYINSTALLER_CMD, check=True, capture_output=True, text=True)
        print("   PyInstaller build successful.")
    except subprocess.CalledProcessError as e:
        print("   !!! PyInstaller failed !!!")
        print(e.stderr)
        return

    # 3. Create package directory structure
    print(f"3/7: Creating package directory: {OUTPUT_DIR}")
    os.makedirs(os.path.join(OUTPUT_DIR, 'ollama'))
    print("   Directory structure created.")

    # 4. Assemble application files
    print("4/7: Assembling application files...")
    shutil.move(os.path.join('dist', APP_NAME), os.path.join(OUTPUT_DIR, f'{APP_NAME}.exe'))
    shutil.copytree(PLUGIN_DIR, os.path.join(OUTPUT_DIR, PLUGIN_DIR))
    print("   Files assembled.")

    # 5. Download and extract Ollama
    print(f"5/7: Downloading Ollama from {OLLAMA_URL}...")
    try:
        response = requests.get(OLLAMA_URL, stream=True)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(os.path.join(OUTPUT_DIR, 'ollama'))
        print("   Ollama downloaded and extracted successfully.")
    except requests.RequestException as e:
        print(f"   !!! Failed to download Ollama: {e} !!!")
        return
    except zipfile.BadZipFile:
        print("   !!! Failed to extract Ollama: The downloaded file is not a valid zip file. !!!")
        return

    # 6. Create README file
    print("6/7: Creating README_SETUP.txt...")
    with open(os.path.join(OUTPUT_DIR, 'README_SETUP.txt'), 'w', encoding='utf-8') as f:
        f.write(README_CONTENT)
    print("   README created.")

    # 7. Create final Zip archive
    print(f"7/7: Creating final archive: {OUTPUT_ZIP}...")
    shutil.make_archive(OUTPUT_DIR, 'zip', root_dir='.', base_dir=OUTPUT_DIR)
    print("   Archive created successfully.")

    # Final cleanup of the staging directory
    shutil.rmtree(OUTPUT_DIR)
    shutil.rmtree('build')
    shutil.rmtree('dist')
    os.remove(f'{APP_NAME}.spec')

    print("\n--- Build process complete! ---")
    print(f"Distribution package is ready: {os.path.abspath(OUTPUT_ZIP)}")

if __name__ == "__main__":
    main()
