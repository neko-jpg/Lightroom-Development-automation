# Approval Queue User Guide
承認キュー機能ガイド

## 概要

承認キュー画面は、AI自動現像された写真を確認・承認するための統合インターフェースです。Before/After比較、AI評価スコア、適用パラメータの詳細を一画面で確認でき、キーボードショートカットで高速に操作できます。

## 画面構成

```
┌─────────────────────────────────────────────────────────────┐
│ Approval Queue (12 photos pending)          Photo 1 of 12  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────┐            │
│ │                     │ │                     │            │
│ │   Before (Original) │ │   After (Processed) │  AI Score  │
│ │                     │ │                     │  ★★★★☆ 4.2│
│ │   [Photo Display]   │ │   [Photo Display]   │            │
│ │                     │ │                     │  Details:  │
│ │                     │ │                     │  Focus: 4.5│
│ └─────────────────────┘ └─────────────────────┘  Exp: 4.0  │
│                                                   Comp: 4.3 │
│                                                              │
│                                                   Context:  │
│                                                   Backlit   │
│                                                   Portrait  │
│                                                              │
│                                                   Preset:   │
│                                                   WhiteLayer│
│                                                   v4 (60%)  │
│                                                              │
│                                                   Params:   │
│                                                   [Details] │
├─────────────────────────────────────────────────────────────┤
│  [✓ Approve] [✗ Reject] [✏️ Modify] [⏭️ Skip]              │
├─────────────────────────────────────────────────────────────┤
│ Keyboard: ← Previous | → Next | Enter Approve | Del Reject │
└─────────────────────────────────────────────────────────────┘
```

## 主要機能

### 1. 写真比較表示
- **Before**: 元の写真（現像前）
- **After**: AI現像後の写真
- 並列表示で変化を一目で確認

### 2. AI評価スコア
- **Overall Score**: 総合評価（1-5星）
- **Focus Score**: ピント精度
- **Exposure Score**: 露出適正
- **Composition Score**: 構図バランス
- **Subject Type**: 被写体タイプ（Portrait, Landscape等）
- **Detected Faces**: 検出された顔の数

### 3. 適用パラメータ詳細
- **Context**: 撮影コンテキスト（Backlit Portrait等）
- **Preset**: 適用されたプリセット名とブレンド率
- **Adjustments**: 詳細な調整パラメータ
  - 基本調整（Exposure, Highlights, Shadows等）
  - HSL調整（色相、彩度、輝度）
  - トーンカーブ

### 4. アクションボタン

#### ✓ Approve（承認）
- 写真を承認し、「書き出し待機」ステータスに移行
- 自動的に次の写真へ移動
- ショートカット: `Enter`

#### ✗ Reject（却下）
- 写真を却下
- 代替プリセットの提案（将来実装）
- 自動的に次の写真へ移動
- ショートカット: `Delete`

#### ✏️ Modify（修正）
- パラメータを手動調整（将来実装）
- ショートカット: `M`

#### ⏭️ Skip（スキップ）
- 現在の写真をスキップして次へ
- 後で再度確認可能
- ショートカット: `S`

## キーボードショートカット

| キー | 機能 | 説明 |
|------|------|------|
| `←` | Previous | 前の写真に戻る |
| `→` | Next | 次の写真に進む |
| `Enter` | Approve | 現在の写真を承認 |
| `Delete` | Reject | 現在の写真を却下 |
| `M` | Modify | 修正モードに入る |
| `S` | Skip | 現在の写真をスキップ |

## 使用方法

### 基本ワークフロー

1. **承認キューを開く**
   - メインウィンドウの「✅ Approval」タブをクリック
   - または、ダッシュボードの「Approval Queue」ボタンをクリック

2. **写真を確認**
   - Before/After画像を比較
   - AI評価スコアを確認
   - 適用パラメータを確認

3. **判断を下す**
   - 良い結果 → `Enter`キーで承認
   - 不満足 → `Delete`キーで却下
   - 後で判断 → `S`キーでスキップ

4. **次の写真へ**
   - 自動的に次の写真が表示される
   - または`→`キーで手動移動

### 高速操作のコツ

1. **キーボード中心の操作**
   - マウスを使わず、キーボードだけで完結
   - `→` → 確認 → `Enter` → `→` のリズムで高速処理

2. **スキップ活用**
   - 判断に迷ったら`S`でスキップ
   - 後でまとめて確認

3. **進捗確認**
   - 画面上部の「Photo X of Y」で進捗を把握
   - 残り枚数を意識して効率的に処理

## API連携

承認キューは以下のREST APIエンドポイントと連携します:

### 承認キュー取得
```http
GET /api/approval/queue?limit=100
```

レスポンス:
```json
{
  "photos": [
    {
      "id": 123,
      "file_name": "IMG_5432.CR3",
      "ai_score": 4.2,
      "focus_score": 4.5,
      "exposure_score": 4.0,
      "composition_score": 4.3,
      "subject_type": "Portrait",
      "detected_faces": 2,
      "context_tag": "backlit_portrait",
      "selected_preset": "WhiteLayer_Transparency_v4"
    }
  ],
  "count": 12
}
```

### 写真承認
```http
POST /api/approval/{photo_id}/approve
```

### 写真却下
```http
POST /api/approval/{photo_id}/reject
Content-Type: application/json

{
  "reason": "User rejected"
}
```

## トラブルシューティング

### 写真が表示されない
- **原因**: APIサーバーが起動していない
- **解決**: `local_bridge/app.py`を起動

### 承認/却下が失敗する
- **原因**: ネットワークエラーまたはAPIエラー
- **解決**: エラーメッセージを確認し、APIサーバーのログをチェック

### キーボードショートカットが効かない
- **原因**: フォーカスが他のウィジェットにある
- **解決**: 承認キュー画面をクリックしてフォーカスを戻す

## 今後の機能拡張

### Phase 1: 画像表示
- [ ] 実際のRAW/JPEG画像の読み込み
- [ ] サムネイル生成とキャッシング
- [ ] ズーム/パン機能
- [ ] ヒストグラム表示

### Phase 2: 修正機能
- [ ] パラメータ調整スライダー
- [ ] リアルタイムプレビュー
- [ ] カスタムプリセット保存
- [ ] 調整履歴の記録

### Phase 3: バッチ操作
- [ ] 複数写真の一括承認/却下
- [ ] フィルタリング（スコア、被写体タイプ等）
- [ ] ソート機能
- [ ] タグ付け機能

### Phase 4: 統計・分析
- [ ] 承認率の表示
- [ ] プリセット別の成功率
- [ ] 時間帯別の傾向分析
- [ ] 学習データの可視化

## 関連ドキュメント

- [Task 26 Completion Summary](TASK_26_COMPLETION_SUMMARY.md)
- [Dashboard Layout](DASHBOARD_LAYOUT.md)
- [Session Management Guide](README.md)

## サポート

問題が発生した場合は、以下を確認してください:

1. APIサーバーが起動しているか
2. データベースが初期化されているか
3. 承認待ちの写真が存在するか

詳細なログは`local_bridge/logs/`ディレクトリで確認できます。

---
**最終更新**: 2025-11-09  
**バージョン**: 1.0.0
