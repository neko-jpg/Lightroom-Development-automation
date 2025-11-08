"""
Context Recognition Engine for Junmai AutoDev system.
Analyzes photo metadata and determines shooting context for automatic preset selection.

Features:
- Rule-based context evaluation
- 20 predefined shooting scenarios
- Context score calculation with weighted conditions
- Automatic preset recommendation based on context

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import time

logger = logging.getLogger(__name__)


class ContextEngine:
    """
    コンテキスト認識エンジン
    
    撮影状況（時間帯、場所、被写体）を分析し、最適なプリセットを自動選択します。
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize context engine
        
        Args:
            rules_file: Path to context rules JSON file (optional)
        """
        if rules_file is None:
            # Default to config/context_rules.json in the same directory
            rules_file = Path(__file__).parent / 'config' / 'context_rules.json'
        
        self.rules_file = Path(rules_file)
        self.rules = self._load_context_rules()
        logger.info(f"Context engine initialized with {len(self.rules)} contexts")
    
    def _load_context_rules(self) -> Dict[str, Any]:
        """
        コンテキストルール定義をロード
        
        Returns:
            コンテキストルールの辞書
        """
        try:
            if not self.rules_file.exists():
                logger.error(f"Context rules file not found: {self.rules_file}")
                return self._get_default_rules()
            
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            contexts = data.get('contexts', {})
            logger.info(f"Loaded {len(contexts)} context rules from {self.rules_file}")
            return contexts
            
        except Exception as e:
            logger.error(f"Error loading context rules: {e}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """
        デフォルトのコンテキストルールを返す
        
        Returns:
            デフォルトルールの辞書
        """
        return {
            'default': {
                'description': 'デフォルト - 標準的な撮影',
                'conditions': [],
                'weights': [],
                'recommended_preset': 'Standard_Balanced_v1',
                'preset_blend': 50
            }
        }
    
    def determine_context(
        self, 
        exif_data: Dict[str, Any], 
        ai_eval: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        コンテキストを判定
        
        Args:
            exif_data: EXIF解析結果（EXIFAnalyzer.analyze()の出力）
            ai_eval: AI評価結果（オプション）
            
        Returns:
            判定結果の辞書:
            {
                'context': str,              # コンテキスト名
                'score': float,              # スコア (0.0-1.0)
                'description': str,          # 説明
                'recommended_preset': str,   # 推奨プリセット
                'preset_blend': int,         # ブレンド量 (0-100)
                'all_scores': Dict[str, float]  # 全コンテキストのスコア
            }
        """
        # Calculate scores for all contexts
        score_map = {}
        
        for context_name, rule in self.rules.items():
            if context_name == 'default':
                continue  # Skip default, use as fallback
            
            score = self._evaluate_rule(rule, exif_data, ai_eval)
            score_map[context_name] = score
            
            logger.debug(f"Context '{context_name}': score={score:.3f}")
        
        # Find best matching context
        if score_map:
            best_context = max(score_map, key=score_map.get)
            best_score = score_map[best_context]
        else:
            best_context = 'default'
            best_score = 0.0
        
        # Use default if best score is too low
        threshold = 0.5
        if best_score < threshold:
            logger.info(f"Best score {best_score:.3f} below threshold {threshold}, using default")
            best_context = 'default'
            best_score = 0.0
        
        # Get context details
        context_rule = self.rules.get(best_context, self.rules['default'])
        
        result = {
            'context': best_context,
            'score': best_score,
            'description': context_rule.get('description', ''),
            'recommended_preset': context_rule.get('recommended_preset', 'Standard_Balanced_v1'),
            'preset_blend': context_rule.get('preset_blend', 50),
            'all_scores': score_map
        }
        
        logger.info(
            f"Determined context: {best_context} "
            f"(score={best_score:.3f}, preset={result['recommended_preset']})"
        )
        
        return result
    
    def _evaluate_rule(
        self, 
        rule: Dict[str, Any], 
        exif_data: Dict[str, Any],
        ai_eval: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        ルールを評価してスコアを計算
        
        Args:
            rule: コンテキストルール
            exif_data: EXIF解析結果
            ai_eval: AI評価結果（オプション）
            
        Returns:
            スコア (0.0-1.0)
        """
        conditions = rule.get('conditions', [])
        weights = rule.get('weights', [])
        
        if not conditions:
            return 0.0
        
        # Ensure weights match conditions
        if len(weights) != len(conditions):
            # Use equal weights if mismatch
            weights = [1.0 / len(conditions)] * len(conditions)
        
        # Normalize weights to sum to 1.0
        weight_sum = sum(weights)
        if weight_sum > 0:
            weights = [w / weight_sum for w in weights]
        
        # Evaluate each condition
        total_score = 0.0
        
        for condition, weight in zip(conditions, weights):
            condition_met = self._evaluate_condition(condition, exif_data, ai_eval)
            if condition_met:
                total_score += weight
        
        return total_score
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        exif_data: Dict[str, Any],
        ai_eval: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        単一の条件を評価
        
        Args:
            condition: 条件定義
            exif_data: EXIF解析結果
            ai_eval: AI評価結果（オプション）
            
        Returns:
            条件が満たされているかどうか
        """
        field = condition.get('field')
        operator = condition.get('operator')
        expected_value = condition.get('value')
        
        if not field or not operator:
            return False
        
        # Get actual value from data
        actual_value = self._get_field_value(field, exif_data, ai_eval)
        
        if actual_value is None:
            return False
        
        # Evaluate based on operator
        try:
            return self._apply_operator(operator, actual_value, expected_value)
        except Exception as e:
            logger.debug(f"Error evaluating condition {field} {operator} {expected_value}: {e}")
            return False
    
    def _get_field_value(
        self,
        field_path: str,
        exif_data: Dict[str, Any],
        ai_eval: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        フィールドパスから値を取得
        
        Args:
            field_path: ドット区切りのフィールドパス (例: "settings.iso")
            exif_data: EXIF解析結果
            ai_eval: AI評価結果（オプション）
            
        Returns:
            フィールド値またはNone
        """
        # Combine data sources
        data = {**exif_data}
        if ai_eval:
            data['ai_eval'] = ai_eval
        
        # Navigate through nested dictionary
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None
        
        return current
    
    def _apply_operator(
        self,
        operator: str,
        actual_value: Any,
        expected_value: Any
    ) -> bool:
        """
        演算子を適用して条件を評価
        
        Args:
            operator: 演算子 (==, !=, >, <, >=, <=, in, between, shutter_faster_than)
            actual_value: 実際の値
            expected_value: 期待値
            
        Returns:
            条件が満たされているかどうか
        """
        if operator == '==':
            return actual_value == expected_value
        
        elif operator == '!=':
            return actual_value != expected_value
        
        elif operator == '>':
            return float(actual_value) > float(expected_value)
        
        elif operator == '<':
            return float(actual_value) < float(expected_value)
        
        elif operator == '>=':
            return float(actual_value) >= float(expected_value)
        
        elif operator == '<=':
            return float(actual_value) <= float(expected_value)
        
        elif operator == 'in':
            if not isinstance(expected_value, list):
                return False
            return actual_value in expected_value
        
        elif operator == 'between':
            if not isinstance(expected_value, list) or len(expected_value) != 2:
                return False
            min_val, max_val = expected_value
            return min_val <= float(actual_value) <= max_val
        
        elif operator == 'shutter_faster_than':
            # Compare shutter speeds (e.g., "1/500" vs "1/250")
            return self._compare_shutter_speeds(actual_value, expected_value)
        
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    def _compare_shutter_speeds(self, actual: str, threshold: str) -> bool:
        """
        シャッタースピードを比較（速い方が大きい値）
        
        Args:
            actual: 実際のシャッタースピード (例: "1/500")
            threshold: 閾値 (例: "1/250")
            
        Returns:
            actual が threshold より速いかどうか
        """
        try:
            actual_val = self._parse_shutter_speed(actual)
            threshold_val = self._parse_shutter_speed(threshold)
            
            if actual_val is None or threshold_val is None:
                return False
            
            # Faster shutter = smaller exposure time
            return actual_val < threshold_val
            
        except Exception as e:
            logger.debug(f"Error comparing shutter speeds: {e}")
            return False
    
    def _parse_shutter_speed(self, shutter_str: str) -> Optional[float]:
        """
        シャッタースピード文字列を秒数に変換
        
        Args:
            shutter_str: シャッタースピード文字列 (例: "1/500", "2", "0.5")
            
        Returns:
            秒数またはNone
        """
        if not shutter_str:
            return None
        
        shutter_str = str(shutter_str).strip()
        
        # Handle fraction format "1/500"
        if '/' in shutter_str:
            parts = shutter_str.split('/')
            if len(parts) == 2:
                try:
                    numerator = float(parts[0])
                    denominator = float(parts[1])
                    if denominator != 0:
                        return numerator / denominator
                except ValueError:
                    pass
        
        # Handle decimal format
        try:
            return float(shutter_str)
        except ValueError:
            return None
    
    def get_context_list(self) -> List[Dict[str, Any]]:
        """
        利用可能なコンテキストのリストを取得
        
        Returns:
            コンテキスト情報のリスト
        """
        contexts = []
        
        for name, rule in self.rules.items():
            contexts.append({
                'name': name,
                'description': rule.get('description', ''),
                'recommended_preset': rule.get('recommended_preset', ''),
                'preset_blend': rule.get('preset_blend', 50),
                'condition_count': len(rule.get('conditions', []))
            })
        
        return contexts
    
    def reload_rules(self) -> bool:
        """
        ルールファイルを再読み込み
        
        Returns:
            成功したかどうか
        """
        try:
            self.rules = self._load_context_rules()
            logger.info(f"Reloaded {len(self.rules)} context rules")
            return True
        except Exception as e:
            logger.error(f"Error reloading rules: {e}")
            return False
    
    def validate_rules(self) -> Tuple[bool, List[str]]:
        """
        ルールファイルの妥当性を検証
        
        Returns:
            (valid, errors) のタプル
        """
        errors = []
        
        if not self.rules:
            errors.append("No rules loaded")
            return False, errors
        
        if 'default' not in self.rules:
            errors.append("Missing 'default' context")
        
        for context_name, rule in self.rules.items():
            # Check required fields
            if 'recommended_preset' not in rule:
                errors.append(f"Context '{context_name}' missing 'recommended_preset'")
            
            if 'preset_blend' not in rule:
                errors.append(f"Context '{context_name}' missing 'preset_blend'")
            
            # Check conditions and weights match
            conditions = rule.get('conditions', [])
            weights = rule.get('weights', [])
            
            if len(conditions) != len(weights) and len(conditions) > 0:
                errors.append(
                    f"Context '{context_name}' has {len(conditions)} conditions "
                    f"but {len(weights)} weights"
                )
            
            # Validate condition structure
            for i, condition in enumerate(conditions):
                if 'field' not in condition:
                    errors.append(
                        f"Context '{context_name}' condition {i} missing 'field'"
                    )
                if 'operator' not in condition:
                    errors.append(
                        f"Context '{context_name}' condition {i} missing 'operator'"
                    )
                if 'value' not in condition:
                    errors.append(
                        f"Context '{context_name}' condition {i} missing 'value'"
                    )
        
        is_valid = len(errors) == 0
        return is_valid, errors


# Convenience function for quick context determination
def determine_photo_context(
    exif_data: Dict[str, Any],
    ai_eval: Optional[Dict[str, Any]] = None,
    rules_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    写真のコンテキストを判定（便利関数）
    
    Args:
        exif_data: EXIF解析結果
        ai_eval: AI評価結果（オプション）
        rules_file: ルールファイルパス（オプション）
        
    Returns:
        コンテキスト判定結果
    """
    engine = ContextEngine(rules_file)
    return engine.determine_context(exif_data, ai_eval)
