# Junmai AutoDev - インストールスクリプト

このディレクトリには、Junmai AutoDev システムのインストール、セットアップ、アンインストールを行うためのスクリプトが含まれています。

## 📋 目次

- [クイックスタート](#クイックスタート)
- [スクリプト一覧](#スクリプト一覧)
- [詳細な使用方法](#詳細な使用方法)
- [トラブルシューティング](#トラブルシューティング)

## 🚀 クイックスタート

### Windows

```powershell
# 1. インストール
.\install_windows.ps1

# 2. 初期設定
python setup_wizard.py

# 3. 起動
.\start.ps1
```

### macOS

```bash
# 1. インストール
chmod +x install_macos.sh
./install_macos.sh

# 2. 初期設定
python3 setup_wizard.py

# 3. 起動
./start.sh
```

## 📦 スクリプト一覧

### インストールスクリプト

#### `install_windows.ps1` (Windows)
Windows 環境用の自動インストールスクリプト

**機能:**
- システム要件の確認
- Python、Redis、Ollama の自動インストール（オプション）
- アプリケーションファイルのコピー
- 仮想環境の作成と依存関係のインストール
- データベースの初期化
- デスクトップショートカットの作成

**使用方法:**
```powershell
# 基本的なインストール
.\install_windows.ps1

# カスタムインストール先
.\install_windows.ps1 -InstallPath "D:\MyApps\JunmaiAutoDev"

# 依存関係チェックをスキップ
.\install_windows.ps1 -SkipDependencies

# 無人インストール（プロンプトなし）
.\install_windows.ps1 -Unattended
```

**オプション:**
- `-InstallPath <path>`: インストール先ディレクトリ（デフォルト: C:\JunmaiAutoDev）
- `-SkipDependencies`: 依存関係のインストールをスキップ
- `-SkipOllama`: Ollama のインストールをスキップ
- `-SkipRedis`: Redis のインストールをスキップ
- `-Unattended`: 無人モード（確認プロンプトなし）

#### `install_macos.sh` (macOS)
macOS 環境用の自動インストールスクリプト

**機能:**
- システム要件の確認
- Homebrew、Python、Redis、Ollama の自動インストール
- アプリケーションファイルのコピー
- 仮想環境の作成と依存関係のインストール
- データベースの初期化
- 起動スクリプトの作成

**使用方法:**
```bash
# 実行権限を付与
chmod +x install_macos.sh

# 基本的なインストール
./install_macos.sh

# カスタムインストール先
./install_macos.sh --install-path "$HOME/MyApps/JunmaiAutoDev"

# 依存関係チェックをスキップ
./install_macos.sh --skip-dependencies

# 無人インストール
./install_macos.sh --unattended
```

**オプション:**
- `--install-path <path>`: インストール先ディレクトリ（デフォルト: ~/JunmaiAutoDev）
- `--skip-dependencies`: 依存関係のインストールをスキップ
- `--skip-ollama`: Ollama のインストールをスキップ
- `--skip-redis`: Redis のインストールをスキップ
- `--unattended`: 無人モード

### セットアップウィザード

#### `setup_wizard.py`
対話型の初期設定ウィザード

**機能:**
- 依存関係の確認
- ホットフォルダーの設定
- Lightroom カタログの指定
- AI 設定（モデル選択、GPU メモリ制限）
- 処理設定（自動処理の有効化）
- 書き出し設定
- 通知設定
- UI 設定

**使用方法:**
```bash
# Windows
python setup_wizard.py

# macOS
python3 setup_wizard.py
```

**設定項目:**
1. **システム設定**
   - ホットフォルダー（複数設定可能）
   - Lightroom カタログパス
   - 一時フォルダー
   - ログレベル

2. **AI 設定**
   - LLM モデル選択
   - GPU メモリ制限
   - モデル量子化
   - 選別閾値

3. **処理設定**
   - 自動取り込み
   - AI 自動選別
   - 自動現像
   - 自動書き出し
   - 同時ジョブ数
   - CPU/GPU 制限

4. **書き出し設定**
   - SNS 用プリセット
   - 印刷用プリセット
   - クラウド同期

5. **通知設定**
   - デスクトップ通知
   - メール通知
   - LINE Notify

6. **UI 設定**
   - テーマ（ダーク/ライト）
   - 言語
   - 詳細設定表示

### 起動スクリプト

#### `start.ps1` (Windows)
Windows 用の起動スクリプト

**機能:**
- 仮想環境のアクティベート
- Redis/Ollama 接続確認
- バックエンドサーバーの起動
- Celery ワーカーの起動
- GUI の起動
- 終了時のクリーンアップ

**使用方法:**
```powershell
.\start.ps1
```

#### `start.sh` (macOS)
macOS 用の起動スクリプト（インストール時に自動生成）

**使用方法:**
```bash
./start.sh
```

### 依存関係チェッカー

#### `check_dependencies.py`
システムの依存関係を確認するスクリプト

**機能:**
- Python バージョンの確認
- 必須パッケージのインストール確認
- Redis 接続確認
- Ollama 接続確認
- GPU 検出
- Lightroom Classic のインストール確認
- ディスク空き容量の確認

**使用方法:**
```bash
# Windows
python check_dependencies.py

# macOS
python3 check_dependencies.py
```

**出力例:**
```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         Junmai AutoDev - Dependency Checker              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

============================================================
System Information
============================================================

OS: Windows 11
Architecture: AMD64
Python: 3.11.5

============================================================
Python Version
============================================================

✓ Python 3.11.5 (compatible)

============================================================
Core Python Packages
============================================================

✓ flask: 3.0.0
✓ sqlalchemy: 2.0.23
✓ redis: 5.0.1
✓ celery: 5.3.4
✓ opencv-python: 4.8.1
✓ pillow: 10.1.0
✓ numpy: 1.26.2
✓ requests: 2.31.0

...
```

### アンインストールスクリプト

#### `uninstall_windows.ps1` (Windows)
Windows 用のアンインストールスクリプト

**機能:**
- 実行中のプロセスの停止
- Lightroom プラグインの削除
- データのバックアップ（オプション）
- インストールディレクトリの削除
- デスクトップショートカットの削除

**使用方法:**
```powershell
# 基本的なアンインストール
.\uninstall_windows.ps1

# データを保持してアンインストール
.\uninstall_windows.ps1 -KeepData

# 無人アンインストール
.\uninstall_windows.ps1 -Unattended

# カスタムインストール先を指定
.\uninstall_windows.ps1 -InstallPath "D:\MyApps\JunmaiAutoDev"
```

**オプション:**
- `-InstallPath <path>`: インストール先ディレクトリ
- `-KeepData`: データをバックアップしてから削除
- `-Unattended`: 無人モード

#### `uninstall_macos.sh` (macOS)
macOS 用のアンインストールスクリプト

**使用方法:**
```bash
# 実行権限を付与
chmod +x uninstall_macos.sh

# 基本的なアンインストール
./uninstall_macos.sh

# データを保持してアンインストール
./uninstall_macos.sh --keep-data

# 無人アンインストール
./uninstall_macos.sh --unattended
```

**オプション:**
- `--install-path <path>`: インストール先ディレクトリ
- `--keep-data`: データをバックアップしてから削除
- `--unattended`: 無人モード

## 📖 詳細な使用方法

### 標準インストール手順

#### Windows

1. **前提条件の確認**
   ```powershell
   # PowerShell のバージョン確認（5.1 以上）
   $PSVersionTable.PSVersion
   ```

2. **インストールスクリプトの実行**
   ```powershell
   # 管理者権限で PowerShell を起動（推奨）
   .\install_windows.ps1
   ```

3. **初期設定ウィザードの実行**
   ```powershell
   cd C:\JunmaiAutoDev
   venv\Scripts\activate
   python setup_wizard.py
   ```

4. **Lightroom プラグインの有効化**
   - Lightroom Classic を起動
   - ファイル > プラグインマネージャー
   - 追加ボタンをクリック
   - `C:\JunmaiAutoDev\plugins\JunmaiAutoDev.lrdevplugin` を選択
   - 有効にするにチェック

5. **アプリケーションの起動**
   ```powershell
   .\start.ps1
   ```

#### macOS

1. **前提条件の確認**
   ```bash
   # macOS バージョン確認（12 以上）
   sw_vers -productVersion
   ```

2. **インストールスクリプトの実行**
   ```bash
   chmod +x install_macos.sh
   ./install_macos.sh
   ```

3. **初期設定ウィザードの実行**
   ```bash
   cd ~/JunmaiAutoDev
   source venv/bin/activate
   python3 setup_wizard.py
   ```

4. **Lightroom プラグインの有効化**
   - Lightroom Classic を起動
   - ファイル > プラグインマネージャー
   - 追加ボタンをクリック
   - `~/JunmaiAutoDev/plugins/JunmaiAutoDev.lrdevplugin` を選択
   - 有効にするにチェック

5. **アプリケーションの起動**
   ```bash
   ./start.sh
   ```

### カスタムインストール

#### 異なるインストール先を指定

```powershell
# Windows
.\install_windows.ps1 -InstallPath "D:\MyApps\JunmaiAutoDev"

# macOS
./install_macos.sh --install-path "$HOME/MyApps/JunmaiAutoDev"
```

#### 依存関係を手動でインストール

```powershell
# Windows
.\install_windows.ps1 -SkipDependencies

# macOS
./install_macos.sh --skip-dependencies
```

その後、手動で依存関係をインストール:
```bash
# Python
# Windows: https://www.python.org/downloads/
# macOS: brew install python@3.11

# Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis

# Ollama
# Windows: https://ollama.ai/download
# macOS: brew install ollama
```

### アップグレード

既存のインストールをアップグレードする場合:

1. **データのバックアップ**
   ```bash
   # 重要なデータをバックアップ
   cp -r data data_backup
   cp -r config config_backup
   ```

2. **新しいバージョンのインストール**
   ```bash
   # 既存のインストールを保持したまま上書き
   ./install_windows.ps1  # または ./install_macos.sh
   ```

3. **設定の確認**
   ```bash
   # 設定ファイルが保持されているか確認
   cat config/config.json
   ```

## 🔧 トラブルシューティング

### インストールエラー

#### "Python が見つかりません"

**Windows:**
```powershell
# Python がインストールされているか確認
python --version

# PATH に追加されているか確認
$env:PATH -split ';' | Select-String python
```

**macOS:**
```bash
# Python がインストールされているか確認
python3 --version

# Homebrew でインストール
brew install python@3.11
```

#### "Redis に接続できません"

**Windows:**
```powershell
# Redis サービスが起動しているか確認
Get-Service redis*

# 手動で起動
redis-server
```

**macOS:**
```bash
# Redis サービスが起動しているか確認
brew services list

# 起動
brew services start redis
```

#### "Ollama に接続できません"

**Windows:**
```powershell
# Ollama が起動しているか確認
Get-Process ollama

# 手動で起動
ollama serve
```

**macOS:**
```bash
# Ollama が起動しているか確認
pgrep ollama

# 起動
ollama serve &
```

#### "GPU が検出されません"

```bash
# NVIDIA ドライバーがインストールされているか確認
nvidia-smi

# CUDA がインストールされているか確認
nvcc --version

# PyTorch で GPU が認識されているか確認
python -c "import torch; print(torch.cuda.is_available())"
```

### 実行時エラー

#### "仮想環境が見つかりません"

```bash
# 仮想環境を再作成
python -m venv venv

# 依存関係を再インストール
source venv/bin/activate  # macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### "データベースエラー"

```bash
# データベースを再初期化
cd local_bridge
python init_database.py
```

#### "ポートが既に使用されています"

```bash
# 使用中のポートを確認
# Windows:
netstat -ano | findstr :5100

# macOS:
lsof -i :5100

# プロセスを終了
# Windows:
taskkill /PID <PID> /F

# macOS:
kill -9 <PID>
```

### アンインストールエラー

#### "ファイルが削除できません"

```bash
# プロセスが実行中でないか確認
# Windows:
Get-Process | Where-Object {$_.Path -like "*JunmaiAutoDev*"}

# macOS:
ps aux | grep JunmaiAutoDev

# 強制終了してから再試行
```

## 📚 関連ドキュメント

- [インストールガイド](docs/INSTALLATION_GUIDE.md) - 詳細なインストール手順
- [ユーザーマニュアル](docs/USER_MANUAL.md) - 使用方法
- [トラブルシューティング](docs/TROUBLESHOOTING.md) - 問題解決
- [FAQ](docs/FAQ.md) - よくある質問

## 🆘 サポート

問題が解決しない場合:

1. [トラブルシューティングガイド](docs/TROUBLESHOOTING.md) を確認
2. [FAQ](docs/FAQ.md) を確認
3. [GitHub Issues](https://github.com/your-repo/junmai-autodev/issues) で報告

---

© 2025 Junmai AutoDev Project
