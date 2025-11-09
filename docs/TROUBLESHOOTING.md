# Junmai AutoDev トラブルシューティングガイド

## 目次
1. [インストール関連](#インストール関連)
2. [起動・接続エラー](#起動接続エラー)
3. [処理エラー](#処理エラー)
4. [パフォーマンス問題](#パフォーマンス問題)
5. [Lightroom 連携](#lightroom-連携)
6. [AI・LLM 関連](#aillm-関連)
7. [ネットワーク・通信](#ネットワーク通信)
8. [データベース](#データベース)
9. [ログの確認方法](#ログの確認方法)
10. [よくある質問](#よくある質問)

---

## インストール関連

### Python のバージョンエラー

**症状**:
```
ERROR: Python 3.12 is not supported
```

**原因**: Python 3.12 以降は一部のライブラリが未対応

**解決方法**:
```bash
# Python 3.10 または 3.11 をインストール
# Windows:
py -3.10 -m venv venv

# macOS:
python3.10 -m venv venv
```

### pip install でエラー

**症状**:
```
ERROR: Could not build wheels for opencv-python
```

**解決方法**:

#### Windows の場合
```cmd
# Visual C++ Build Tools をインストール
# https://visualstudio.microsoft.com/downloads/

# または、ビルド済みホイールを使用
pip install opencv-python-headless
```

#### macOS の場合
```bash
# Xcode Command Line Tools をインストール
xcode-select --install

# Homebrew で依存関係をインストール
brew install cmake
```

### Redis インストールエラー（Windows）

**症状**: Redis for Windows が見つからない

**解決方法**:

**方法 1**: WSL2 を使用
```bash
# WSL2 で Ubuntu をインストール
wsl --install

# WSL2 内で Redis をインストール
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**方法 2**: Docker を使用
```bash
docker run -d -p 6379:6379 redis:latest
```

### Ollama インストールエラー

**症状**: Ollama がインストールできない

**解決方法**:

#### Windows の場合
```cmd
# 管理者権限でコマンドプロンプトを開く
# インストーラーを再実行

# または、手動でサービスを起動
ollama serve
```

#### macOS の場合
```bash
# Homebrew を最新化
brew update
brew upgrade

# Ollama を再インストール
brew reinstall ollama
```

---

## 起動・接続エラー

### バックエンドサーバーが起動しない

**症状**:
```
Address already in use: 5100
```

**原因**: ポート 5100 が既に使用されている

**解決方法**:

#### Windows の場合
```cmd
# ポートを使用しているプロセスを確認
netstat -ano | findstr :5100

# プロセスを終了（PID を確認後）
taskkill /PID [PID番号] /F
```

#### macOS の場合
```bash
# ポートを使用しているプロセスを確認
lsof -i :5100

# プロセスを終了
kill -9 [PID番号]
```

**代替方法**: ポート番号を変更

`local_bridge/app.py` を編集:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5101)  # 5100 → 5101
```

### Redis 接続エラー

**症状**:
```
ConnectionError: Error connecting to Redis at localhost:6379
```

**診断**:
```bash
# Redis が起動しているか確認
redis-cli ping
# 正常な場合: PONG
```

**解決方法**:

#### Redis が起動していない場合

**Windows**:
```cmd
# サービスを起動
net start Redis

# または、手動起動
redis-server
```

**macOS**:
```bash
# Homebrew サービスを起動
brew services start redis

# または、手動起動
redis-server /usr/local/etc/redis.conf
```

#### Redis が別のポートで起動している場合

`config.json` を編集:
```json
"redis": {
  "host": "localhost",
  "port": 6380,
  "db": 0
}
```

### Ollama 接続エラー

**症状**:
```
Cannot connect to Ollama at http://localhost:11434
```

**診断**:
```bash
# Ollama が起動しているか確認
curl http://localhost:11434/api/tags
```

**解決方法**:

#### Ollama が起動していない場合
```bash
# バックグラウンドで起動
ollama serve &

# または、別ターミナルで起動
ollama serve
```

#### モデルがダウンロードされていない場合
```bash
# モデル一覧を確認
ollama list

# モデルをダウンロード
ollama pull llama3.1:8b-instruct
```

#### ファイアウォールでブロックされている場合

**Windows**:
1. Windows Defender ファイアウォール を開く
2. **詳細設定** → **受信の規則**
3. **新しい規則** → ポート 11434 を許可

**macOS**:
```bash
# ファイアウォール設定を確認
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

### Lightroom プラグインが接続しない

**症状**: Lightroom プラグインが「接続できません」と表示

**診断チェックリスト**:
1. ✓ バックエンドサーバーが起動しているか
2. ✓ Lightroom Classic が起動しているか
3. ✓ プラグインが有効になっているか
4. ✓ ファイアウォールで通信が許可されているか

**解決方法**:

#### プラグインを再インストール
1. Lightroom Classic を起動
2. **ファイル > プラグインマネージャー**
3. Junmai AutoDev を選択 → **削除**
4. Lightroom を再起動
5. プラグインを再度追加

#### 接続設定を確認

`JunmaiAutoDev.lrdevplugin/Info.lua` を編集:
```lua
SERVER_URL = "http://localhost:5100"  -- ポート番号を確認
```

#### ログを確認
```
C:\Users\[ユーザー名]\AppData\Roaming\Adobe\Lightroom\Logs\
```

---

## 処理エラー

### 写真が取り込まれない

**症状**: ホットフォルダーに写真をコピーしても何も起こらない

**診断**:
```bash
# ログを確認
tail -f local_bridge/logs/main.log
```

**解決方法**:

#### ホットフォルダー監視が起動していない場合
```python
# app.py で確認
# 以下のメッセージが表示されるか確認
✓ Hot folder watcher started
```

#### ファイル形式が対応していない場合

対応形式を確認:
- RAW: CR3, CR2, NEF, ARW, RAF, ORF, DNG
- JPEG: JPG, JPEG

#### ファイルが書き込み中の場合

大容量ファイルは書き込み完了まで待機します（最大 30 秒）。

#### 権限エラーの場合

**Windows**:
```cmd
# フォルダの権限を確認
icacls "D:\Photos\Inbox"

# 必要に応じて権限を付与
icacls "D:\Photos\Inbox" /grant Users:F
```

**macOS**:
```bash
# フォルダの権限を確認
ls -la /path/to/inbox

# 必要に応じて権限を付与
chmod 755 /path/to/inbox
```

### AI 評価が実行されない

**症状**: 写真は取り込まれるが、星評価が付かない

**診断**:
```bash
# Celery ワーカーが起動しているか確認
ps aux | grep celery  # macOS/Linux
tasklist | findstr celery  # Windows
```

**解決方法**:

#### Celery ワーカーを起動
```bash
cd local_bridge
python start_worker.py
```

#### Redis キューを確認
```bash
redis-cli
> LLEN celery
> LRANGE celery 0 -1
```

#### GPU メモリ不足の場合

`config.json` を編集:
```json
"ai": {
  "gpu_memory_limit_mb": 4096,  # 6144 → 4096
  "enable_quantization": true
}
```

### 現像設定が適用されない

**症状**: AI 評価は完了するが、Lightroom で現像設定が適用されない

**診断**:
```bash
# ジョブキューを確認
curl http://localhost:5100/api/jobs
```

**解決方法**:

#### Lightroom プラグインを確認
1. Lightroom で **ファイル > プラグインマネージャー**
2. Junmai AutoDev が **有効** になっているか確認
3. **ステータス** が「実行中」になっているか確認

#### 仮想コピーを確認

Lightroom で写真を選択し、仮想コピーが作成されているか確認。

#### ドライランモードを確認

`config.json` で `dryRun` が `false` になっているか確認:
```json
"safety": {
  "dryRun": false
}
```

### 書き出しエラー

**症状**: 書き出しが失敗する

**診断**:
```bash
# エラーログを確認
tail -f local_bridge/logs/errors.log
```

**解決方法**:

#### ディスク容量不足
```bash
# 空き容量を確認
# Windows:
dir "D:\Export"
# macOS:
df -h /path/to/export
```

#### 書き出し先フォルダが存在しない

`config.json` で指定したフォルダを作成:
```bash
mkdir -p D:\Export\SNS
```

#### 権限エラー

書き出し先フォルダの書き込み権限を確認。

---

## パフォーマンス問題

### 処理が遅い

**症状**: 1 枚の処理に 30 秒以上かかる

**診断**:
```bash
# GPU 使用率を確認
nvidia-smi

# CPU 使用率を確認
# Windows:
taskmgr
# macOS:
top
```

**解決方法**:

#### GPU が使用されていない場合

CUDA が正しくインストールされているか確認:
```bash
python -c "import torch; print(torch.cuda.is_available())"
# True が表示されるべき
```

CUDA をインストール:
```
https://developer.nvidia.com/cuda-downloads
```

#### GPU メモリ不足の場合

`config.json` で量子化を有効化:
```json
"ai": {
  "enable_quantization": true
}
```

#### 同時実行ジョブ数を減らす

`config.json` を編集:
```json
"processing": {
  "max_concurrent_jobs": 1  # 3 → 1
}
```

#### LLM モデルを軽量化

`config.json` を編集:
```json
"ai": {
  "llm_model": "llama3.1:8b-instruct"  # 11b → 8b
}
```

### メモリ不足

**症状**:
```
MemoryError: Unable to allocate array
```

**解決方法**:

#### システムメモリを確認
```bash
# Windows:
systeminfo | findstr "Physical Memory"
# macOS:
sysctl hw.memsize
```

#### 画像キャッシュをクリア
```bash
cd local_bridge
python -c "from cache_manager import CacheManager; CacheManager().clear_all()"
```

#### Redis メモリ制限を設定

`redis.conf` を編集:
```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### GPU 温度が高い

**症状**: GPU 温度が 80°C を超える

**解決方法**:

#### GPU 温度制限を設定

`config.json` を編集:
```json
"processing": {
  "gpu_temp_limit_celsius": 70  # 75 → 70
}
```

#### 冷却を改善
- PC ケースの通気を確認
- GPU ファンの清掃
- 室温を下げる

#### 処理速度を制限

`config.json` を編集:
```json
"processing": {
  "max_concurrent_jobs": 1,
  "cpu_limit_percent": 60
}
```

---

## Lightroom 連携

### カタログがロックされている

**症状**:
```
ERROR: Catalog is locked by another process
```

**解決方法**:

1. Lightroom Classic を完全に終了
2. タスクマネージャーで `Lightroom.exe` が残っていないか確認
3. カタログの `.lock` ファイルを削除:
   ```
   D:\Lightroom\Catalog.lrcat.lock
   ```
4. Lightroom を再起動

### 仮想コピーが作成されない

**症状**: 元の写真に直接適用されてしまう

**解決方法**:

`config.json` で仮想コピーを強制:
```json
"safety": {
  "snapshot": true,
  "virtual_copy": true
}
```

### スナップショットが作成されない

**症状**: 失敗時に元に戻せない

**解決方法**:

プラグインの設定を確認:

`JunmaiAutoDev.lrdevplugin/Main.lua` を編集:
```lua
CREATE_SNAPSHOT = true
```

---

## AI・LLM 関連

### LLM の応答が遅い

**症状**: AI 評価に 1 分以上かかる

**解決方法**:

#### モデルを軽量化
```bash
# 8B モデルに変更
ollama pull llama3.1:8b-instruct
```

`config.json` を編集:
```json
"ai": {
  "llm_model": "llama3.1:8b-instruct"
}
```

#### GPU を使用しているか確認
```bash
# Ollama のログを確認
ollama ps
```

GPU が使用されていない場合:
```bash
# CUDA 版の Ollama を再インストール
```

### LLM の評価が不正確

**症状**: 明らかに良い写真が低評価になる

**解決方法**:

#### 選別閾値を調整

`config.json` を編集:
```json
"ai": {
  "selection_threshold": 3.0  # 3.5 → 3.0（寛容に）
}
```

#### プロンプトを調整

`local_bridge/ai_selector.py` の評価プロンプトをカスタマイズ。

#### 学習データを蓄積

承認・却下を繰り返すことで、徐々に精度が向上します。

### 顔検出が機能しない

**症状**: ポートレート写真で顔が検出されない

**解決方法**:

#### OpenCV モデルを確認
```bash
cd local_bridge
python -c "import cv2; print(cv2.__version__)"
```

#### モデルファイルをダウンロード
```bash
cd local_bridge/models
wget https://github.com/opencv/opencv/raw/master/data/haarcascades/haarcascade_frontalface_default.xml
```

---

## ネットワーク・通信

### モバイル Web UI にアクセスできない

**症状**: スマートフォンから `http://[IP]:5100` にアクセスできない

**診断**:
```bash
# サーバーが起動しているか確認
curl http://localhost:5100/api/system/status
```

**解決方法**:

#### ファイアウォールを確認

**Windows**:
1. Windows Defender ファイアウォール を開く
2. **詳細設定** → **受信の規則**
3. ポート 5100 を許可する規則を追加

**macOS**:
```bash
# ファイアウォールを一時的に無効化してテスト
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

#### IP アドレスを確認

**Windows**:
```cmd
ipconfig
```

**macOS**:
```bash
ifconfig | grep "inet "
```

正しい IP アドレスでアクセスしているか確認。

#### 同じネットワークに接続しているか確認

デスクトップとスマートフォンが同じ Wi-Fi に接続されているか確認。

### WebSocket 接続エラー

**症状**: リアルタイム更新が機能しない

**診断**:
```javascript
// ブラウザのコンソールで確認
WebSocket connection to 'ws://localhost:5100/ws' failed
```

**解決方法**:

#### WebSocket サーバーが起動しているか確認
```bash
# ログを確認
tail -f local_bridge/logs/main.log | grep WebSocket
```

#### プロキシ・VPN を無効化

プロキシや VPN が WebSocket をブロックしている可能性があります。

#### ブラウザのキャッシュをクリア

Ctrl+Shift+Delete でキャッシュをクリア。

---

## データベース

### データベースが破損した

**症状**:
```
sqlite3.DatabaseError: database disk image is malformed
```

**解決方法**:

#### バックアップから復元
```bash
cd local_bridge/data
cp backups/processing_YYYYMMDD.db processing.db
```

#### データベースを再構築
```bash
cd local_bridge
python init_database.py --reset
```

**警告**: すべてのデータが失われます。

### マイグレーションエラー

**症状**:
```
alembic.util.exc.CommandError: Can't locate revision
```

**解決方法**:

#### マイグレーション履歴をリセット
```bash
cd local_bridge
alembic stamp head
alembic upgrade head
```

---

## ログの確認方法

### ログファイルの場所

```
local_bridge/logs/
├── main.log          # メインログ
├── performance.log   # パフォーマンスログ
├── errors.log        # エラーログ
├── failsafe.log      # フェイルセーフログ
└── retry.log         # リトライログ
```

### ログの確認コマンド

#### リアルタイムでログを監視

**Windows**:
```cmd
powershell Get-Content local_bridge\logs\main.log -Wait -Tail 50
```

**macOS/Linux**:
```bash
tail -f local_bridge/logs/main.log
```

#### エラーのみを抽出

**Windows**:
```cmd
findstr "ERROR" local_bridge\logs\main.log
```

**macOS/Linux**:
```bash
grep "ERROR" local_bridge/logs/main.log
```

#### 特定の日時のログを確認

```bash
grep "2025-11-08 14:" local_bridge/logs/main.log
```

### ログレベルの変更

`config.json` を編集:
```json
"system": {
  "log_level": "DEBUG"  # INFO → DEBUG
}
```

---

## よくある質問

### Q: 処理中に PC をスリープさせても大丈夫ですか？

**A**: いいえ、処理が中断されます。スリープを無効化するか、処理完了を待ってください。

### Q: 複数の PC で同じカタログを使用できますか？

**A**: いいえ、Lightroom カタログは同時に 1 つの PC からのみアクセスできます。

### Q: RAW + JPEG で撮影した場合、どちらが処理されますか？

**A**: RAW ファイルが優先されます。JPEG は無視されます。

### Q: 処理済みの写真を再処理できますか？

**A**: はい、セッション管理画面から「再現像」を実行できます。

### Q: 学習データはどこに保存されますか？

**A**: `local_bridge/data/processing.db` の `learning_data` テーブルに保存されます。

### Q: クラウド同期は安全ですか？

**A**: はい、TLS 1.3 で暗号化されます。ただし、機密性の高い写真は同期を無効化することを推奨します。

### Q: 商用利用は可能ですか？

**A**: はい、MIT ライセンスに従って自由に使用できます。

---

## サポートへの問い合わせ

上記の方法で解決しない場合は、以下の情報を添えて GitHub Issues で報告してください:

1. **環境情報**:
   - OS とバージョン
   - Python バージョン
   - GPU モデル
   - Lightroom Classic バージョン

2. **エラーメッセージ**:
   - 完全なエラーメッセージ
   - スタックトレース

3. **ログファイル**:
   - `main.log` の関連部分
   - `errors.log` の内容

4. **再現手順**:
   - エラーが発生する具体的な手順

**GitHub Issues**: https://github.com/your-repo/junmai-autodev/issues

---

© 2025 Junmai AutoDev Project
