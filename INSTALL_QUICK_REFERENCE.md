# Junmai AutoDev - インストール クイックリファレンス

## 🚀 5分でインストール

### Windows

```powershell
# ステップ 1: インストール
.\install_windows.ps1

# ステップ 2: 初期設定
python setup_wizard.py

# ステップ 3: 起動
.\start.ps1
```

### macOS

```bash
# ステップ 1: インストール
chmod +x install_macos.sh && ./install_macos.sh

# ステップ 2: 初期設定
python3 setup_wizard.py

# ステップ 3: 起動
./start.sh
```

## 📋 システム要件

| 項目 | 要件 |
|------|------|
| **OS** | Windows 10/11 (64-bit) または macOS 12+ |
| **CPU** | Intel Core i5 以上 |
| **メモリ** | 16GB RAM 以上 |
| **GPU** | NVIDIA RTX 4060 8GB 以上（推奨） |
| **ストレージ** | 50GB 以上の空き容量 |
| **Python** | 3.9 - 3.11 |

## 🔧 必要なソフトウェア

### 自動インストールされるもの
- ✅ Python 依存パッケージ
- ✅ Ollama + Llama 3.1 モデル（オプション）
- ✅ Redis（オプション）

### 手動でインストールが必要なもの
- ⚠️ Lightroom Classic 12.0+
- ⚠️ Python 3.9-3.11（未インストールの場合）

## 📦 インストールオプション

### 基本インストール
```powershell
# Windows
.\install_windows.ps1

# macOS
./install_macos.sh
```

### カスタムインストール先
```powershell
# Windows
.\install_windows.ps1 -InstallPath "D:\MyApps\JunmaiAutoDev"

# macOS
./install_macos.sh --install-path "$HOME/MyApps/JunmaiAutoDev"
```

### 無人インストール
```powershell
# Windows
.\install_windows.ps1 -Unattended

# macOS
./install_macos.sh --unattended
```

### 依存関係をスキップ
```powershell
# Windows
.\install_windows.ps1 -SkipDependencies

# macOS
./install_macos.sh --skip-dependencies
```

## ⚙️ 初期設定項目

### 必須設定
1. **ホットフォルダー**: 写真を自動監視するフォルダ
2. **Lightroom カタログ**: 使用する .lrcat ファイルのパス

### 推奨設定
3. **LLM モデル**: llama3.1:8b-instruct（デフォルト）
4. **GPU メモリ制限**: 6144 MB（RTX 4060 の場合）
5. **自動処理**: 取り込み、選別、現像を有効化

### オプション設定
6. **書き出しプリセット**: SNS用、印刷用
7. **通知**: デスクトップ、メール、LINE
8. **テーマ**: ダーク/ライト

## 🎯 インストール後の確認

### 依存関係チェック
```bash
python check_dependencies.py
```

### 期待される出力
```
✓ Python 3.11.5 (compatible)
✓ flask: 3.0.0
✓ sqlalchemy: 2.0.23
✓ Redis: 7.0.0
✓ Ollama: 3 models available
✓ GPU: NVIDIA GeForce RTX 4060 (8.0 GB)
```

## 🚦 起動方法

### GUI を起動
```powershell
# Windows
.\start.ps1

# macOS
./start.sh
```

### 個別コンポーネントを起動

#### バックエンドサーバー
```bash
cd local_bridge
python app.py
```

#### Celery ワーカー
```bash
cd local_bridge
python start_worker.py
```

#### デスクトップ GUI
```bash
cd gui_qt
python main.py
```

## 🔍 トラブルシューティング

### "Python が見つかりません"
```bash
# バージョン確認
python --version  # Windows
python3 --version # macOS

# インストール
# Windows: https://www.python.org/downloads/
# macOS: brew install python@3.11
```

### "Redis に接続できません"
```bash
# 起動確認
# Windows: Get-Service redis*
# macOS: brew services list

# 起動
# Windows: redis-server
# macOS: brew services start redis
```

### "Ollama に接続できません"
```bash
# 起動確認
# Windows: Get-Process ollama
# macOS: pgrep ollama

# 起動
ollama serve
```

### "GPU が検出されません"
```bash
# NVIDIA ドライバー確認
nvidia-smi

# PyTorch で確認
python -c "import torch; print(torch.cuda.is_available())"
```

## 🗑️ アンインストール

### データを保持してアンインストール
```powershell
# Windows
.\uninstall_windows.ps1 -KeepData

# macOS
./uninstall_macos.sh --keep-data
```

### 完全アンインストール
```powershell
# Windows
.\uninstall_windows.ps1

# macOS
./uninstall_macos.sh
```

## 📞 サポート

### ドキュメント
- 📖 [詳細インストールガイド](docs/INSTALLATION_GUIDE.md)
- 📖 [ユーザーマニュアル](docs/USER_MANUAL.md)
- 📖 [トラブルシューティング](docs/TROUBLESHOOTING.md)
- 📖 [FAQ](docs/FAQ.md)

### コミュニティ
- 💬 GitHub Issues
- 💬 Discord サーバー
- 💬 公式フォーラム

## 🎓 次のステップ

1. ✅ インストール完了
2. ✅ 初期設定完了
3. ✅ 依存関係確認
4. ⏭️ [ユーザーマニュアル](docs/USER_MANUAL.md)を読む
5. ⏭️ テスト写真で動作確認
6. ⏭️ 本番環境で使用開始

---

**最終更新**: 2025-11-09  
**バージョン**: 2.0
