"""
A/B Testing System for Junmai AutoDev.
Implements preset comparison experiments, effectiveness measurement, statistical significance testing, and report generation.

Requirements: 10.4, 10.5
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json
import statistics
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from models.database import Preset, Photo, LearningData, ABTest, ABTestAssignment, get_session


class ABTestManager:
    """
    A/Bテスト管理システム
    
    プリセットの比較実験を設定・実行し、効果を測定して
    統計的有意性を検定し、レポートを生成します。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the A/B test manager.
        
        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db = db_session or get_session()
        self.min_samples_per_variant = 30  # 各バリアントの最小サンプル数
        self.significance_level = 0.05  # 有意水準（α = 0.05）
    
    # ========== A/B Test Creation and Management ==========
    
    def create_ab_test(
        self,
        name: str,
        description: str,
        preset_a_id: int,
        preset_b_id: int,
        context_tag: Optional[str] = None,
        target_sample_size: int = 100,
        duration_days: int = 30
    ) -> 'ABTest':
        """
        A/Bテストを作成する (Requirement 10.4)
        
        Args:
            name: テスト名
            description: テストの説明
            preset_a_id: プリセットA（コントロール）のID
            preset_b_id: プリセットB（バリアント）のID
            context_tag: 対象コンテキストタグ（オプション）
            target_sample_size: 目標サンプル数
            duration_days: テスト期間（日数）
        
        Returns:
            ABTest: 作成されたA/Bテスト
        
        Raises:
            ValueError: プリセットが見つからない場合
        """
        # プリセットの存在確認
        preset_a = self.db.query(Preset).filter(Preset.id == preset_a_id).first()
        preset_b = self.db.query(Preset).filter(Preset.id == preset_b_id).first()
        
        if not preset_a or not preset_b:
            raise ValueError("One or both presets not found")
        
        # A/Bテストを作成
        ab_test = ABTest(
            name=name,
            description=description,
            preset_a_id=preset_a_id,
            preset_b_id=preset_b_id,
            context_tag=context_tag,
            target_sample_size=target_sample_size,
            duration_days=duration_days,
            status='active',
            start_date=datetime.utcnow()
        )
        
        self.db.add(ab_test)
        self.db.commit()
        self.db.refresh(ab_test)
        
        return ab_test
    
    def get_ab_test(self, test_id: int) -> Optional['ABTest']:
        """A/Bテストを取得する"""
        return self.db.query(ABTest).filter(ABTest.id == test_id).first()
    
    def list_ab_tests(
        self,
        status: Optional[str] = None,
        context_tag: Optional[str] = None
    ) -> List['ABTest']:
        """
        A/Bテストのリストを取得する
        
        Args:
            status: ステータスでフィルタ（'active', 'completed', 'paused'）
            context_tag: コンテキストタグでフィルタ
        
        Returns:
            List[ABTest]: A/Bテストのリスト
        """
        query = self.db.query(ABTest)
        
        if status:
            query = query.filter(ABTest.status == status)
        
        if context_tag:
            query = query.filter(ABTest.context_tag == context_tag)
        
        return query.order_by(ABTest.created_at.desc()).all()
    
    def pause_ab_test(self, test_id: int) -> 'ABTest':
        """A/Bテストを一時停止する"""
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        ab_test.status = 'paused'
        self.db.commit()
        self.db.refresh(ab_test)
        
        return ab_test
    
    def resume_ab_test(self, test_id: int) -> 'ABTest':
        """A/Bテストを再開する"""
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        ab_test.status = 'active'
        self.db.commit()
        self.db.refresh(ab_test)
        
        return ab_test
    
    def complete_ab_test(self, test_id: int) -> 'ABTest':
        """A/Bテストを完了する"""
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        ab_test.status = 'completed'
        ab_test.end_date = datetime.utcnow()
        self.db.commit()
        self.db.refresh(ab_test)
        
        return ab_test
    
    # ========== Assignment and Tracking ==========
    
    def assign_photo_to_variant(
        self,
        test_id: int,
        photo_id: int,
        variant: str = None
    ) -> 'ABTestAssignment':
        """
        写真をA/Bテストのバリアントに割り当てる
        
        Args:
            test_id: A/BテストID
            photo_id: 写真ID
            variant: バリアント（'A' or 'B'）。Noneの場合は自動割り当て
        
        Returns:
            ABTestAssignment: 割り当て記録
        """
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        if ab_test.status != 'active':
            raise ValueError(f"A/B test is not active (status: {ab_test.status})")
        
        # 既存の割り当てをチェック
        existing = self.db.query(ABTestAssignment).filter(
            and_(
                ABTestAssignment.test_id == test_id,
                ABTestAssignment.photo_id == photo_id
            )
        ).first()
        
        if existing:
            return existing
        
        # バリアントを決定（指定されていない場合は均等割り当て）
        if variant is None:
            # 現在の割り当て数を取得
            count_a = self.db.query(func.count(ABTestAssignment.id)).filter(
                and_(
                    ABTestAssignment.test_id == test_id,
                    ABTestAssignment.variant == 'A'
                )
            ).scalar() or 0
            
            count_b = self.db.query(func.count(ABTestAssignment.id)).filter(
                and_(
                    ABTestAssignment.test_id == test_id,
                    ABTestAssignment.variant == 'B'
                )
            ).scalar() or 0
            
            # 少ない方に割り当て
            variant = 'A' if count_a <= count_b else 'B'
        
        # プリセットIDを決定
        preset_id = ab_test.preset_a_id if variant == 'A' else ab_test.preset_b_id
        
        # 割り当てを作成
        assignment = ABTestAssignment(
            test_id=test_id,
            photo_id=photo_id,
            variant=variant,
            preset_id=preset_id,
            assigned_at=datetime.utcnow()
        )
        
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment
    
    def record_result(
        self,
        test_id: int,
        photo_id: int,
        approved: bool,
        processing_time: Optional[float] = None
    ) -> None:
        """
        A/Bテストの結果を記録する
        
        Args:
            test_id: A/BテストID
            photo_id: 写真ID
            approved: 承認されたかどうか
            processing_time: 処理時間（秒）
        """
        assignment = self.db.query(ABTestAssignment).filter(
            and_(
                ABTestAssignment.test_id == test_id,
                ABTestAssignment.photo_id == photo_id
            )
        ).first()
        
        if not assignment:
            raise ValueError(f"No assignment found for test {test_id}, photo {photo_id}")
        
        assignment.approved = approved
        assignment.processing_time = processing_time
        assignment.result_recorded_at = datetime.utcnow()
        
        self.db.commit()
    
    # ========== Effectiveness Measurement ==========
    
    def measure_effectiveness(self, test_id: int) -> Dict:
        """
        A/Bテストの効果を測定する (Requirement 10.5)
        
        Args:
            test_id: A/BテストID
        
        Returns:
            Dict: 効果測定結果
        """
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        # 各バリアントの結果を取得
        assignments_a = self.db.query(ABTestAssignment).filter(
            and_(
                ABTestAssignment.test_id == test_id,
                ABTestAssignment.variant == 'A',
                ABTestAssignment.result_recorded_at.isnot(None)
            )
        ).all()
        
        assignments_b = self.db.query(ABTestAssignment).filter(
            and_(
                ABTestAssignment.test_id == test_id,
                ABTestAssignment.variant == 'B',
                ABTestAssignment.result_recorded_at.isnot(None)
            )
        ).all()
        
        # サンプル数チェック
        if len(assignments_a) < self.min_samples_per_variant or \
           len(assignments_b) < self.min_samples_per_variant:
            return {
                'status': 'insufficient_data',
                'test_id': test_id,
                'test_name': ab_test.name,
                'samples_a': len(assignments_a),
                'samples_b': len(assignments_b),
                'min_required': self.min_samples_per_variant
            }
        
        # 承認率を計算
        approval_rate_a = sum(1 for a in assignments_a if a.approved) / len(assignments_a)
        approval_rate_b = sum(1 for a in assignments_b if a.approved) / len(assignments_b)
        
        # 処理時間を計算
        times_a = [a.processing_time for a in assignments_a if a.processing_time]
        times_b = [a.processing_time for a in assignments_b if a.processing_time]
        
        avg_time_a = statistics.mean(times_a) if times_a else None
        avg_time_b = statistics.mean(times_b) if times_b else None
        
        # 相対的な改善率を計算
        approval_improvement = ((approval_rate_b - approval_rate_a) / approval_rate_a * 100) if approval_rate_a > 0 else 0
        
        time_improvement = None
        if avg_time_a and avg_time_b:
            time_improvement = ((avg_time_a - avg_time_b) / avg_time_a * 100)
        
        return {
            'status': 'success',
            'test_id': test_id,
            'test_name': ab_test.name,
            'variant_a': {
                'preset_id': ab_test.preset_a_id,
                'samples': len(assignments_a),
                'approval_rate': approval_rate_a,
                'avg_processing_time': avg_time_a
            },
            'variant_b': {
                'preset_id': ab_test.preset_b_id,
                'samples': len(assignments_b),
                'approval_rate': approval_rate_b,
                'avg_processing_time': avg_time_b
            },
            'improvements': {
                'approval_rate': approval_improvement,
                'processing_time': time_improvement
            }
        }
    
    # ========== Statistical Significance Testing ==========
    
    def test_statistical_significance(self, test_id: int) -> Dict:
        """
        統計的有意性を検定する (Requirement 10.5)
        
        二項検定（承認率）とt検定（処理時間）を実行します。
        
        Args:
            test_id: A/BテストID
        
        Returns:
            Dict: 統計検定結果
        """
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        # 効果測定を実行
        effectiveness = self.measure_effectiveness(test_id)
        
        if effectiveness['status'] != 'success':
            return effectiveness
        
        # 各バリアントのデータを取得
        assignments_a = self.db.query(ABTestAssignment).filter(
            and_(
                ABTestAssignment.test_id == test_id,
                ABTestAssignment.variant == 'A',
                ABTestAssignment.result_recorded_at.isnot(None)
            )
        ).all()
        
        assignments_b = self.db.query(ABTestAssignment).filter(
            and_(
                ABTestAssignment.test_id == test_id,
                ABTestAssignment.variant == 'B',
                ABTestAssignment.result_recorded_at.isnot(None)
            )
        ).all()
        
        # 承認率の統計検定（カイ二乗検定）
        approvals_a = sum(1 for a in assignments_a if a.approved)
        approvals_b = sum(1 for a in assignments_b if a.approved)
        
        # 2x2分割表を作成
        contingency_table = [
            [approvals_a, len(assignments_a) - approvals_a],
            [approvals_b, len(assignments_b) - approvals_b]
        ]
        
        # Check if contingency table is valid (no zero expected frequencies)
        # If all approved or all rejected in both groups, skip chi-squared test
        if approvals_a == 0 or approvals_a == len(assignments_a) or \
           approvals_b == 0 or approvals_b == len(assignments_b):
            # Use Fisher's exact test for small samples or extreme cases
            from scipy.stats import fisher_exact
            _, p_value_approval = fisher_exact(contingency_table)
            chi2 = None
        else:
            chi2, p_value_approval, dof, expected = stats.chi2_contingency(contingency_table)
        
        # 処理時間のt検定
        times_a = [a.processing_time for a in assignments_a if a.processing_time]
        times_b = [a.processing_time for a in assignments_b if a.processing_time]
        
        p_value_time = None
        t_statistic = None
        
        if len(times_a) >= 2 and len(times_b) >= 2:
            t_statistic, p_value_time = stats.ttest_ind(times_a, times_b)
        
        # 有意性の判定
        approval_significant = p_value_approval < self.significance_level
        time_significant = p_value_time < self.significance_level if p_value_time else False
        
        # 勝者の決定
        winner = None
        if approval_significant:
            if effectiveness['variant_b']['approval_rate'] > effectiveness['variant_a']['approval_rate']:
                winner = 'B'
            else:
                winner = 'A'
        
        return {
            'status': 'success',
            'test_id': test_id,
            'test_name': ab_test.name,
            'significance_level': self.significance_level,
            'approval_rate_test': {
                'chi2_statistic': float(chi2) if chi2 is not None else None,
                'p_value': float(p_value_approval),
                'significant': bool(approval_significant),
                'interpretation': 'Significant difference' if approval_significant else 'No significant difference'
            },
            'processing_time_test': {
                't_statistic': float(t_statistic) if t_statistic is not None else None,
                'p_value': float(p_value_time) if p_value_time is not None else None,
                'significant': bool(time_significant),
                'interpretation': 'Significant difference' if time_significant else 'No significant difference'
            } if p_value_time else None,
            'winner': winner,
            'recommendation': self._generate_recommendation(
                winner,
                effectiveness,
                approval_significant,
                time_significant
            )
        }
    
    def _generate_recommendation(
        self,
        winner: Optional[str],
        effectiveness: Dict,
        approval_significant: bool,
        time_significant: bool
    ) -> str:
        """
        テスト結果に基づく推奨事項を生成する
        
        Args:
            winner: 勝者バリアント（'A', 'B', or None）
            effectiveness: 効果測定結果
            approval_significant: 承認率の有意性
            time_significant: 処理時間の有意性
        
        Returns:
            str: 推奨事項
        """
        if not winner:
            return "No statistically significant difference found. Continue using current preset (A) or collect more data."
        
        improvement = effectiveness['improvements']['approval_rate']
        
        if winner == 'B':
            if improvement > 10:
                return f"Strong recommendation: Switch to Preset B. Approval rate improved by {improvement:.1f}% with statistical significance."
            elif improvement > 5:
                return f"Moderate recommendation: Consider switching to Preset B. Approval rate improved by {improvement:.1f}%."
            else:
                return f"Weak recommendation: Preset B shows slight improvement ({improvement:.1f}%), but consider practical significance."
        else:
            return "Recommendation: Continue using Preset A. It performs better than or equal to Preset B."
    
    # ========== Report Generation ==========
    
    def generate_report(self, test_id: int, output_path: Optional[str] = None) -> Dict:
        """
        A/Bテストのレポートを生成する (Requirement 10.5)
        
        Args:
            test_id: A/BテストID
            output_path: レポート出力パス（JSON）。Noneの場合は辞書を返すのみ
        
        Returns:
            Dict: レポート内容
        """
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        # 効果測定と統計検定を実行
        effectiveness = self.measure_effectiveness(test_id)
        significance = self.test_statistical_significance(test_id)
        
        # プリセット情報を取得
        preset_a = self.db.query(Preset).filter(Preset.id == ab_test.preset_a_id).first()
        preset_b = self.db.query(Preset).filter(Preset.id == ab_test.preset_b_id).first()
        
        # レポートを構築
        report = {
            'report_generated_at': datetime.utcnow().isoformat(),
            'test_info': {
                'id': ab_test.id,
                'name': ab_test.name,
                'description': ab_test.description,
                'status': ab_test.status,
                'context_tag': ab_test.context_tag,
                'start_date': ab_test.start_date.isoformat() if ab_test.start_date else None,
                'end_date': ab_test.end_date.isoformat() if ab_test.end_date else None,
                'duration_days': ab_test.duration_days,
                'target_sample_size': ab_test.target_sample_size
            },
            'presets': {
                'variant_a': {
                    'id': preset_a.id,
                    'name': preset_a.name,
                    'version': preset_a.version
                } if preset_a else None,
                'variant_b': {
                    'id': preset_b.id,
                    'name': preset_b.name,
                    'version': preset_b.version
                } if preset_b else None
            },
            'effectiveness': effectiveness,
            'statistical_significance': significance,
            'summary': self._generate_summary(effectiveness, significance)
        }
        
        # ファイルに出力
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def _generate_summary(self, effectiveness: Dict, significance: Dict) -> Dict:
        """
        レポートのサマリーを生成する
        
        Args:
            effectiveness: 効果測定結果
            significance: 統計検定結果
        
        Returns:
            Dict: サマリー情報
        """
        if effectiveness['status'] != 'success':
            return {
                'conclusion': 'Insufficient data for analysis',
                'action': 'Continue collecting data'
            }
        
        winner = significance.get('winner')
        approval_improvement = effectiveness['improvements']['approval_rate']
        
        if winner == 'B':
            conclusion = f"Preset B outperforms Preset A with {approval_improvement:.1f}% improvement in approval rate"
        elif winner == 'A':
            conclusion = "Preset A performs better than or equal to Preset B"
        else:
            conclusion = "No statistically significant difference between presets"
        
        return {
            'conclusion': conclusion,
            'winner': winner,
            'approval_improvement_percent': approval_improvement,
            'statistically_significant': significance['approval_rate_test']['significant'],
            'recommendation': significance.get('recommendation', ''),
            'action': 'Deploy winner' if winner else 'Continue testing or use current preset'
        }
    
    def generate_comparison_report(
        self,
        test_ids: List[int],
        output_path: Optional[str] = None
    ) -> Dict:
        """
        複数のA/Bテストを比較するレポートを生成する
        
        Args:
            test_ids: A/BテストIDのリスト
            output_path: レポート出力パス（JSON）
        
        Returns:
            Dict: 比較レポート
        """
        reports = []
        
        for test_id in test_ids:
            try:
                report = self.generate_report(test_id)
                reports.append(report)
            except Exception as e:
                print(f"Error generating report for test {test_id}: {e}")
        
        # 比較サマリーを作成
        comparison = {
            'comparison_generated_at': datetime.utcnow().isoformat(),
            'total_tests': len(reports),
            'tests': reports,
            'overall_summary': {
                'tests_with_significant_results': sum(
                    1 for r in reports 
                    if r.get('statistical_significance', {}).get('approval_rate_test', {}).get('significant', False)
                ),
                'tests_with_winner_b': sum(
                    1 for r in reports 
                    if r.get('statistical_significance', {}).get('winner') == 'B'
                ),
                'avg_improvement': statistics.mean([
                    r['effectiveness']['improvements']['approval_rate']
                    for r in reports
                    if r.get('effectiveness', {}).get('status') == 'success'
                ]) if reports else 0
            }
        }
        
        # ファイルに出力
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, ensure_ascii=False, indent=2)
        
        return comparison
    
    # ========== Helper Methods ==========
    
    def get_test_progress(self, test_id: int) -> Dict:
        """
        A/Bテストの進捗状況を取得する
        
        Args:
            test_id: A/BテストID
        
        Returns:
            Dict: 進捗情報
        """
        ab_test = self.get_ab_test(test_id)
        if not ab_test:
            raise ValueError(f"A/B test with ID {test_id} not found")
        
        # 割り当て数を取得
        total_assignments = self.db.query(func.count(ABTestAssignment.id)).filter(
            ABTestAssignment.test_id == test_id
        ).scalar() or 0
        
        completed_assignments = self.db.query(func.count(ABTestAssignment.id)).filter(
            and_(
                ABTestAssignment.test_id == test_id,
                ABTestAssignment.result_recorded_at.isnot(None)
            )
        ).scalar() or 0
        
        # 経過日数を計算
        if ab_test.start_date:
            elapsed_days = (datetime.utcnow() - ab_test.start_date).days
        else:
            elapsed_days = 0
        
        # 進捗率を計算
        progress_percent = (completed_assignments / ab_test.target_sample_size * 100) if ab_test.target_sample_size > 0 else 0
        
        return {
            'test_id': test_id,
            'test_name': ab_test.name,
            'status': ab_test.status,
            'total_assignments': total_assignments,
            'completed_assignments': completed_assignments,
            'target_sample_size': ab_test.target_sample_size,
            'progress_percent': min(progress_percent, 100),
            'elapsed_days': elapsed_days,
            'duration_days': ab_test.duration_days,
            'ready_for_analysis': completed_assignments >= self.min_samples_per_variant * 2
        }
