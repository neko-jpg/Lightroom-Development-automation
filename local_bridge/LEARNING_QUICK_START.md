# Learning System Quick Start Guide

## 概要

学習システムは、ユーザーの承認・却下履歴を記録し、パラメータパターンを分析して、カスタマイズされたプリセットを自動生成します。

## セットアップ

### 1. データベース初期化

```python
from models.database import init_db

# データベースを初期化（learning_dataテーブルが自動作成されます）
init_db('sqlite:///data/junmai.db')
```

### 2. 学習システムのインポート

```python
from learning_system import LearningSystem

# 学習システムのインスタンスを作成
learning_system = LearningSystem()
```

## 基本的な使い方

### ステップ1: ユーザーフィードバックの記録

#### 承認の記録

```python
# 写真を承認
learning_system.record_approval(
    photo_id=1,
    original_preset='WhiteLayer_Transparency_v4'
)
```

#### 却下の記録

```python
# 写真を却下
learning_system.record_rejection(
    photo_id=2,
    original_preset='WhiteLayer_Transparency_v4',
    reason='露出オーバー'
)
```

#### 修正の記録

```python
# 写真を修正して承認
learning_system.record_modification(
    photo_id=3,
    original_preset='WhiteLayer_Transparency_v4',
    final_preset='WhiteLayer_Transparency_v4',
    parameter_adjustments={
        'Exposure2012': 0.3,      # 露出を+0.3EV調整
        'Highlights2012': -15,    # ハイライトを-15調整
        'Shadows2012': 20         # シャドウを+20調整
    }
)
```

### ステップ2: パターン分析

```python
# 過去90日間のパターンを分析
analysis = learning_system.analyze_parameter_patterns(
    context_tag='backlit_portrait',  # 逆光ポートレート
    preset_name='WhiteLayer_Transparency_v4',
    days=90
)

if analysis['status'] == 'success':
    print(f"サンプル数: {analysis['sample_count']}")
    print(f"承認率: {analysis['approval_rate']:.1%}")
    
    # パラメータ調整の平均値
    for param, stats in analysis['avg_adjustments'].items():
        print(f"{param}: 平均={stats['mean']:.2f}, 中央値={stats['median']:.2f}")
else:
    print(f"データ不足: {analysis['sample_count']}/{analysis['min_required']}サンプル")
```

### ステップ3: カスタマイズプリセットの生成

```python
# カスタマイズされたプリセットを生成
preset_config = learning_system.generate_customized_preset(
    base_preset_name='WhiteLayer_Transparency_v4',
    context_tag='backlit_portrait',
    analysis_days=90
)

if preset_config:
    # データベースに保存
    saved_preset = learning_system.save_customized_preset(preset_config)
    
    print(f"✓ プリセット生成成功!")
    print(f"  名前: {saved_preset.name}")
    print(f"  バージョン: {saved_preset.version}")
    print(f"  承認率: {preset_config['learning_stats']['approval_rate']:.1%}")
else:
    print("⚠ プリセット生成失敗（データ不足または低承認率）")
```

### ステップ4: プリセット効果の評価

```python
# プリセットの効果を評価
evaluation = learning_system.evaluate_preset_effectiveness(
    preset_name='WhiteLayer_Transparency_v4',
    days=30
)

if evaluation['status'] == 'success':
    print(f"使用回数: {evaluation['total_uses']}")
    print(f"承認率: {evaluation['approval_rate']:.1%}")
    print(f"修正率: {evaluation['modification_rate']:.1%}")
    print(f"却下率: {evaluation['rejection_rate']:.1%}")
    print(f"効果スコア: {evaluation['effectiveness_score']:.2f}/1.0")
```

## 実践的なワークフロー

### シナリオ: 100枚の写真を2週間かけて処理

```python
from learning_system import LearningSystem

learning_system = LearningSystem()

# === 1週目: フィードバック収集 ===
print("1週目: ユーザーフィードバックを収集中...")

for photo_id in range(1, 51):  # 50枚処理
    # 80%は承認、15%は修正、5%は却下
    if photo_id % 20 == 0:
        # 却下
        learning_system.record_rejection(
            photo_id=photo_id,
            original_preset='WhiteLayer_Transparency_v4',
            reason='露出が合わない'
        )
    elif photo_id % 7 == 0:
        # 修正
        learning_system.record_modification(
            photo_id=photo_id,
            original_preset='WhiteLayer_Transparency_v4',
            final_preset='WhiteLayer_Transparency_v4',
            parameter_adjustments={
                'Exposure2012': 0.25,
                'Highlights2012': -12
            }
        )
    else:
        # 承認
        learning_system.record_approval(
            photo_id=photo_id,
            original_preset='WhiteLayer_Transparency_v4'
        )

# === 2週目: パターン分析とプリセット生成 ===
print("\n2週目: パターンを分析してカスタムプリセットを生成...")

# パターン分析
analysis = learning_system.analyze_parameter_patterns(
    context_tag='backlit_portrait',
    preset_name='WhiteLayer_Transparency_v4',
    days=14
)

if analysis['status'] == 'success':
    print(f"✓ 分析完了: {analysis['sample_count']}サンプル")
    
    # カスタムプリセット生成
    preset_config = learning_system.generate_customized_preset(
        base_preset_name='WhiteLayer_Transparency_v4',
        context_tag='backlit_portrait',
        analysis_days=14
    )
    
    if preset_config:
        saved_preset = learning_system.save_customized_preset(preset_config)
        print(f"✓ カスタムプリセット生成: {saved_preset.name}")
        
        # === 3週目: 新しいプリセットで処理 ===
        print("\n3週目: 新しいプリセットを使用...")
        
        for photo_id in range(51, 101):  # 残り50枚
            # 新しいプリセットで処理
            learning_system.record_approval(
                photo_id=photo_id,
                original_preset=saved_preset.name
            )
        
        # 効果を評価
        evaluation = learning_system.evaluate_preset_effectiveness(
            preset_name=saved_preset.name,
            days=7
        )
        
        print(f"\n✓ 新プリセットの効果:")
        print(f"  承認率: {evaluation['approval_rate']:.1%}")
        print(f"  効果スコア: {evaluation['effectiveness_score']:.2f}")
```

## データのバックアップと復元

### バックアップ

```python
# 学習データをエクスポート
result = learning_system.export_learning_data(
    output_path='data/learning_backup_20251108.json',
    days=None  # 全期間
)

print(f"✓ {result['total_records']}件のデータをバックアップしました")
```

### 復元

```python
# 学習データをインポート
result = learning_system.import_learning_data(
    input_path='data/learning_backup_20251108.json'
)

print(f"✓ {result['imported_count']}件のデータをインポートしました")
print(f"  スキップ: {result['skipped_count']}件（重複）")
print(f"  エラー: {result['error_count']}件")
```

## 学習システムのサマリー

```python
# 過去30日間のサマリーを取得
summary = learning_system.get_learning_summary(days=30)

print(f"総レコード数: {summary['total_records']}")
print(f"承認: {summary['approved_count']}")
print(f"却下: {summary['rejected_count']}")
print(f"修正: {summary['modified_count']}")
print(f"全体承認率: {summary['approval_rate']:.1%}")

print("\nプリセット使用統計:")
for preset, count in summary['preset_usage'].items():
    print(f"  {preset}: {count}回")
```

## 設定のカスタマイズ

```python
# 学習システムのパラメータを調整
learning_system = LearningSystem()

# 最小サンプル数を変更（デフォルト: 20）
learning_system.min_samples_for_learning = 30

# 承認率閾値を変更（デフォルト: 0.7 = 70%）
learning_system.approval_threshold = 0.8  # 80%
```

## トラブルシューティング

### データ不足エラー

```python
analysis = learning_system.analyze_parameter_patterns(...)

if analysis['status'] == 'insufficient_data':
    print(f"現在: {analysis['sample_count']}サンプル")
    print(f"必要: {analysis['min_required']}サンプル")
    print("→ もっと多くの写真を処理してください")
```

### 低承認率

```python
preset_config = learning_system.generate_customized_preset(...)

if preset_config is None:
    # パターン分析で承認率を確認
    analysis = learning_system.analyze_parameter_patterns(...)
    if analysis['approval_rate'] < 0.7:
        print(f"承認率が低すぎます: {analysis['approval_rate']:.1%}")
        print("→ プリセットの見直しが必要です")
```

## ベストプラクティス

### 1. 定期的なフィードバック記録
- 写真を処理するたびにフィードバックを記録
- 修正した場合は調整内容も記録

### 2. 十分なデータ収集
- 最低20サンプル（デフォルト）を収集してから分析
- より正確な結果には50-100サンプルが推奨

### 3. コンテキスト別の学習
- 撮影状況（逆光、室内、夜景など）ごとに分析
- コンテキストタグを活用

### 4. 定期的な評価
- 月次でプリセット効果を評価
- 効果スコアが低いプリセットは見直し

### 5. データのバックアップ
- 定期的に学習データをエクスポート
- 重要なマイルストーンでバックアップ

## 次のステップ

1. **実際の写真で試す**: サンプル写真でフィードバックを記録
2. **パターンを確認**: 分析結果を確認して傾向を把握
3. **カスタムプリセット生成**: 十分なデータが集まったら生成
4. **効果を測定**: 新しいプリセットの効果を評価
5. **継続的改善**: 定期的に分析と最適化を繰り返す

## サポート

詳細なドキュメント:
- `LEARNING_SYSTEM_IMPLEMENTATION.md` - 実装の詳細
- `example_learning_usage.py` - 使用例
- `test_learning_system.py` - テストコード

---

**Happy Learning! 📚✨**
