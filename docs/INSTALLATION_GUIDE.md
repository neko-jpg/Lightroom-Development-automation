# Junmai AutoDev インストールガイド

## 目次
1. [システム要件](#システム要件)
2. [事前準備](#事前準備)
3. [インストール手順](#インストール手順)
4. [初期設定](#初期設定)
5. [動作確認](#動作確認)
6. [アンインストール](#アンインストール)

---

## システム要件

### 必須要件

#### ハードウェア
- **CPU**: Intel Core i5 以上（推奨: i7 以上）
- **メモリ**: 16GB RAM 以上（推奨: 32GB）
- **GPU**: NVIDIA RTX 4060 8GB VRAM 以上（推奨: RTX 4070 以上）
- **ストレージ**: 50GB 以上の空き容量（SSD推奨）

#### ソフトウェア
- **OS**: Windows 10/11 (64-bit) または macOS 12 以上
- **Lightroom Classic**: バージョン 12.0 以上
- **Python**: 3.9 以上 3.11 以下
- **Node.js**: 16.x 以上（モバイルWeb UI使用時）
- **Redis**: 6.x 以上（バックグラウンド処理用）

### 推奨環境
- インターネット接続（初回セットアップ時のみ）
- デュアルモニター（作業効率向上のため）

---

## 事前準備

### 1. Lightroom Classic のインストール

Adobe Creative Cloud から Lightroom Classic をインストールしてください。

```
https://www.adobe.com/products/photoshop-lightroom-classic.html
```

### 2. Python のインストール

#### Windows の場合

1. Python 公式サイトからインストーラーをダウンロード
   ```
   https://www.python.org/downloads/
   ```

2. インストーラーを実行し、**"Add Python to PATH"** にチェックを入れる

3. インストール完了後、コマンドプロンプトで確認
   ```cmd
   python --version
   ```

#### macOS の場合

Homebrew を使用してインストール:
```bash
brew install python@3.10
```

### 3. Redis のインストール

#### Windows の場合

1. Redis for Windows をダウンロード
   ```
   https://github.com/microsoftarchive/redis/releases
   ```

2. インストーラーを実行し、デフォルト設定でインストール

3. サービスとして自動起動するよう設定

#### macOS の場合

```bash
brew install redis
brew services start redis
```

### 4. Ollama のインストール（ローカルLLM用）

#### Windows の場合

1. Ollama 公式サイトからインストーラーをダウンロード
   ```
   https://ollama.ai/download
   ```

2. インストール後、Llama 3.1 モデルをダウンロード
   ```cmd
   ollama pull llama3.1:8b-instruct
   ```

#### macOS の場合

```bash
brew install ollama
ollama serve &
ollama pull llama3.1:8b-instruct
```

---

## インストール手順

### ステップ 1: プロジェクトのダウンロード

```bash
git clone https://github.com/your-repo/junmai-autodev.git
cd junmai-autodev
```

### ステップ 2: Python 依存関係のインストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### ステップ 3: データベースの初期化

```bash
cd local_bridge
python init_database.py
```

成功すると以下のメッセージが表示されます:
```
✓ Database initialized successfully
✓ Tables created: sessions, photos, jobs, presets, statistics, learning_data
```

### ステップ 4: Lightroom プラグインのインストール

1. Lightroom Classic を起動

2. メニューから **ファイル > プラグインマネージャー** を選択

3. **追加** ボタンをクリック

4. `JunmaiAutoDev.lrdevplugin` フォルダを選択

5. プラグインが一覧に表示されることを確認

6. **有効にする** にチェックを入れる

### ステップ 5: デスクトップ GUI のセットアップ（オプション）

PyQt6 ベースの GUI を使用する場合:

```bash
cd gui_qt
pip install -r requirements.txt
```

### ステップ 6: モバイル Web UI のセットアップ（オプション）

```bash
cd mobile_web
npm install
```

---

## 初期設定

### 1. 設定ファイルの作成

`local_bridge/config/config.json` を編集:

```json
{
  "version": "2.0",
  "system": {
    "hot_folders": [
      "D:/Photos/Inbox"
    ],
    "lightroom_catalog": "D:/Lightroom/Catalog.lrcat",
    "temp_folder": "C:/Temp/JunmaiAutoDev",
    "log_level": "INFO"
  },
  "ai": {
    "llm_provider": "ollama",
    "llm_model": "llama3.1:8b-instruct",
    "ollama_host": "http://localhost:11434",
    "gpu_memory_limit_mb": 6144,
    "selection_threshold": 3.5
  },
  "processing": {
    "auto_import": true,
    "auto_select": true,
    "auto_develop": true,
    "auto_export": false,
    "max_concurrent_jobs": 3,
    "cpu_limit_percent": 80
  }
}
```

### 2. ホットフォルダーの設定

1. 監視したいフォルダを作成（例: `D:/Photos/Inbox`）

2. `config.json` の `hot_folders` に追加

3. フォルダの書き込み権限を確認

### 3. Lightroom カタログの指定

`config.json` の `lightroom_catalog` に、使用する Lightroom カタログのパスを設定:

```json
"lightroom_catalog": "D:/Lightroom/MyPhotos.lrcat"
```

---

## 動作確認

### 1. バックエンドサーバーの起動

```bash
cd local_bridge
python app.py
```

正常に起動すると:
```
 * Running on http://127.0.0.1:5100
 * WebSocket server started on ws://127.0.0.1:5100/ws
✓ Hot folder watcher started
✓ Redis connection established
```

### 2. Celery ワーカーの起動（別ターミナル）

```bash
cd local_bridge
python start_worker.py
```

### 3. デスクトップ GUI の起動（オプション）

```bash
cd gui_qt
python main.py
```

### 4. テスト写真での動作確認

1. テスト用の RAW ファイルを 1 枚用意

2. ホットフォルダーにコピー

3. GUI またはログで処理状況を確認

4. Lightroom で写真が取り込まれ、現像設定が適用されていることを確認

---

## トラブルシューティング

### Redis 接続エラー

**エラー**: `ConnectionError: Error connecting to Redis`

**解決方法**:
```bash
# Redis が起動しているか確認
# Windows:
redis-cli ping
# macOS:
brew services list
```

### Ollama 接続エラー

**エラー**: `Cannot connect to Ollama at http://localhost:11434`

**解決方法**:
```bash
# Ollama が起動しているか確認
ollama list

# 起動していない場合
ollama serve
```

### GPU メモリ不足

**エラー**: `CUDA out of memory`

**解決方法**:
1. `config.json` で `gpu_memory_limit_mb` を減らす（例: 4096）
2. `enable_quantization` を `true` に設定
3. 他の GPU 使用アプリケーションを終了

### Lightroom プラグインが動作しない

**確認事項**:
1. Lightroom Classic のバージョンが 12.0 以上か
2. プラグインマネージャーで有効になっているか
3. バックエンドサーバーが起動しているか
4. ファイアウォールで通信がブロックされていないか

---

## アンインストール

### 1. サービスの停止

```bash
# バックエンドサーバーを停止（Ctrl+C）
# Celery ワーカーを停止（Ctrl+C）
# Redis を停止
# Windows:
redis-cli shutdown
# macOS:
brew services stop redis
```

### 2. Lightroom プラグインの削除

1. Lightroom Classic を起動
2. **ファイル > プラグインマネージャー**
3. Junmai AutoDev を選択
4. **削除** ボタンをクリック

### 3. ファイルの削除

```bash
# プロジェクトフォルダを削除
rm -rf junmai-autodev

# 仮想環境を削除
rm -rf venv
```

### 4. データベースの削除（オプション）

```bash
# データベースファイルを削除
rm local_bridge/data/*.db
```

---

## 次のステップ

インストールが完了したら、[ユーザーマニュアル](USER_MANUAL.md) を参照して基本的な使い方を学んでください。

## サポート

問題が解決しない場合は、以下をご確認ください:
- [トラブルシューティングガイド](TROUBLESHOOTING.md)
- [FAQ](FAQ.md)
- GitHub Issues: https://github.com/your-repo/junmai-autodev/issues

---

© 2025 Junmai AutoDev Project
