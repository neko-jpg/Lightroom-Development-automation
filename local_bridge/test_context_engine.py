"""
Unit tests for Context Recognition Engine.

Tests context determination, rule evaluation, condition matching,
and preset recommendation based on shooting scenarios.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import time

from context_engine import ContextEngine, determine_photo_context


class TestContextEngine:
    """Test suite for ContextEngine class."""
    
    @pytest.fixture
    def sample_rules(self):
        """Create sample context rules for testing."""
        return {
            "contexts": {
                "default": {
                    "description": "デフォルト - 標準的な撮影",
                    "conditions": [],
                    "weights": [],
                    "recommended_preset": "Standard_Balanced_v1",
                    "preset_blend": 50
                },
                "backlit_portrait": {
                    "description": "逆光ポートレート",
                    "conditions": [
                        {"field": "settings.iso", "operator": ">", "value": 400},
                        {"field": "settings.focal_length", "operator": "between", "value": [35, 85]},
                        {"field": "datetime.time_of_day", "operator": "in", "value": ["golden_hour_evening", "golden_hour_morning"]},
                        {"field": "location.location_type", "operator": "==", "value": "outdoor"}
                    ],
                    "weights": [0.3, 0.2, 0.3, 0.2],
                    "recommended_preset": "WhiteLayer_Transparency_v4",
                    "preset_blend": 60
                },
                "low_light_indoor": {
                    "description": "室内低照度",
                    "conditions": [
                        {"field": "settings.iso", "operator": ">", "value": 1600},
                        {"field": "location.has_gps", "operator": "==", "value": False}
                    ],
                    "weights": [0.6, 0.4],
                    "recommended_preset": "LowLight_NR_v2",
                    "preset_blend": 80
                },
                "landscape_sky": {
                    "description": "風景（空あり）",
                    "conditions": [
                        {"field": "settings.focal_length", "operator": "<", "value": 35},
                        {"field": "settings.aperture", "operator": ">=", "value": 8.0},
                        {"field": "location.location_type", "operator": "==", "value": "outdoor"}
                    ],
                    "weights": [0.4, 0.3, 0.3],
                    "recommended_preset": "Landscape_Vivid_v3",
                    "preset_blend": 70
                }
            }
        }
    
    @pytest.fixture
    def engine_with_rules(self, sample_rules, tmp_path):
        """Create ContextEngine with sample rules."""
        rules_file = tmp_path / "context_rules.json"
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(sample_rules, f)
        
        return ContextEngine(str(rules_file))
    
    # ========== Initialization Tests ==========
    
    def test_initialization_with_rules_file(self, engine_with_rules):
        """Test initialization with rules file."""
        assert engine_with_rules is not None
        assert len(engine_with_rules.rules) > 0
        assert 'default' in engine_with_rules.rules
        assert 'backlit_portrait' in engine_with_rules.rules
    
    def test_initialization_without_rules_file(self):
        """Test initialization without rules file (uses defaults)."""
        engine = ContextEngine('nonexistent_file.json')
        
        assert engine is not None
        assert 'default' in engine.rules
        assert len(engine.rules) == 1  # Only default
    
    def test_initialization_with_invalid_json(self, tmp_path):
        """Test initialization with invalid JSON file."""
        rules_file = tmp_path / "invalid.json"
        with open(rules_file, 'w') as f:
            f.write("invalid json content")
        
        engine = ContextEngine(str(rules_file))
        
        # Should fall back to default rules
        assert 'default' in engine.rules
    
    # ========== Context Determination Tests ==========
    
    def test_determine_context_backlit_portrait(self, engine_with_rules):
        """Test context determination for backlit portrait."""
        exif_data = {
            'settings': {
                'iso': 800,
                'focal_length': 50.0,
                'aperture': 1.8
            },
            'location': {
                'location_type': 'outdoor',
                'has_gps': True
            },
            'datetime': {
                'time_of_day': 'golden_hour_evening'
            }
        }
        
        result = engine_with_rules.determine_context(exif_data)
        
        assert result['context'] == 'backlit_portrait'
        assert result['score'] > 0.5
        assert result['recommended_preset'] == 'WhiteLayer_Transparency_v4'
        assert result['preset_blend'] == 60
    
    def test_determine_context_low_light_indoor(self, engine_with_rules):
        """Test context determination for low light indoor."""
        exif_data = {
            'settings': {
                'iso': 3200,
                'focal_length': 35.0
            },
            'location': {
                'location_type': 'unknown',
                'has_gps': False
            },
            'datetime': {
                'time_of_day': 'evening'
            }
        }
        
        result = engine_with_rules.determine_context(exif_data)
        
        assert result['context'] == 'low_light_indoor'
        assert result['score'] > 0.5
        assert result['recommended_preset'] == 'LowLight_NR_v2'
    
    def test_determine_context_landscape(self, engine_with_rules):
        """Test context determination for landscape."""
        exif_data = {
            'settings': {
                'iso': 100,
                'focal_length': 24.0,
                'aperture': 11.0
            },
            'location': {
                'location_type': 'outdoor',
                'has_gps': True
            },
            'datetime': {
                'time_of_day': 'morning'
            }
        }
        
        result = engine_with_rules.determine_context(exif_data)
        
        assert result['context'] == 'landscape_sky'
        assert result['recommended_preset'] == 'Landscape_Vivid_v3'
    
    def test_determine_context_default_fallback(self, engine_with_rules):
        """Test fallback to default context when no match."""
        exif_data = {
            'settings': {
                'iso': 200,
                'focal_length': 100.0
            },
            'location': {},
            'datetime': {}
        }
        
        result = engine_with_rules.determine_context(exif_data)
        
        assert result['context'] == 'default'
        assert result['recommended_preset'] == 'Standard_Balanced_v1'
    
    def test_determine_context_low_score_fallback(self, engine_with_rules):
        """Test fallback to default when best score is too low."""
        exif_data = {
            'settings': {
                'iso': 200,  # Doesn't match any high-scoring context
                'focal_length': 50.0
            },
            'location': {
                'location_type': 'indoor'
            },
            'datetime': {
                'time_of_day': 'midday'
            }
        }
        
        result = engine_with_rules.determine_context(exif_data)
        
        # Should fall back to default if score is too low
        if result['score'] < 0.5:
            assert result['context'] == 'default'
    
    def test_determine_context_with_ai_eval(self, engine_with_rules):
        """Test context determination with AI evaluation data."""
        exif_data = {
            'settings': {'iso': 800, 'focal_length': 50.0},
            'location': {'location_type': 'outdoor'},
            'datetime': {'time_of_day': 'golden_hour_evening'}
        }
        
        ai_eval = {
            'faces_detected': 1,
            'overall_score': 4.5
        }
        
        result = engine_with_rules.determine_context(exif_data, ai_eval)
        
        assert 'context' in result
        assert 'score' in result
    
    # ========== Rule Evaluation Tests ==========
    
    def test_evaluate_rule_all_conditions_met(self, engine_with_rules):
        """Test rule evaluation when all conditions are met."""
        rule = {
            'conditions': [
                {'field': 'settings.iso', 'operator': '>', 'value': 400},
                {'field': 'settings.focal_length', 'operator': '==', 'value': 50.0}
            ],
            'weights': [0.5, 0.5]
        }
        
        exif_data = {
            'settings': {
                'iso': 800,
                'focal_length': 50.0
            }
        }
        
        score = engine_with_rules._evaluate_rule(rule, exif_data)
        
        assert score == 1.0  # All conditions met
    
    def test_evaluate_rule_partial_match(self, engine_with_rules):
        """Test rule evaluation with partial condition match."""
        rule = {
            'conditions': [
                {'field': 'settings.iso', 'operator': '>', 'value': 400},
                {'field': 'settings.focal_length', 'operator': '==', 'value': 50.0}
            ],
            'weights': [0.6, 0.4]
        }
        
        exif_data = {
            'settings': {
                'iso': 800,  # Matches
                'focal_length': 85.0  # Doesn't match
            }
        }
        
        score = engine_with_rules._evaluate_rule(rule, exif_data)
        
        assert score == 0.6  # Only first condition met
    
    def test_evaluate_rule_no_match(self, engine_with_rules):
        """Test rule evaluation with no conditions met."""
        rule = {
            'conditions': [
                {'field': 'settings.iso', 'operator': '>', 'value': 1000},
                {'field': 'settings.focal_length', 'operator': '==', 'value': 50.0}
            ],
            'weights': [0.5, 0.5]
        }
        
        exif_data = {
            'settings': {
                'iso': 400,  # Doesn't match
                'focal_length': 85.0  # Doesn't match
            }
        }
        
        score = engine_with_rules._evaluate_rule(rule, exif_data)
        
        assert score == 0.0
    
    def test_evaluate_rule_missing_weights(self, engine_with_rules):
        """Test rule evaluation with missing weights (uses equal weights)."""
        rule = {
            'conditions': [
                {'field': 'settings.iso', 'operator': '>', 'value': 400},
                {'field': 'settings.focal_length', 'operator': '==', 'value': 50.0}
            ],
            'weights': []  # Missing weights
        }
        
        exif_data = {
            'settings': {
                'iso': 800,
                'focal_length': 50.0
            }
        }
        
        score = engine_with_rules._evaluate_rule(rule, exif_data)
        
        assert score == 1.0  # Should use equal weights
    
    # ========== Condition Evaluation Tests ==========
    
    def test_evaluate_condition_equals(self, engine_with_rules):
        """Test condition evaluation with == operator."""
        condition = {'field': 'settings.iso', 'operator': '==', 'value': 800}
        exif_data = {'settings': {'iso': 800}}
        
        result = engine_with_rules._evaluate_condition(condition, exif_data)
        
        assert result is True
    
    def test_evaluate_condition_not_equals(self, engine_with_rules):
        """Test condition evaluation with != operator."""
        condition = {'field': 'settings.iso', 'operator': '!=', 'value': 800}
        exif_data = {'settings': {'iso': 1600}}
        
        result = engine_with_rules._evaluate_condition(condition, exif_data)
        
        assert result is True
    
    def test_evaluate_condition_greater_than(self, engine_with_rules):
        """Test condition evaluation with > operator."""
        condition = {'field': 'settings.iso', 'operator': '>', 'value': 400}
        exif_data = {'settings': {'iso': 800}}
        
        result = engine_with_rules._evaluate_condition(condition, exif_data)
        
        assert result is True
    
    def test_evaluate_condition_less_than(self, engine_with_rules):
        """Test condition evaluation with < operator."""
        condition = {'field': 'settings.focal_length', 'operator': '<', 'value': 35}
        exif_data = {'settings': {'focal_length': 24.0}}
        
        result = engine_with_rules._evaluate_condition(condition, exif_data)
        
        assert result is True
    
    def test_evaluate_condition_in_list(self, engine_with_rules):
        """Test condition evaluation with 'in' operator."""
        condition = {
            'field': 'datetime.time_of_day',
            'operator': 'in',
            'value': ['golden_hour_morning', 'golden_hour_evening']
        }
        exif_data = {'datetime': {'time_of_day': 'golden_hour_evening'}}
        
        result = engine_with_rules._evaluate_condition(condition, exif_data)
        
        assert result is True
    
    def test_evaluate_condition_between(self, engine_with_rules):
        """Test condition evaluation with 'between' operator."""
        condition = {
            'field': 'settings.focal_length',
            'operator': 'between',
            'value': [35, 85]
        }
        exif_data = {'settings': {'focal_length': 50.0}}
        
        result = engine_with_rules._evaluate_condition(condition, exif_data)
        
        assert result is True
    
    def test_evaluate_condition_missing_field(self, engine_with_rules):
        """Test condition evaluation with missing field."""
        condition = {'field': 'settings.nonexistent', 'operator': '==', 'value': 100}
        exif_data = {'settings': {'iso': 800}}
        
        result = engine_with_rules._evaluate_condition(condition, exif_data)
        
        assert result is False
    
    # ========== Field Value Extraction Tests ==========
    
    def test_get_field_value_simple(self, engine_with_rules):
        """Test field value extraction for simple path."""
        data = {'settings': {'iso': 800}}
        
        value = engine_with_rules._get_field_value('settings.iso', data)
        
        assert value == 800
    
    def test_get_field_value_nested(self, engine_with_rules):
        """Test field value extraction for nested path."""
        data = {
            'camera': {
                'settings': {
                    'advanced': {
                        'metering': 'matrix'
                    }
                }
            }
        }
        
        value = engine_with_rules._get_field_value(
            'camera.settings.advanced.metering', data
        )
        
        assert value == 'matrix'
    
    def test_get_field_value_missing(self, engine_with_rules):
        """Test field value extraction for missing path."""
        data = {'settings': {'iso': 800}}
        
        value = engine_with_rules._get_field_value('settings.nonexistent', data)
        
        assert value is None
    
    def test_get_field_value_with_ai_eval(self, engine_with_rules):
        """Test field value extraction with AI evaluation data."""
        exif_data = {'settings': {'iso': 800}}
        ai_eval = {'faces_detected': 2}
        
        value = engine_with_rules._get_field_value(
            'ai_eval.faces_detected', exif_data, ai_eval
        )
        
        assert value == 2
    
    # ========== Operator Application Tests ==========
    
    def test_apply_operator_shutter_faster_than(self, engine_with_rules):
        """Test shutter speed comparison operator."""
        # 1/500 is faster than 1/250
        result = engine_with_rules._apply_operator(
            'shutter_faster_than', '1/500', '1/250'
        )
        assert result is True
        
        # 1/125 is slower than 1/250
        result = engine_with_rules._apply_operator(
            'shutter_faster_than', '1/125', '1/250'
        )
        assert result is False
    
    def test_apply_operator_unknown(self, engine_with_rules):
        """Test unknown operator."""
        result = engine_with_rules._apply_operator(
            'unknown_operator', 100, 50
        )
        
        assert result is False
    
    # ========== Shutter Speed Parsing Tests ==========
    
    def test_parse_shutter_speed_fraction(self, engine_with_rules):
        """Test shutter speed parsing for fraction format."""
        speed = engine_with_rules._parse_shutter_speed('1/500')
        
        assert speed is not None
        assert abs(speed - 0.002) < 0.0001
    
    def test_parse_shutter_speed_decimal(self, engine_with_rules):
        """Test shutter speed parsing for decimal format."""
        speed = engine_with_rules._parse_shutter_speed('2.5')
        
        assert speed == 2.5
    
    def test_parse_shutter_speed_invalid(self, engine_with_rules):
        """Test shutter speed parsing for invalid format."""
        speed = engine_with_rules._parse_shutter_speed('invalid')
        
        assert speed is None
    
    def test_compare_shutter_speeds(self, engine_with_rules):
        """Test shutter speed comparison."""
        # 1/1000 is faster than 1/500
        result = engine_with_rules._compare_shutter_speeds('1/1000', '1/500')
        assert result is True
        
        # 1/250 is slower than 1/500
        result = engine_with_rules._compare_shutter_speeds('1/250', '1/500')
        assert result is False
    
    # ========== Context List Tests ==========
    
    def test_get_context_list(self, engine_with_rules):
        """Test getting list of available contexts."""
        contexts = engine_with_rules.get_context_list()
        
        assert len(contexts) > 0
        assert any(c['name'] == 'backlit_portrait' for c in contexts)
        assert any(c['name'] == 'low_light_indoor' for c in contexts)
        
        # Check structure
        for context in contexts:
            assert 'name' in context
            assert 'description' in context
            assert 'recommended_preset' in context
            assert 'preset_blend' in context
    
    # ========== Rules Reload Tests ==========
    
    def test_reload_rules(self, engine_with_rules, tmp_path):
        """Test reloading rules from file."""
        # Modify rules file
        new_rules = {
            "contexts": {
                "default": {
                    "description": "Updated default",
                    "conditions": [],
                    "weights": [],
                    "recommended_preset": "New_Preset_v1",
                    "preset_blend": 75
                }
            }
        }
        
        with open(engine_with_rules.rules_file, 'w', encoding='utf-8') as f:
            json.dump(new_rules, f)
        
        success = engine_with_rules.reload_rules()
        
        assert success is True
        assert engine_with_rules.rules['default']['recommended_preset'] == 'New_Preset_v1'
    
    # ========== Rules Validation Tests ==========
    
    def test_validate_rules_valid(self, engine_with_rules):
        """Test validation of valid rules."""
        is_valid, errors = engine_with_rules.validate_rules()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_rules_missing_default(self):
        """Test validation with missing default context."""
        engine = ContextEngine('nonexistent.json')
        engine.rules = {
            'backlit_portrait': {
                'recommended_preset': 'Test',
                'preset_blend': 50,
                'conditions': [],
                'weights': []
            }
        }
        
        is_valid, errors = engine.validate_rules()
        
        assert is_valid is False
        assert any('default' in error for error in errors)
    
    def test_validate_rules_missing_preset(self):
        """Test validation with missing recommended_preset."""
        engine = ContextEngine('nonexistent.json')
        engine.rules = {
            'default': {
                'preset_blend': 50,
                'conditions': [],
                'weights': []
            }
        }
        
        is_valid, errors = engine.validate_rules()
        
        assert is_valid is False
        assert any('recommended_preset' in error for error in errors)
    
    def test_validate_rules_mismatched_weights(self):
        """Test validation with mismatched conditions and weights."""
        engine = ContextEngine('nonexistent.json')
        engine.rules = {
            'default': {
                'recommended_preset': 'Test',
                'preset_blend': 50,
                'conditions': [
                    {'field': 'test', 'operator': '==', 'value': 1},
                    {'field': 'test2', 'operator': '==', 'value': 2}
                ],
                'weights': [1.0]  # Only one weight for two conditions
            }
        }
        
        is_valid, errors = engine.validate_rules()
        
        assert is_valid is False
        assert any('weights' in error for error in errors)
    
    # ========== Convenience Function Tests ==========
    
    def test_determine_photo_context_function(self, tmp_path, sample_rules):
        """Test convenience function for context determination."""
        rules_file = tmp_path / "context_rules.json"
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(sample_rules, f)
        
        exif_data = {
            'settings': {'iso': 800, 'focal_length': 50.0},
            'location': {'location_type': 'outdoor'},
            'datetime': {'time_of_day': 'golden_hour_evening'}
        }
        
        result = determine_photo_context(exif_data, rules_file=str(rules_file))
        
        assert 'context' in result
        assert 'recommended_preset' in result


class TestContextEngineIntegration:
    """Integration tests for ContextEngine with real-world scenarios."""
    
    @pytest.fixture
    def engine(self, tmp_path, sample_rules):
        """Create engine with sample rules."""
        rules_file = tmp_path / "context_rules.json"
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(sample_rules, f)
        return ContextEngine(str(rules_file))
    
    @pytest.fixture
    def sample_rules(self):
        """Sample rules for integration tests."""
        return {
            "contexts": {
                "default": {
                    "description": "Default",
                    "conditions": [],
                    "weights": [],
                    "recommended_preset": "Standard_v1",
                    "preset_blend": 50
                },
                "backlit_portrait": {
                    "description": "Backlit portrait",
                    "conditions": [
                        {"field": "settings.iso", "operator": ">", "value": 400},
                        {"field": "settings.focal_length", "operator": "between", "value": [35, 85]},
                        {"field": "datetime.time_of_day", "operator": "in", 
                         "value": ["golden_hour_evening", "golden_hour_morning"]}
                    ],
                    "weights": [0.3, 0.4, 0.3],
                    "recommended_preset": "WhiteLayer_v4",
                    "preset_blend": 60
                }
            }
        }
    
    def test_wedding_photography_scenario(self, engine):
        """Test context determination for wedding photography."""
        exif_data = {
            'settings': {
                'iso': 1600,
                'focal_length': 50.0,
                'aperture': 2.0
            },
            'location': {
                'location_type': 'unknown',
                'has_gps': False
            },
            'datetime': {
                'time_of_day': 'evening'
            }
        }
        
        result = engine.determine_context(exif_data)
        
        assert result['context'] is not None
        assert result['recommended_preset'] is not None
    
    def test_outdoor_portrait_scenario(self, engine):
        """Test context determination for outdoor portrait."""
        exif_data = {
            'settings': {
                'iso': 800,
                'focal_length': 85.0,
                'aperture': 1.8
            },
            'location': {
                'location_type': 'outdoor',
                'has_gps': True
            },
            'datetime': {
                'time_of_day': 'golden_hour_evening'
            }
        }
        
        result = engine.determine_context(exif_data)
        
        # Should match backlit_portrait
        assert result['context'] == 'backlit_portrait'
        assert result['score'] > 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
