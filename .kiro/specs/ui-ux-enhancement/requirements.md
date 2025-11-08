# Requirements Document

## Introduction

本要件定義書は、Junmai AutoDev（Lightroom × LLM 自動現像システム）の革新的な業務効率化機能の追加に関する要件を定義します。本システムは、趣味でカメラマン並みの撮影・編集を行う写真家の実際のワークフローを深く理解し、**撮影→取り込み→選別→現像→書き出し**という一連の作業における時間的・精神的負担を劇的に削減することを目指します。特に、他業務と並行しながら写真編集を進められる「非同期・自動化」と、余暇時間を最大化する「ゼロタッチ処理」を実現します。

## Glossary

- **System**: Junmai AutoDev システム全体（GUI、ローカル・ブリッジ、Lightroomプラグインを含む）
- **Photographer**: システムを使用する写真家（趣味でカメラマン並みの撮影・編集を行う）
- **Ollama**: ローカルで動作するOSS LLMランタイム（完全無料、APIキー不要）
- **Llama Model**: Meta社のオープンソースLLM（Llama 3.1 8B等、RTX 4060 8GB VRAMで動作）
- **Hot Folder**: 自動監視される取り込みフォルダ（新規写真の自動検知・処理開始）
- **Smart Selection**: AIによる写真の自動選別・評価機能（ローカルAIモデル使用）
- **Workflow Session**: 撮影から書き出しまでの一連の作業セッション
- **Background Processing**: Photographerが他作業中にバックグラウンドで実行される自動現像
- **Approval Queue**: 最終確認が必要な写真のキュー
- **Auto-Export Pipeline**: 現像完了後の自動書き出しと配信
- **Context-Aware Preset**: 撮影状況（時間帯、場所、被写体）を考慮した自動プリセット選択
- **Batch Session**: 複数の撮影セッションをまとめて処理する機能
- **Notification System**: 処理完了や確認要求を通知するシステム
- **Local AI**: ローカルGPU（RTX 4060等）で動作するAIモデル（クラウドAPI不要）

## Requirements

### Requirement 1: ホットフォルダー自動監視と取り込み

**User Story:** Photographerとして、撮影後にSDカードから写真を指定フォルダにコピーするだけで自動的に取り込み・現像が開始されるようにしたいので、ホットフォルダー監視機能が必要です

#### Acceptance Criteria

1. THE System SHALL 設定された監視フォルダ内の新規画像ファイル（RAW、JPEG）を5秒以内に検知する
2. WHEN 新規ファイルが検知された場合、THE System SHALL 自動的にLightroomカタログへ取り込みを実行する
3. THE System SHALL 取り込み時にEXIFデータ（撮影日時、カメラ設定、GPS位置情報）を解析する
4. THE System SHALL 解析されたEXIFデータに基づいて適切なコレクションとキーワードを自動付与する
5. WHEN 取り込みが完了した場合、THE System SHALL 自動的に次の処理ステップ（選別または現像）を開始する

### Requirement 2: AI自動選別とスマート評価

**User Story:** Photographerとして、数百枚の写真から良い写真を手動で選別する時間を削減したいので、AI自動選別機能が必要です

#### Acceptance Criteria

1. THE System SHALL 取り込まれた写真に対して自動的に品質評価（1-5星）を実行する
2. THE System SHALL ピント、露出、構図、被写体の表情を分析して評価スコアを算出する
3. THE System SHALL 類似写真グループを検出し、グループ内で最良の1枚を自動選択する
4. WHEN 評価が完了した場合、THE System SHALL 4星以上の写真を「現像推奨」コレクションに自動追加する
5. THE System SHALL Photographerの過去の採用傾向を学習し、評価精度を向上させる

### Requirement 3: コンテキスト認識型自動現像

**User Story:** Photographerとして、撮影状況に応じた最適な現像設定が自動適用されるようにしたいので、コンテキスト認識機能が必要です

#### Acceptance Criteria

1. THE System SHALL EXIF情報から撮影時刻、天候、場所を判定する
2. THE System SHALL 画像解析により被写体タイプ（ポートレート、風景、スポーツ等）を分類する
3. WHEN 撮影コンテキストが判定された場合、THE System SHALL 対応する最適プリセットを自動選択する
4. THE System SHALL 逆光、夜景、室内など特殊条件を検出し、補正パラメータを自動調整する
5. THE System SHALL 同一セッション内の写真に対して一貫性のある色調を維持する

### Requirement 4: バックグラウンド自動処理エンジン

**User Story:** Photographerとして、他の作業をしている間にバックグラウンドで現像が完了するようにしたいので、非同期処理機能が必要です

#### Acceptance Criteria

1. THE System SHALL Lightroomが起動していない場合でも、バックグラウンドで現像ジョブを実行可能にする
2. THE System SHALL CPU使用率を監視し、Photographerの他作業を妨げないようリソース使用を自動調整する
3. WHEN システムアイドル時間を検知した場合、THE System SHALL 処理速度を最大化する
4. THE System SHALL 処理キューの優先度を自動管理し、緊急度の高いジョブを優先実行する
5. THE System SHALL 処理完了時にデスクトップ通知とメール通知を送信する

### Requirement 5: ワンクリック承認ワークフロー

**User Story:** Photographerとして、現像結果を素早く確認・承認して次の工程に進めたいので、効率的な承認インターフェースが必要です

#### Acceptance Criteria

1. THE System SHALL 現像完了写真を承認キューに自動追加する
2. THE System SHALL 承認画面で現像前後の比較表示を提供する
3. WHEN Photographerが承認ボタンをクリックした場合、THE System SHALL 写真を「書き出し待機」ステータスに移行する
4. WHEN Photographerが却下ボタンをクリックした場合、THE System SHALL 代替プリセットを提案する
5. THE System SHALL キーボードショートカット（矢印キー、Enter、Delete）で高速承認を可能にする

### Requirement 6: 自動書き出しとクラウド配信

**User Story:** Photographerとして、承認後の書き出しと配信を自動化したいので、エクスポートパイプライン機能が必要です

#### Acceptance Criteria

1. THE System SHALL 承認された写真を設定された書き出しプリセット（解像度、形式、品質）で自動書き出しする
2. THE System SHALL 書き出し先を用途別（SNS用、印刷用、アーカイブ用）に複数設定可能にする
3. WHEN 書き出しが完了した場合、THE System SHALL 指定されたクラウドストレージ（Dropbox、Google Drive等）へ自動アップロードする
4. THE System SHALL 書き出しファイル名を撮影日時とシーケンス番号で自動命名する
5. THE System SHALL 書き出し完了後に元のRAWファイルを自動アーカイブする

### Requirement 7: セッション管理とワークフロー追跡

**User Story:** Photographerとして、複数の撮影セッションを並行管理し、各セッションの進捗を把握したいので、セッション管理機能が必要です

#### Acceptance Criteria

1. THE System SHALL 撮影日時とフォルダ構造から自動的にセッションを作成する
2. THE System SHALL 各セッションの進捗状況（取り込み、選別、現像、書き出し）を表示する
3. WHEN Photographerがセッションを選択した場合、THE System SHALL 該当写真のみをフィルタ表示する
4. THE System SHALL セッション単位での一括操作（再現像、書き出し、アーカイブ）を提供する
5. THE System SHALL セッション統計（総枚数、採用率、処理時間）を表示する

### Requirement 8: インテリジェント通知システム

**User Story:** Photographerとして、重要なイベントのみ通知を受け取り、作業の中断を最小限にしたいので、スマート通知機能が必要です

#### Acceptance Criteria

1. THE System SHALL 処理完了、エラー発生、承認要求の3種類の通知を提供する
2. THE System SHALL 通知の緊急度（高、中、低）を自動判定する
3. WHEN 緊急度が高い場合、THE System SHALL デスクトップ通知とサウンドで即座に通知する
4. WHEN 緊急度が低い場合、THE System SHALL 通知をバッファリングし、まとめて表示する
5. THE System SHALL 通知設定（時間帯、種類、方法）をカスタマイズ可能にする

### Requirement 9: モバイルコンパニオンアプリ

**User Story:** Photographerとして、外出先や移動中にスマートフォンで進捗確認と簡易操作をしたいので、モバイルアプリが必要です

#### Acceptance Criteria

1. THE System SHALL モバイルブラウザからアクセス可能なWeb UIを提供する
2. THE Web UI SHALL 現在の処理状況とセッション一覧を表示する
3. THE Web UI SHALL 承認キューの写真をスワイプ操作で承認・却下可能にする
4. THE Web UI SHALL プッシュ通知（PWA）をサポートする
5. THE Web UI SHALL 低帯域環境でも動作するよう最適化する

### Requirement 10: プリセットライブラリとバージョン管理

**User Story:** Photographerとして、作風の進化に合わせてプリセットを改良・管理したいので、バージョン管理機能が必要です

#### Acceptance Criteria

1. THE System SHALL プリセットをバージョン番号付きで保存する
2. THE System SHALL プリセットの変更履歴と適用結果を記録する
3. WHEN 新バージョンのプリセットが作成された場合、THE System SHALL 旧バージョンとの比較レポートを生成する
4. THE System SHALL プリセットのA/Bテスト機能を提供する
5. THE System SHALL 最も効果的なプリセットを統計的に推奨する

### Requirement 11: バッチ再現像とスタイル統一

**User Story:** Photographerとして、過去の写真を新しいプリセットで一括再現像したいので、バッチ再現像機能が必要です

#### Acceptance Criteria

1. THE System SHALL 指定されたコレクションまたは期間の写真を一括選択可能にする
2. THE System SHALL 選択された写真に対して新しいプリセットを一括適用する
3. WHEN バッチ再現像が実行される場合、THE System SHALL 元の設定をスナップショットとして保存する
4. THE System SHALL バッチ処理の進捗と残り時間を表示する
5. THE System SHALL 処理完了後に変更前後の比較レポートを生成する

### Requirement 12: パフォーマンス最適化とリソース管理

**User Story:** Photographerとして、システムが常に高速かつ安定して動作するようにしたいので、パフォーマンス最適化が必要です

#### Acceptance Criteria

1. THE System SHALL 1枚の写真の現像処理を平均5秒以内に完了する
2. THE System SHALL 同時に最大20件のジョブをキューに保持可能にする
3. THE System SHALL メモリ使用量を1GB以下に抑える
4. WHEN システムリソースが不足している場合、THE System SHALL 処理を一時停止し、Photographerに通知する
5. THE System SHALL 定期的にキャッシュとログをクリーンアップする

### Requirement 13: 学習型プリセット最適化

**User Story:** Photographerとして、自分の好みに合わせてシステムが学習・進化するようにしたいので、機械学習機能が必要です

#### Acceptance Criteria

1. THE System SHALL Photographerの承認・却下履歴を記録する
2. THE System SHALL 承認された写真の共通パラメータパターンを分析する
3. WHEN 十分なデータが蓄積された場合、THE System SHALL カスタマイズされたプリセットを自動生成する
4. THE System SHALL 生成されたプリセットの効果を定期的に評価する
5. THE System SHALL 学習データをエクスポート・インポート可能にする

### Requirement 14: エラー回復とフェイルセーフ

**User Story:** Photographerとして、システムエラーが発生しても作業が失われないようにしたいので、堅牢なエラー処理が必要です

#### Acceptance Criteria

1. WHEN 処理中にエラーが発生した場合、THE System SHALL 自動的に3回までリトライする
2. WHEN リトライが失敗した場合、THE System SHALL エラー詳細をログに記録し、Photographerに通知する
3. THE System SHALL 処理中断時に中間状態を保存し、再開可能にする
4. THE System SHALL 定期的に自動バックアップを実行する
5. THE System SHALL システムクラッシュ後の自動復旧機能を提供する

### Requirement 15: 統計とインサイト

**User Story:** Photographerとして、自分の撮影・編集パターンを理解し改善したいので、詳細な統計機能が必要です

#### Acceptance Criteria

1. THE System SHALL 日次・週次・月次の処理統計を表示する
2. THE System SHALL 撮影時間帯、被写体タイプ、使用プリセットの分布を可視化する
3. THE System SHALL 処理時間の推移と効率化効果を数値化する
4. THE System SHALL 最も時間がかかっている工程を特定し、改善提案を表示する
5. THE System SHALL 統計データをPDFレポートとしてエクスポートする




### Requirement 16: 完全無料・オフライン動作保証

**User Story:** Photographerとして、継続的なコストをかけずにシステムを使用したいので、完全無料でオフライン動作する設計が必要です

#### Acceptance Criteria

1. THE System SHALL Ollama + Llama 3.1 8B（またはそれ以上）のOSSモデルを使用する
2. THE System SHALL RTX 4060 8GB VRAMで快適に動作する
3. THE System SHALL OpenAI APIキーやクラウドサービスを一切必要としない
4. THE System SHALL インターネット接続なしで全機能が動作する（初回モデルダウンロード後）
5. THE System SHALL すべてのコンポーネント（Python、Flask、Tkinter、Lightroom SDK）を無料ソフトウェアで構成する

### Requirement 17: GPU最適化とリソース効率

**User Story:** Photographerとして、RTX 4060の性能を最大限活用しつつ、他のアプリケーションも快適に使用したいので、GPU最適化が必要です

#### Acceptance Criteria

1. THE System SHALL LLM推論時にGPUメモリ使用量を6GB以下に制限する
2. THE System SHALL 画像解析（AI選別）時にGPUを効率的に活用する
3. WHEN Photographerが他のGPU使用アプリケーションを起動した場合、THE System SHALL 自動的にGPU使用を抑制する
4. THE System SHALL モデルの量子化（4bit/8bit）オプションを提供し、メモリ使用量を削減可能にする
5. THE System SHALL GPU温度を監視し、過熱時に処理速度を自動調整する

### Requirement 18: マルチモデル対応とモデル管理

**User Story:** Photographerとして、用途に応じて異なるLLMモデルを使い分けたいので、マルチモデル対応が必要です

#### Acceptance Criteria

1. THE System SHALL Llama 3.1 8B、Llama 3.1 11B、Mixtral 8x7Bなど複数のモデルをサポートする
2. THE System SHALL 設定画面でモデルを切り替え可能にする
3. THE System SHALL 各モデルの推奨用途（速度重視、品質重視）を表示する
4. WHEN 新しいモデルが利用可能になった場合、THE System SHALL 通知し、ワンクリックでダウンロード可能にする
5. THE System SHALL モデルごとのパフォーマンス統計（処理時間、品質スコア）を記録する
