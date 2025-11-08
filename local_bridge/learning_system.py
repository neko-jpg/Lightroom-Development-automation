"""
Learning System for Junmai AutoDev.
Implements user feedback learning, parameter pattern analysis, and customized preset generation.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from models.database import LearningData, Photo, Preset, get_session


class LearningSystem:
    """
    学習型最適化システム
    
    ユーザーの承認・却下履歴を記録し、パラメータパターンを分析して
    カスタマイズされたプリセットを自動生成します。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the learning system.
        
        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db = db_session or get_session()
        self.min_samples_for_learning = 20  # 学習に必要な最小サンプル数
        self.approval_threshold = 0.7  # 承認率の閾値
    
    def record_approval(
        self,
        photo_id: int,
        original_preset: str,
        final_preset: Optional[str] = None,
        parameter_adjustments: Optional[Dict] = None
    ) -> LearningData:
        """
        承認履歴を記録する (Requirement 13.1)
        
        Args:
            photo_id: 写真ID
            original_preset: 元のプリセット名
            final_preset: 最終的なプリセット名（修正された場合）
            parameter_adjustments: パラメータ調整内容
        
        Returns:
            LearningData: 記録された学習データ
        """
        # 写真の承認状態を更新
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.approved = True
            photo.approved_at = datetime.utcnow()
        
        # 学習データを記録
        learning_data = LearningData(
            photo_id=photo_id,
            action='approved',
            original_preset=original_preset,
            final_preset=final_preset or original_preset,
            timestamp=datetime.utcnow()
        )
        
        if parameter_adjustments:
            learning_data.set_parameter_adjustments(parameter_adjustments)
        
        self.db.add(learning_data)
        self.db.commit()
        
        return learning_data
    
    def record_rejection(
        self,
        photo_id: int,
        original_preset: str,
        reason: Optional[str] = None
    ) -> LearningData:
        """
        却下履歴を記録する (Requirement 13.1)
        
        Args:
            photo_id: 写真ID
            original_preset: 元のプリセット名
            reason: 却下理由
        
        Returns:
            LearningData: 記録された学習データ
        """
        # 写真の却下状態を更新
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.approved = False
            photo.rejection_reason = reason
            photo.status = 'rejected'
        
        # 学習データを記録
        learning_data = LearningData(
            photo_id=photo_id,
            action='rejected',
            original_preset=original_preset,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(learning_data)
        self.db.commit()
        
        return learning_data
    
    def record_modification(
        self,
        photo_id: int,
        original_preset: str,
        final_preset: str,
        parameter_adjustments: Dict
    ) -> LearningData:
        """
        修正履歴を記録する (Requirement 13.1)
        
        Args:
            photo_id: 写真ID
            original_preset: 元のプリセット名
            final_preset: 修正後のプリセット名
            parameter_adjustments: パラメータ調整内容
        
        Returns:
            LearningData: 記録された学習データ
        """
        # 写真の承認状態を更新（修正後は承認扱い）
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.approved = True
            photo.approved_at = datetime.utcnow()
            photo.selected_preset = final_preset
        
        # 学習データを記録
        learning_data = LearningData(
            photo_id=photo_id,
            action='modified',
            original_preset=original_preset,
            final_preset=final_preset,
            timestamp=datetime.utcnow()
        )
        learning_data.set_parameter_adjustments(parameter_adjustments)
        
        self.db.add(learning_data)
        self.db.commit()
        
        return learning_data
    
    def analyze_parameter_patterns(
        self,
        context_tag: Optional[str] = None,
        preset_name: Optional[str] = None,
        days: int = 90
    ) -> Dict:
        """
        パラメータパターンを分析する (Requirement 13.2)
        
        Args:
            context_tag: 分析対象のコンテキストタグ（オプション）
            preset_name: 分析対象のプリセット名（オプション）
            days: 分析対象期間（日数）
        
        Returns:
            Dict: パラメータパターン分析結果
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 承認または修正されたデータを取得
        query = self.db.query(LearningData, Photo).join(
            Photo, LearningData.photo_id == Photo.id
        ).filter(
            and_(
                LearningData.action.in_(['approved', 'modified']),
                LearningData.timestamp >= cutoff_date
            )
        )
        
        if context_tag:
            query = query.filter(Photo.context_tag == context_tag)
        
        if preset_name:
            query = query.filter(LearningData.original_preset == preset_name)
        
        results = query.all()
        
        if len(results) < self.min_samples_for_learning:
            return {
                'status': 'insufficient_data',
                'sample_count': len(results),
                'min_required': self.min_samples_for_learning
            }
        
        # パラメータ調整の集計
        parameter_stats = defaultdict(list)
        approval_count = 0
        modification_count = 0
        
        for learning_data, photo in results:
            if learning_data.action == 'approved':
                approval_count += 1
            elif learning_data.action == 'modified':
                modification_count += 1
                adjustments = learning_data.get_parameter_adjustments()
                for param, value in adjustments.items():
                    parameter_stats[param].append(value)
        
        # 統計計算
        avg_adjustments = {}
        for param, values in parameter_stats.items():
            if values:
                avg_adjustments[param] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        approval_rate = approval_count / len(results) if results else 0
        
        return {
            'status': 'success',
            'sample_count': len(results),
            'approval_count': approval_count,
            'modification_count': modification_count,
            'approval_rate': approval_rate,
            'avg_adjustments': avg_adjustments,
            'context_tag': context_tag,
            'preset_name': preset_name,
            'analysis_period_days': days
        }
    
    def generate_customized_preset(
        self,
        base_preset_name: str,
        context_tag: str,
        analysis_days: int = 90
    ) -> Optional[Dict]:
        """
        カスタマイズされたプリセットを自動生成する (Requirement 13.3)
        
        Args:
            base_preset_name: ベースとなるプリセット名
            context_tag: コンテキストタグ
            analysis_days: 分析期間（日数）
        
        Returns:
            Dict: 生成されたプリセット設定、または None
        """
        # パターン分析を実行
        analysis = self.analyze_parameter_patterns(
            context_tag=context_tag,
            preset_name=base_preset_name,
            days=analysis_days
        )
        
        if analysis['status'] != 'success':
            return None
        
        # 承認率が閾値を下回る場合は生成しない
        if analysis['approval_rate'] < self.approval_threshold:
            return None
        
        # ベースプリセットを取得
        base_preset = self.db.query(Preset).filter(
            Preset.name == base_preset_name
        ).first()
        
        if not base_preset:
            return None
        
        # ベース設定をコピー
        base_config = base_preset.get_config_template()
        customized_config = json.loads(json.dumps(base_config))  # Deep copy
        
        # 平均調整値を適用
        avg_adjustments = analysis['avg_adjustments']
        
        if 'pipeline' in customized_config:
            for stage in customized_config['pipeline']:
                if 'settings' in stage:
                    for param, adjustment_stats in avg_adjustments.items():
                        if param in stage['settings']:
                            # 中央値を使用（外れ値の影響を減らす）
                            current_value = stage['settings'][param]
                            adjustment = adjustment_stats['median']
                            stage['settings'][param] = current_value + adjustment
        
        # カスタマイズされたプリセット名を生成
        custom_name = f"{base_preset_name}_Custom_{context_tag}"
        
        return {
            'name': custom_name,
            'version': f"learned_{datetime.utcnow().strftime('%Y%m%d')}",
            'base_preset': base_preset_name,
            'context_tag': context_tag,
            'config_template': customized_config,
            'blend_amount': base_preset.blend_amount,
            'learning_stats': {
                'sample_count': analysis['sample_count'],
                'approval_rate': analysis['approval_rate'],
                'analysis_period_days': analysis_days
            }
        }
    
    def save_customized_preset(self, preset_config: Dict) -> Preset:
        """
        カスタマイズされたプリセットをデータベースに保存する
        
        Args:
            preset_config: generate_customized_preset() の戻り値
        
        Returns:
            Preset: 保存されたプリセット
        """
        # 既存のカスタムプリセットを確認
        existing = self.db.query(Preset).filter(
            Preset.name == preset_config['name']
        ).first()
        
        if existing:
            # 更新
            existing.version = preset_config['version']
            existing.set_config_template(preset_config['config_template'])
            existing.blend_amount = preset_config['blend_amount']
            existing.updated_at = datetime.utcnow()
            preset = existing
        else:
            # 新規作成
            preset = Preset(
                name=preset_config['name'],
                version=preset_config['version'],
                blend_amount=preset_config['blend_amount']
            )
            preset.set_config_template(preset_config['config_template'])
            preset.set_context_tags([preset_config['context_tag']])
            self.db.add(preset)
        
        self.db.commit()
        return preset
    
    def evaluate_preset_effectiveness(
        self,
        preset_name: str,
        days: int = 30
    ) -> Dict:
        """
        プリセットの効果を評価する (Requirement 13.4)
        
        Args:
            preset_name: 評価対象のプリセット名
            days: 評価期間（日数）
        
        Returns:
            Dict: 評価結果
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # プリセット使用履歴を取得
        results = self.db.query(LearningData, Photo).join(
            Photo, LearningData.photo_id == Photo.id
        ).filter(
            and_(
                or_(
                    LearningData.original_preset == preset_name,
                    LearningData.final_preset == preset_name
                ),
                LearningData.timestamp >= cutoff_date
            )
        ).all()
        
        if not results:
            return {
                'status': 'no_data',
                'preset_name': preset_name
            }
        
        # 統計計算
        total_uses = len(results)
        approved_count = sum(1 for ld, _ in results if ld.action == 'approved')
        rejected_count = sum(1 for ld, _ in results if ld.action == 'rejected')
        modified_count = sum(1 for ld, _ in results if ld.action == 'modified')
        
        approval_rate = approved_count / total_uses if total_uses > 0 else 0
        modification_rate = modified_count / total_uses if total_uses > 0 else 0
        rejection_rate = rejected_count / total_uses if total_uses > 0 else 0
        
        # AI評価スコアの平均
        ai_scores = [photo.ai_score for _, photo in results if photo.ai_score]
        avg_ai_score = statistics.mean(ai_scores) if ai_scores else None
        
        # コンテキスト別の使用状況
        context_usage = defaultdict(int)
        for _, photo in results:
            if photo.context_tag:
                context_usage[photo.context_tag] += 1
        
        return {
            'status': 'success',
            'preset_name': preset_name,
            'evaluation_period_days': days,
            'total_uses': total_uses,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'modified_count': modified_count,
            'approval_rate': approval_rate,
            'modification_rate': modification_rate,
            'rejection_rate': rejection_rate,
            'avg_ai_score': avg_ai_score,
            'context_usage': dict(context_usage),
            'effectiveness_score': self._calculate_effectiveness_score(
                approval_rate, modification_rate, rejection_rate
            )
        }
    
    def _calculate_effectiveness_score(
        self,
        approval_rate: float,
        modification_rate: float,
        rejection_rate: float
    ) -> float:
        """
        プリセットの効果スコアを計算する
        
        承認率を重視し、修正率と却下率をペナルティとして考慮
        """
        score = (
            approval_rate * 1.0 +
            modification_rate * 0.5 -
            rejection_rate * 1.0
        )
        return max(0.0, min(1.0, score))
    
    def export_learning_data(
        self,
        output_path: str,
        days: Optional[int] = None
    ) -> Dict:
        """
        学習データをエクスポートする (Requirement 13.5)
        
        Args:
            output_path: 出力ファイルパス（JSON）
            days: エクスポート対象期間（日数、Noneの場合は全期間）
        
        Returns:
            Dict: エクスポート結果
        """
        query = self.db.query(LearningData, Photo).join(
            Photo, LearningData.photo_id == Photo.id
        )
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(LearningData.timestamp >= cutoff_date)
        
        results = query.all()
        
        # データを整形
        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'export_period_days': days,
            'total_records': len(results),
            'records': []
        }
        
        for learning_data, photo in results:
            record = {
                'learning_data_id': learning_data.id,
                'photo_id': learning_data.photo_id,
                'action': learning_data.action,
                'original_preset': learning_data.original_preset,
                'final_preset': learning_data.final_preset,
                'parameter_adjustments': learning_data.get_parameter_adjustments(),
                'timestamp': learning_data.timestamp.isoformat(),
                'photo_info': {
                    'file_name': photo.file_name,
                    'context_tag': photo.context_tag,
                    'ai_score': photo.ai_score,
                    'subject_type': photo.subject_type
                }
            }
            export_data['records'].append(record)
        
        # JSONファイルに書き出し
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return {
            'status': 'success',
            'output_path': output_path,
            'total_records': len(results)
        }
    
    def import_learning_data(self, input_path: str) -> Dict:
        """
        学習データをインポートする (Requirement 13.5)
        
        Args:
            input_path: 入力ファイルパス（JSON）
        
        Returns:
            Dict: インポート結果
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for record in import_data.get('records', []):
            try:
                # 写真IDの存在確認
                photo = self.db.query(Photo).filter(
                    Photo.id == record['photo_id']
                ).first()
                
                if not photo:
                    skipped_count += 1
                    continue
                
                # 重複チェック（同じphoto_id、action、timestampの組み合わせ）
                timestamp = datetime.fromisoformat(record['timestamp'])
                existing = self.db.query(LearningData).filter(
                    and_(
                        LearningData.photo_id == record['photo_id'],
                        LearningData.action == record['action'],
                        LearningData.timestamp == timestamp
                    )
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # 学習データを作成
                learning_data = LearningData(
                    photo_id=record['photo_id'],
                    action=record['action'],
                    original_preset=record.get('original_preset'),
                    final_preset=record.get('final_preset'),
                    timestamp=timestamp
                )
                
                if record.get('parameter_adjustments'):
                    learning_data.set_parameter_adjustments(
                        record['parameter_adjustments']
                    )
                
                self.db.add(learning_data)
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error importing record: {e}")
        
        self.db.commit()
        
        return {
            'status': 'success',
            'input_path': input_path,
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'error_count': error_count
        }
    
    def get_learning_summary(self, days: int = 30) -> Dict:
        """
        学習システムのサマリーを取得する
        
        Args:
            days: 集計期間（日数）
        
        Returns:
            Dict: サマリー情報
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 全体統計
        total_records = self.db.query(func.count(LearningData.id)).filter(
            LearningData.timestamp >= cutoff_date
        ).scalar()
        
        approved = self.db.query(func.count(LearningData.id)).filter(
            and_(
                LearningData.action == 'approved',
                LearningData.timestamp >= cutoff_date
            )
        ).scalar()
        
        rejected = self.db.query(func.count(LearningData.id)).filter(
            and_(
                LearningData.action == 'rejected',
                LearningData.timestamp >= cutoff_date
            )
        ).scalar()
        
        modified = self.db.query(func.count(LearningData.id)).filter(
            and_(
                LearningData.action == 'modified',
                LearningData.timestamp >= cutoff_date
            )
        ).scalar()
        
        # プリセット別統計
        preset_stats = self.db.query(
            LearningData.original_preset,
            func.count(LearningData.id).label('count')
        ).filter(
            LearningData.timestamp >= cutoff_date
        ).group_by(
            LearningData.original_preset
        ).all()
        
        return {
            'period_days': days,
            'total_records': total_records or 0,
            'approved_count': approved or 0,
            'rejected_count': rejected or 0,
            'modified_count': modified or 0,
            'approval_rate': (approved / total_records) if total_records else 0,
            'preset_usage': {
                preset: count for preset, count in preset_stats if preset
            }
        }
