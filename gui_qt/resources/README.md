# Junmai AutoDev - Resources Directory

このディレクトリには、GUI アプリケーションで使用するリソースファイルを格納します。

## ディレクトリ構造

```
resources/
├── icons/          # アイコンファイル
│   ├── app_icon.png       # アプリケーションアイコン (256x256)
│   ├── dashboard.png      # ダッシュボードアイコン
│   ├── sessions.png       # セッションアイコン
│   ├── approval.png       # 承認アイコン
│   ├── presets.png        # プリセットアイコン
│   ├── settings.png       # 設定アイコン
│   └── logs.png           # ログアイコン
├── styles/         # スタイルシート
│   ├── dark_theme.qss     # ダークテーマ
│   └── light_theme.qss    # ライトテーマ
└── README.md       # このファイル
```

## アイコンについて

アイコンファイルは以下の仕様で作成してください：

- **フォーマット**: PNG (透過背景推奨)
- **サイズ**: 
  - アプリケーションアイコン: 256x256px
  - タブアイコン: 32x32px または 64x64px
- **カラー**: ダークテーマとライトテーマの両方で視認性の高い色

### アイコン作成のヒント

1. **無料アイコンリソース**:
   - [Heroicons](https://heroicons.com/) - MIT ライセンス
   - [Feather Icons](https://feathericons.com/) - MIT ライセンス
   - [Material Icons](https://fonts.google.com/icons) - Apache 2.0

2. **アイコン生成ツール**:
   - [Figma](https://www.figma.com/) - 無料プラン利用可能
   - [Inkscape](https://inkscape.org/) - オープンソース

3. **プレースホルダー**:
   - アイコンがない場合、アプリケーションは絵文字をフォールバックとして使用します
   - 例: 📊 (Dashboard), 📁 (Sessions), ✅ (Approval)

## スタイルシートについて

### ダークテーマ (dark_theme.qss)
- 背景色: #1e1e1e (濃いグレー)
- テキスト色: #e0e0e0 (明るいグレー)
- アクセント色: #0078d4 (青)

### ライトテーマ (light_theme.qss)
- 背景色: #f5f5f5 (明るいグレー)
- テキスト色: #333333 (濃いグレー)
- アクセント色: #0078d4 (青)

### カスタマイズ

スタイルシートは Qt Style Sheets (QSS) 形式で記述されています。
CSS に似た構文で、Qt ウィジェットの外観をカスタマイズできます。

詳細は [Qt Style Sheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html) を参照してください。

## 使用方法

```python
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# アイコンの設定
app.setWindowIcon(QIcon("resources/icons/app_icon.png"))

# スタイルシートの適用
with open("resources/styles/dark_theme.qss", "r") as f:
    app.setStyleSheet(f.read())
```

## ライセンス

このプロジェクトで使用するアイコンやリソースは、各ライセンスに従ってください。
商用利用可能なライセンス（MIT, Apache 2.0 等）を推奨します。
