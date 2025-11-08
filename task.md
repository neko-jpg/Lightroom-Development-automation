# Lightroom × ChatGPT 自動現像システム 進捗管理

プロジェクト全体のタスクリストです。

## フェーズ1: ローカル・ブリッジ APIサーバーの開発

-   [x] プロジェクトの初期設定 (ディレクトリ、依存関係)
-   [x] Ollama通信モジュールの実装 (`ollama_client.py`)
-   [x] `LrDevConfig v1` JSONスキーマの定義 (`schema.py`)
-   [x] JSONスキーマ検証機能の実装 (`validator.py`)
-   [x] FlaskによるAPIサーバーの実装 (`app.py`)
-   [x] 動作確認用のテストスクリプト作成 (`test_api.py`)
-   [x] `.gitignore` の作成と不要ファイルの整理

## フェーズ2: Lightroom Classic プラグインの開発 (Lua)

-   [x] プラグインの基本構造作成 (`.lrdevplugin`)
-   [x] ローカル・ブリッジへのポーリング機能実装
-   [x] 受信したJSONを展開し、現像設定を適用するロジ-ック (`JobRunner.lua`)
-   [x] `base` `toneCurve` `HSL` `detail` `effects` `calibration`各ステージの適用器を実装
-   [x] 仮想コピーとスナップショットによる安全な適用・ロールバック機能
-   [x] 簡易的なUI（実行ボタン、ステータス表示）の実装

## フェーズ3: 統合と拡張

-   [x] ローカル・ブリッジとLrCプラグインの結合テスト
-   [x] プリセット適用・ブレンド機能の近似実装
-   [x] エラーハンドリングとログ記録の強化
-   [x] 簡易的なGUI（PyQt/Tkinter）によるプロンプト入力画面の作成
-   [x] READMEの作成 (セットアップ手順、使い方)
