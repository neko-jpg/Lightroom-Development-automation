# Junmai AutoDev: Lightroom × LLM 自動現像システム

## 概要

**Junmai AutoDev**は、大規模言語モデル（LLM）を活用して、Adobe Lightroom Classicの現像設定を自動化するシステムです。ユーザーが「透明感のあるポートレート」のような自然言語で指示を出すと、システムがそれを解析し、Lightroomの現像パラメータに変換して自動的に適用します。

このプロジェクトは、Lightroomプラグイン（Lua）、ローカルAPIブリッジ（Python/Flask）、そしてローカルLLM（Ollama）を組み合わせて実現されています。

## アーキテクチャ

システムは以下の3つの主要コンポーネントで構成されています。

```
[GUI (Python/Tkinter)] -> [ローカル・ブリッジ (Python/Flask)] <-> [Ollama LLM]
                                     ^
                                     | (HTTP Polling)
                                     v
                  [Lightroom Classic プラグイン (Lua)]
```

1.  **GUI (`gui.py`)**: ユーザーがプロンプトを入力し、ブリッジサーバーに送信するためのシンプルなデスクトップアプリケーションです。
2.  **ローカル・ブリッジ (`local_bridge/`)**:
    *   GUIからプロンプトを受け取ります。
    *   Ollamaで実行されているLLMにプロンプトを渡し、`LrDevConfig v1`形式のJSON現像設定を生成させます。
    *   生成された設定をジョブとしてキューに追加し、Lightroomプラグインからのリクエストを待ちます。
3.  **Lightroom プラグイン (`JunmaiAutoDev.lrdevplugin/`)**:
    *   Lightroom内で動作し、定期的にローカル・ブリッジに新しいジョブがないか問い合わせます（ポーリング）。
    *   新しいジョブがあれば取得し、そのJSON設定に基づいて、現在選択されている写真に現像設定を適用します。
    *   安全のため、元の写真を保護する仮想コピーを作成してから編集を行います。

## セットアップ手順

### 必要なもの

*   **Adobe Lightroom Classic**: バージョン 12以上。
*   **Python**: 3.10以上。
*   **Ollama**: `llama3.1:8b-instruct`のような互換性のあるモデルがローカルで実行されていること。

### 1. ローカル・ブリッジサーバーのセットアップ

まず、APIサーバーを起動します。

```bash
# 1. 依存関係をインストール
pip install -r local_bridge/requirements.txt

# 2. サーバーを起動
python local_bridge/app.py
```

サーバーはデフォルトで `http://127.0.0.1:5100` で起動します。

### 2. Lightroom プラグインのインストール

1.  Lightroom Classicを開き、`ファイル > プラグインマネージャー` を選択します。
2.  `追加`ボタンをクリックし、このリポジトリ内にある`JunmaiAutoDev.lrdevplugin`フォルダを選択します。
3.  プラグインがリストに表示され、緑色のステータスアイコンが点灯していれば有効化されています。`完了`をクリックします。

## 使用方法

1.  **Ollamaを起動**: `ollama serve`コマンドなどで、LLMが利用可能な状態になっていることを確認してください。
2.  **ブリッジサーバーを起動**: 上記の手順に従って、`python local_bridge/app.py`を実行します。
3.  **GUIを起動**: 別のターミナルで、`python gui.py`を実行してプロンプト入力画面を開きます。
4.  **プロンプトを送信**: GUIのテキストエリアに「逆光の秋のポートレート、透明感と柔らかな肌の質感で」のような指示を入力し、`Submit to Lightroom`ボタンをクリックします。
5.  **Lightroomで適用**:
    *   Lightroom Classicで、現像したい写真を選択し、`現像`モジュールを開きます。
    *   プラグインがバックグラウンドでサーバーに問い合わせ、数秒以内に新しいジョブを見つけて自動的に適用を開始します。
    *   `JunmaiAutoDev Edit`という名前の仮想コピーが作成され、そこに設定が適用されます。

以上で、LLMによる自動現像が完了します。
