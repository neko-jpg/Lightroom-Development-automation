# Junmai AutoDev - PyQt6 Desktop GUI

Junmai AutoDev の新しいデスクトップ GUI（PyQt6 ベース）

## 概要

このディレクトリには、Tkinter から PyQt6 に移行した新しいデスクトップ GUI が含まれています。
モダンな UI、タブベースのインターフェース、ダークテーマ対応を実現しています。

## 要件

- Python 3.11+
- PyQt6 6.7.0+

## インストール

```bash
# PyQt6 のインストール
pip install -r ../requirements.txt

# または個別にインストール
pip install PyQt6==6.7.0
```

## 実行方法

```bash
# gui_qt ディレクトリから実行
cd gui_qt
python main.py

# またはプロジェクトルートから実行
python gui_qt/main.py
```

## プロジェクト構造

```
gui_qt/
├── main.py                 # アプリケーションエントリーポイント
├── main_window.py          # メインウィンドウクラス
├── __init__.py             # パッケージ初期化
├── resources/              # リソースファイル
│   ├── icons/              # アイコン（未実装）
│   ├── styles/             # スタイルシート
│   │   ├── dark_theme.qss  # ダークテーマ
│   │   └── light_theme.qss # ライトテーマ
│   └── README.md           # リソースガイド
└── README.md               # このファイル
```

## 機能

### 実装済み

- ✅ PyQt6 プロジェクト構造
- ✅ メインウィンドウクラス
- ✅ タブベースのインターフェース（6タブ）
  - Dashboard（ダッシュボード）
  - Sessions（セッション管理）
  - Approval（承認キュー）
  - Presets（プリセット管理）
  - Settings（設定）
  - Logs（ログ）
- ✅ ダークテーマ・ライトテーマ対応
- ✅ ステータスバー
- ✅ 定期更新タイマー

### 未実装（今後のタスク）

- ⏳ ダッシュボード画面の実装（Task 24）
- ⏳ セッション管理画面の実装（Task 25）
- ⏳ 承認キュー画面の実装（Task 26）
- ⏳ 設定画面の実装（Task 27）
- ⏳ 統計・レポート画面の実装（Task 28）

## 設計原則

### Requirements: 8.1

本 GUI は以下の要件を満たします：

- デスクトップ通知対応
- システムステータス表示
- セッション管理
- 承認キュー
- 設定管理

### アーキテクチャ

- **MVC パターン**: モデル（データ）、ビュー（UI）、コントローラー（ロジック）の分離
- **シグナル・スロット**: Qt のイベント駆動アーキテクチャを活用
- **非同期処理**: QTimer を使用した定期更新
- **テーマ対応**: QSS（Qt Style Sheets）によるスタイル管理

## 開発ガイド

### 新しいタブの追加

```python
def add_new_tab(self):
    """新しいタブの追加"""
    new_tab = QWidget()
    layout = QVBoxLayout(new_tab)
    
    # ウィジェットの追加
    label = QLabel("New Tab Content")
    layout.addWidget(label)
    
    # タブに追加
    self.tab_widget.addTab(new_tab, "🆕 New Tab")
```

### スタイルシートの適用

```python
# アプリケーション全体にスタイルを適用
with open("resources/styles/dark_theme.qss", "r", encoding="utf-8") as f:
    app.setStyleSheet(f.read())
```

### シグナル・スロットの使用

```python
# ボタンクリックイベント
button = QPushButton("Click Me")
button.clicked.connect(self.on_button_clicked)

def on_button_clicked(self):
    print("Button clicked!")
```

## トラブルシューティング

### PyQt6 がインストールできない

```bash
# pip を最新版にアップグレード
python -m pip install --upgrade pip

# PyQt6 を再インストール
pip install --force-reinstall PyQt6
```

### High DPI 表示がぼやける

main.py で以下の設定が有効になっていることを確認：

```python
app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
```

### スタイルシートが適用されない

- ファイルパスが正しいか確認
- UTF-8 エンコーディングで読み込んでいるか確認
- QSS 構文エラーがないか確認

## 参考資料

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt Style Sheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [Qt Widgets Examples](https://doc.qt.io/qt-6/qtwidgets-index.html)

## ライセンス

このプロジェクトは Junmai AutoDev プロジェクトの一部です。
