# Junmai AutoDev クイックリファレンス

## 🚀 5 分でわかる Junmai AutoDev

### システム起動

```bash
# 1. Redis を起動
redis-server

# 2. Ollama を起動
ollama serve

# 3. バックエンドサーバーを起動
cd local_bridge
python app.py

# 4. Celery ワーカーを起動（別ターミナル）
python start_worker.py

# 5. デスクトップ GUI を起動（オプション）
cd gui_qt
python main.py
```

---

## 📸 基本ワークフロー

1. **写真をコピー** → ホットフォルダー（例: `D:/Photos/Inbox`）
2. **自動処理** → 取り込み・選別・現像（バックグラウンド）
3. **承認** → GUI で確認・承認
4. **書き出し** → 自動書き出し（オプション）

---

## ⌨️ キーボードショートカット

### 承認キュー

| キー | アクション |
|------|-----------|
| → | 次の写真 |
| ← | 前の写真 |
| Enter | 承認 |
| Delete | 却下 |
| Space | スキップ |
| E | Lightroom で編集 |

---

## 🔧 よく使う設定

### config.json の場所
```
local_bridge/config/config.json
```

### AI 設定

```json
"ai": {
  "llm_model": "llama3.1:8b-instruct",
  "selection_threshold": 3.5,
  "gpu_memory_limit_mb": 6144
}
```

### 処理設定

```json
"processing": {
  "auto_import": true,
  "auto_select": true,
  "auto_develop": true,
  "max_concurrent_jobs": 3
}
```

---

## 🐛 トラブルシューティング

### Redis 接続エラー
```bash
redis-cli ping  # PONG が返ればOK
```

### Ollama 接続エラー
```bash
ollama list  # モデル一覧が表示されればOK
```

### GPU が認識されない
```bash
nvidia-smi  # GPU 情報が表示されればOK
```

### ログ確認
```bash
# Windows
powershell Get-Content local_bridge\logs\main.log -Wait -Tail 50

# macOS/Linux
tail -f local_bridge/logs/main.log
```

---

## 📊 星評価の意味

| 星 | 評価 | アクション |
|----|------|-----------|
| ★★★★★ | 傑作 | 即採用 |
| ★★★★☆ | 優秀 | 採用推奨 |
| ★★★☆☆ | 良好 | 条件付き |
| ★★☆☆☆ | 平凡 | 要検討 |
| ★☆☆☆☆ | 不良 | 不採用 |

---

## 🌐 モバイルアクセス

```
http://[デスクトップのIPアドレス]:5100
```

### IP アドレスの確認

**Windows**:
```cmd
ipconfig
```

**macOS**:
```bash
ifconfig | grep "inet "
```

---

## 📁 重要なファイル・フォルダ

```
junmai-autodev/
├── local_bridge/
│   ├── config/config.json      # 設定ファイル
│   ├── data/processing.db      # データベース
│   ├── logs/                   # ログファイル
│   └── app.py                  # バックエンドサーバー
├── gui_qt/
│   └── main.py                 # デスクトップ GUI
├── JunmaiAutoDev.lrdevplugin/  # Lightroom プラグイン
└── docs/                       # ドキュメント
```

---

## 🔗 リンク集

- **インストールガイド**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **ユーザーマニュアル**: [USER_MANUAL.md](USER_MANUAL.md)
- **トラブルシューティング**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **FAQ**: [FAQ.md](FAQ.md)
- **GitHub**: https://github.com/your-repo/junmai-autodev
- **Discord**: https://discord.gg/junmai-autodev

---

## 💡 ヒント

### 処理速度を上げる
- GPU を使用
- 軽量モデル（8B）を使用
- 同時実行ジョブ数を増やす

### 精度を上げる
- 学習データを蓄積
- 選別閾値を調整
- カスタムプリセットを作成

### メモリを節約
- 量子化を有効化
- GPU メモリ制限を設定
- キャッシュを定期的にクリア

---

© 2025 Junmai AutoDev Project
