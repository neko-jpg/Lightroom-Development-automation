# AGENTS.md — Lightroom×ChatGPT 自動現像システム

> バージョン: 2025-11-08 / ステータス: Draft → RC1

---

## 0. 議論層の宣言（哲学／戦略／実務／創造）

* **哲学**: 感性の再現ではなく**構造の記述**。意図→数値→再現性。曖昧表現は**JSON**へ還元。
* **戦略**: **分業型エージェント**で要件→設計→検証→適用を直列化。LLMは**構造出力＋厳格バリデーション**に限定。
* **実務**: Lightroom Classic（Lua SDK）を前提に、**ローカル・ブリッジ**（Python/Node）＋**ジョブキュー**で非同期実行、**仮想コピー/スナップショット**で安全担保。
* **創造**: 「作風プリセット × シーン診断 × 微調整ルール」の合成。作風は**バージョン管理**しAB評価。

---

## 1. 文書目的

この文書は、本プロジェクトにおける**エージェント群（AGENTS）**の設計・責務・入出力契約（Message Contracts）・評価・運用SOPを定義する。プロジェクト固有の**LrDevConfig v1**スキーマ、Lua/ブリッジ構成、運用ガードレールに準拠する。

---

## 2. 全体アーキテクチャとデータフロー

```
[User/Operator]
   ↓  (自然言語要件)
[01.Requirement-Interpreter] ──▶ 正規化指示（構造化）
   ↓
[02.Config-Synthesizer] ──▶ LrDevConfig v1 JSON（厳格）
   ↓
[03.Schema-Validator] ──▶ バリデーション済みJSON
   ↓
[04.Policy-Gate] ──▶ 安全/既定値注入・上限下限制御
   ↓
[05.Bridge-Orchestrator] ──▶ jobs/inbox/*.json 登録
   ↓
[06.LrC-Executor(Lua)] ──▶ 適用（仮想コピー/スナップショット）
   ↓
[07.QA-Previewer] ──▶ プレビュー/比較キャプチャ
   ↓
[08.Export-Manager] ──▶ 任意の書き出し
   ↓
[09.Auditor] ──▶ ログ/メタ埋め込み/再現性
```

---

## 3. エージェント編成（Roster）

### A1. Requirement-Interpreter（要件正規化）

* **目的**: 写真の状況・作風・制約を**構造化要件**へ変換。
* **入力**: 自然言語プロンプト（被写体/光環境/質感/禁止事項 等）。
* **出力**: `NormalizedSpec v1`（後述）。
* **ベストプラクティス**: 同義語吸収、曖昧語排除、閾値/範囲の明示、**必須/任意/禁止**の三分。

### A2. Config-Synthesizer（設定合成）

* **目的**: `NormalizedSpec v1` から **LrDevConfig v1** を厳密生成。
* **入出力**: 入力=NormalizedSpec v1、出力=LrDevConfig v1（JSON）
* **制約**: **順序保証**（base→toneCurve→HSL→detail→effects→calibration→local→preset）。温度は **0–0.3**、決定性重視。

### A3. Schema-Validator（スキーマ検証）

* **目的**: JSON Schema（厳格）による**厳密検証**。
* **動作**: 失敗時は**最大3回再生成**（温度漸減）→失敗なら**人手レビュー・キュー**へ回送。

### A4. Policy-Gate（ポリシー/安全弁）

* **目的**: 露出/彩度等の**上限・下限**、肌色/HSLの**禁止領域**、**ドライラン/ロールバック**フラグの強制。
* **副作用**: 既定値注入（欠落時）と**安全域へのクリップ**。

### A5. Bridge-Orchestrator（投入/進行管理）

* **目的**: `jobs/inbox/`への登録、進行状態のトラッキング、結果収集。
* **I/F**: HTTPエンドポイント or ファイル監視。リトライ/エクスポネンシャルバックオフ。

### A6. LrC-Executor（Lua適用器）

* **目的**: LrDevelopController により順次適用。**仮想コピー**と**スナップショット**をジョブ前に作成。
* **ガード**: **dryRun**時は確定禁止。例外時は**スナップショット復帰**。

### A7. QA-Previewer（品質検査）

* **目的**: ビュー切替/ズーム/比較の**自動キャプチャ**、ヒストグラム/クリッピングの軽量検査。
* **成果物**: `previews/` にPNG保存、ジョブに紐づく計測（例: 平均輝度/スキントーンΔE）。

### A8. Export-Manager（書き出し）

* **目的**: 任意プリセットで書き出し（IG/長辺2048等）。**デフォルトはOFF**。

### A9. Auditor（監査・再現）

* **目的**: 時刻/写真ID/ステージ/値/結果の**構造ログ**。写真メタに**適用JSONの埋め込み**。

---

## 4. メッセージ契約（Message Contracts）

### 4.1 NormalizedSpec v1（Interpreter → Synthesizer）

```json
{
  "scene": {"lighting": "backlit|overcast|indoor|night", "skin": "soft|texture_keep", "blue_sky_bias": "avoid|keep"},
  "style": {"name": "WhiteLayer_Transparency", "version": "v4", "blend": 60},
  "constraints": {"orange_hsl": {"h": -4, "s": -6, "l": 4}, "blue_hsl": {"s": -8, "l": -6}},
  "export": {"enable": false, "preset": "Junmai_IG_2048_long_edge"},
  "safety": {"dryRun": true, "snapshot": true}
}
```

### 4.2 LrDevConfig v1（Synthesizer → Validator → Gate → Orchestrator）

* 既存スキーマに準拠。`pipeline[].stage` は限定列挙、数値は範囲制約。

### 4.3 Bridge API（Orchestrator ↔ Executor）

* `POST /job` → `{"jobId": "..."}`
* `GET /job/next` → 次ジョブ払い出し
* `POST /job/{id}/result` → 実行結果（成功/失敗、メトリクス、プレビュー参照）

---

## 5. プロンプト指針（最新ベストプラクティス）

* **役割宣言**: 各エージェントは**職能と出力フォーマットを冒頭に固定**。
* **構造出力強制**: `response_format=json_schema`/GBNF 等を活用し**厳密JSON**のみを許容。
* **決定性**: `temperature 0–0.3 / top_p ≤ 0.9 / seed固定可`。再現性のため**乱数要素を禁止**。
* **禁則語**: 「少し」「いい感じ」等の曖昧語は**閾値付き**で再記述。単位（K, EV, %）は必須。
* **長さ制限**: トークン上限の70%でサマリ＋本体の二層構造（途中切断回避）。
* **再試行規則**: バリデーションNG時は**差分説明＋再生成**。3回超は**人手レビュー**へ。

---

## 6. スキーマ/バリデーション

* **JSON Schema**で`required/enum/minimum/maximum`を徹底。
* **スキントーン安全域**: `HSL.orange.sat ∈ [-20, +10]` など**クリップ**規則をGateで適用。
* **順序保証**: `pipeline` の段階不整合は**自動並べ替え**ではなく**エラー**。

---

## 7. 安全・ガードレール

* **ドライラン既定ON**、本番は明示フラグ必須。
* **仮想コピー + スナップショット**をジョブ前に作成し、失敗時は**即復帰**。
* **プリセット“ブレンド”**は擬似（スライダー再調整で近似）。
* **上限**例: Exposure∈[-1.5,+1.5], Clarity∈[-20,+20], Dehaze∈[-10,+10]。
* **PII/機微情報の取り扱い**: ローカルのみ。クラウド送信禁止オプションを明示。

---

## 8. 観測性（Observability）

* **構造ログ**: `time(JST)/jobId/photoId/stage/param/value/result(ms)`
* **メトリクス**: 処理時間、失敗率、再実行率、Δ露出、Δ彩度、スキントーンΔE。
* **可視化**: 日次レポートと失敗トップN、作風別の効果量。

---

## 9. 失敗設計（SRE観点）

* **リトライ**: 一時失敗は指数バックオフ（最大3）/ 永続失敗は**人手キュー**。
* **アイドポテンシ**: jobIdの**重複投入検知**。同一jobIdは**再適用不可**。
* **タイムアウト**: ステージ単位で上限（例: 15s/写真）。
* **フェイルセーフ**: 途中失敗は**スナップショット復帰**で原状回復。

---

## 10. プロバイダ適配（Provider Adapters）

* **対象**: Gemini / Ollama / LM Studio / llama.cpp 等。
* **共通規則**: JSON Schema厳格、温度低、再試行3回、**決定性重視**。
* **切替**: 環境変数 or 設定ファイルで選択。レート制御はキューで吸収。

---

## 11. セキュリティ/プライバシー

* **APIキー**は環境変数のみ。設定画面やログへ平文出力を禁止。
* **データ保全**: ローカル保存のJSON/ログはローテーション（日次）＋暗号化オプション。
* **権限**: 実行ユーザは最小権限。書き出し先はプロジェクト専用ディレクトリ。

---

## 12. 運用SOP（抜粋）

1. `_INBOX_YYYY-MM-DD` コレクションを作成し写真投入。
2. NormalizedSpec v1 を記述（テンプレート付）。
3. Config-Synthesizerで LrDevConfig v1 を生成。
4. Validator→Gate を通過後、`dryRun=true`で投入。
5. QAプレビューを確認→問題なければ `dryRun=false` で本番。
6. 書き出しが必要な場合のみ Export を有効化。
7. 日次でログとメトリクスをレビュー。

---

## 13. 評価/Evals

* **静的評価**: スキーマ合致率、ガード違反率、差分シミュレーション。
* **動的評価**: ゴールデンセット（代表50枚）で**目視＋数値**の二重評価。
* **AB**: 作風 v4 vs v4.1、ゲート閾値の影響分析。

---

## 14. テンプレート（実務用）

### 14.1 NormalizedSpec v1 テンプレ

```json
{
  "scene": {"lighting": "backlit", "skin": "soft", "blue_sky_bias": "avoid"},
  "style": {"name": "WhiteLayer_Transparency", "version": "v4", "blend": 60},
  "constraints": {
    "orange_hsl": {"h": -4, "s": -6, "l": 4},
    "blue_hsl": {"s": -8, "l": -6},
    "tone_curve": [[0,0],[28,22],[64,60],[190,192],[255,255]]
  },
  "export": {"enable": false, "preset": "Junmai_IG_2048_long_edge"},
  "safety": {"dryRun": true, "snapshot": true}
}
```

### 14.2 エージェント用プロンプト雛形（抜粋）

**Requirement-Interpreter**

```
あなたは要件正規化エージェントです。曖昧語を排し、NormalizedSpec v1 をJSONのみで出力します。
- 必須: scene/style/constraints/export/safety
- 単位: 温度K, 量% 明示
- 禁止: 自然言語の説明、補足文、コードブロック外出力
```

**Config-Synthesizer**

```
あなたは設定合成エージェントです。NormalizedSpec v1 を LrDevConfig v1 に変換します。
- 順序: base→toneCurve→HSL→detail→effects→calibration→local→preset
- 範囲: Gateの上限/下限を前提に生成
- 出力: JSONのみ
```

---

## 15. 変更管理（Versioning）

* **LrDevConfig**: `version` を必須。互換性破壊はメジャー更新（v2）。
* **作風**: `WhiteLayer_Transparency_v4.xmp` など**ファイル名と内部タグ**で整合。
* **プロンプト**: Gitで管理、変更理由と評価結果をコミットメッセージに残す。

---

## 16. 付録：代表的なガード値（例）

| パラメータ         |  既定 |   下限 |   上限 | 備考            |
| ------------- | --: | ---: | ---: | ------------- |
| Exposure (EV) | 0.0 | -1.5 | +1.5 | 被写体保持のため極端値禁止 |
| Highlights    |   0 |  -50 |  +20 | 白飛び抑制         |
| Shadows       |   0 |  -10 |  +40 | 顔陰影維持         |
| Clarity       |   0 |  -20 |  +20 | 肌荒れ抑制         |
| Dehaze        |   0 |  -10 |  +10 | 空色過剰防止        |
| Vibrance      |   0 |  -10 |  +15 | 彩度暴発防止        |

---

## 17. 用語集

* **LrDevConfig v1**: 本プロジェクトの現像指示JSON仕様。
* **dryRun**: 仮適用モード（確定書き換え禁止）。
* **Gate**: 安全域と既定値の注入器。

---

## 18. 既知の制約

* ローカル・ブラシ等の完全自動は難しく、**プリセット＋不透明度相当**で近似。
* Lightroom Classic SDKは受信サーバが建てられないため、**ローカル・ブリッジ必須**。

---

## 19. リリース計画（RC1 → GA）

1. ゴールデンセット50枚でE2E（dryRun）
2. 失敗トップN改善（Gate/Prompt修正）
3. 本番適用（25%→50%→100%ロールアウト）
4. GA後は週次でメトリクスレビューと作風AB

---

© 2025 Lightroom×ChatGPT Auto-Develop System — Agents Specification