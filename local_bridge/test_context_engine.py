"""
Unit tests for Context Recognition Engine.

Tests context determination, rule evaluation, and score calculation.
"""

import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime, time

from context_engine import ContextEngine, determine_photo_context


class TestContextEngine(unittest.TestCase):
    """Test cases for ContextEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary rules file for testing
        self.temp_rules = self._create_test_rules()
        self.engine = ContextEngine(self.temp_rules.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'temp_rules'):
            self.temp_rules.close()
    
    def _create_test_rules(self):
        """Create a temporary rules file for testing"""
        rules = {
            "version": "1.0",
            "contexts": {
                "backlit_portrait": {
                    "description": "逆光ポートレート",
                    "conditions": [
                        {"field": "settings.iso", "operator": ">", "value": 400},
                        {"field": "settings.focal_length", "operator": "between", "value": [35, 85]},
                        {"field": "context_hints.time_of_day", "operator": "==", "value": "golden_hour_evening"}
                    ],
                    "weights": [0.3, 0.4, 0.3],
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
                "default": {
                    "description": "デフォルト",
                    "conditions": [],
                    "weights": [],
                    "recommended_preset": "Standard_Balanced_v1",
                    "preset_blend": 50
                }
            }
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(rules, temp_file)
        temp_file.flush()
        return temp_file
    
    def _create_sample_exif_data(self, **overrides):
        """Create sample EXIF data for testing"""
        data = {
            'camera': {
                'make': 'Canon',
                'model': 'EOS R5',
                'lens': 'RF 50mm F1.8'
            },
            'settings': {
                'iso': 800,
                'focal_length': 50.0,
                'aperture': 2.8,
                'shutter_speed': '1/250',
                'exposure_compensation': 0.0
            },
            'location': {
                'latitude': None,
                'longitude': None,
                'location_type': 'unknown',
                'has_gps': False
            },
            'datetime': {
                'capture_time': datetime(2025, 11, 8, 17, 30),
                'time_of_day': 'golden_hour_evening'
            },
            'context_hints': {
                'lighting': 'moderate_light',
                'subject_type': 'standard',
                'time_of_day': 'golden_hour_evening'
            }
        }
        
        # Apply overrides
        for key, value in overrides.items():
            if '.' in key:
                parts = key.split('.')
                current = data
                for part in parts[:-1]:
                    current = current[part]
                current[parts[-1]] = value
            else:
                data[key] = value
        
        return data
    
    def test_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.rules)
        self.assertIn('default', self.engine.rules)
    
    def test_load_context_rules(self):
        """Test loading context rules from file"""
        rules = self.engine.rules
        self.assertIn('backlit_portrait', rules)
        self.assertIn('low_light_indoor', rules)
        self.assertIn('default', rules)
    
    def test_backlit_portrait_detection(self):
        """Test detection of backlit portrait context"""
        exif_data = self._create_sample_exif_data()
        exif_data['settings']['iso'] = 500
        exif_data['settings']['focal_length'] = 50.0
        exif_data['context_hints']['time_of_day'] = 'golden_hour_evening'
        
        result = self.engine.determine_context(exif_data)
        
        self.assertEqual(result['context'], 'backlit_portrait')
        self.assertGreater(result['score'], 0.5)
        self.assertEqual(result['recommended_preset'], 'WhiteLayer_Transparency_v4')
        self.assertEqual(result['preset_blend'], 60)
    
    def test_low_light_indoor_detection(self):
        """Test detection of low light indoor context"""
        exif_data = self._create_sample_exif_data()
        exif_data['settings']['iso'] = 3200
        exif_data['location']['has_gps'] = False
        exif_data['context_hints']['time_of_day'] = 'evening'
        
        result = self.engine.determine_context(exif_data)
        
        self.assertEqual(result['context'], 'low_light_indoor')
        self.assertGreater(result['score'], 0.5)
        self.assertEqual(result['recommended_preset'], 'LowLight_NR_v2')
    
    def test_default_context_fallback(self):
        """Test fallback to default context when no match"""
        exif_data = self._create_sample_exif_data()
        exif_data['settings']['iso'] = 200
        exif_data['settings']['focal_length'] = 24.0
        exif_data['context_hints']['time_of_day'] = 'midday'
        
        result = self.engine.determine_context(exif_data)
        
        # Should fall back to default due to low scores
        self.assertEqual(result['context'], 'default')
        self.assertEqual(result['recommended_preset'], 'Standard_Balanced_v1')
    
    def test_operator_greater_than(self):
        """Test > operator"""
        condition = {"field": "settings.iso", "operator": ">", "value": 1000}
        exif_data = self._create_sample_exif_data()
        exif_data['settings']['iso'] = 1600
        
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertTrue(result)
        
        exif_data['settings']['iso'] = 800
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertFalse(result)
    
    def test_operator_between(self):
        """Test between operator"""
        condition = {
            "field": "settings.focal_length",
            "operator": "between",
            "value": [35, 85]
        }
        exif_data = self._create_sample_exif_data()
        
        exif_data['settings']['focal_length'] = 50.0
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertTrue(result)
        
        exif_data['settings']['focal_length'] = 24.0
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertFalse(result)
        
        exif_data['settings']['focal_length'] = 100.0
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertFalse(result)
    
    def test_operator_in(self):
        """Test in operator"""
        condition = {
            "field": "context_hints.time_of_day",
            "operator": "in",
            "value": ["golden_hour_evening", "golden_hour_morning"]
        }
        exif_data = self._create_sample_exif_data()
        
        exif_data['context_hints']['time_of_day'] = 'golden_hour_evening'
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertTrue(result)
        
        exif_data['context_hints']['time_of_day'] = 'midday'
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertFalse(result)
    
    def test_operator_equals(self):
        """Test == operator"""
        condition = {
            "field": "location.has_gps",
            "operator": "==",
            "value": False
        }
        exif_data = self._create_sample_exif_data()
        
        exif_data['location']['has_gps'] = False
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertTrue(result)
        
        exif_data['location']['has_gps'] = True
        result = self.engine._evaluate_condition(condition, exif_data)
        self.assertFalse(result)
    
    def test_shutter_speed_comparison(self):
        """Test shutter speed comparison"""
        # Test faster shutter speed
        self.assertTrue(
            self.engine._compare_shutter_speeds("1/1000", "1/500")
        )
        
        # Test slower shutter speed
        self.assertFalse(
            self.engine._compare_shutter_speeds("1/250", "1/500")
        )
        
        # Test equal shutter speed
        self.assertFalse(
            self.engine._compare_shutter_speeds("1/500", "1/500")
        )
    
    def test_parse_shutter_speed(self):
        """Test shutter speed parsing"""
        # Test fraction format
        self.assertAlmostEqual(
            self.engine._parse_shutter_speed("1/500"),
            0.002
        )
        
        # Test decimal format
        self.assertAlmostEqual(
            self.engine._parse_shutter_speed("2.5"),
            2.5
        )
        
        # Test invalid format
        self.assertIsNone(
            self.engine._parse_shutter_speed("invalid")
        )
    
    def test_get_field_value(self):
        """Test nested field value retrieval"""
        exif_data = self._create_sample_exif_data()
        
        # Test nested access
        value = self.engine._get_field_value('settings.iso', exif_data)
        self.assertEqual(value, 800)
        
        # Test deeper nesting
        value = self.engine._get_field_value('context_hints.time_of_day', exif_data)
        self.assertEqual(value, 'golden_hour_evening')
        
        # Test non-existent field
        value = self.engine._get_field_value('nonexistent.field', exif_data)
        self.assertIsNone(value)
    
    def test_get_context_list(self):
        """Test getting list of available contexts"""
        contexts = self.engine.get_context_list()
        
        self.assertIsInstance(contexts, list)
        self.assertGreater(len(contexts), 0)
        
        # Check structure
        for context in contexts:
            self.assertIn('name', context)
            self.assertIn('description', context)
            self.assertIn('recommended_preset', context)
            self.assertIn('preset_blend', context)
    
    def test_validate_rules(self):
        """Test rule validation"""
        is_valid, errors = self.engine.validate_rules()
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_rules_with_errors(self):
        """Test rule validation with invalid rules"""
        # Create invalid rules
        invalid_rules = {
            "version": "1.0",
            "contexts": {
                "invalid_context": {
                    "description": "Missing required fields",
                    "conditions": [
                        {"field": "settings.iso", "operator": ">"}  # Missing value
                    ],
                    "weights": [1.0, 0.5]  # Mismatched weights
                }
            }
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(invalid_rules, temp_file)
        temp_file.flush()
        temp_file.close()
        
        engine = ContextEngine(temp_file.name)
        is_valid, errors = engine.validate_rules()
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # Clean up
        Path(temp_file.name).unlink()
    
    def test_score_calculation(self):
        """Test context score calculation"""
        exif_data = self._create_sample_exif_data()
        exif_data['settings']['iso'] = 500
        exif_data['settings']['focal_length'] = 50.0
        exif_data['context_hints']['time_of_day'] = 'golden_hour_evening'
        
        result = self.engine.determine_context(exif_data)
        
        # All conditions met, should have high score
        self.assertGreater(result['score'], 0.9)
        
        # Check all_scores contains multiple contexts
        self.assertIn('all_scores', result)
        self.assertIsInstance(result['all_scores'], dict)
    
    def test_convenience_function(self):
        """Test convenience function"""
        exif_data = self._create_sample_exif_data()
        exif_data['settings']['iso'] = 3200
        exif_data['location']['has_gps'] = False
        
        result = determine_photo_context(exif_data, rules_file=self.temp_rules.name)
        
        self.assertIn('context', result)
        self.assertIn('score', result)
        self.assertIn('recommended_preset', result)
    
    def test_reload_rules(self):
        """Test reloading rules"""
        initial_count = len(self.engine.rules)
        
        success = self.engine.reload_rules()
        
        self.assertTrue(success)
        self.assertEqual(len(self.engine.rules), initial_count)
    
    def test_with_ai_evaluation(self):
        """Test context determination with AI evaluation data"""
        exif_data = self._create_sample_exif_data()
        ai_eval = {
            'overall_score': 4.5,
            'focus_score': 4.8,
            'faces_detected': 1
        }
        
        result = self.engine.determine_context(exif_data, ai_eval)
        
        self.assertIsNotNone(result)
        self.assertIn('context', result)


class TestContextEngineIntegration(unittest.TestCase):
    """Integration tests with real rules file"""
    
    def setUp(self):
        """Set up with real rules file"""
        rules_file = Path(__file__).parent / 'config' / 'context_rules.json'
        if rules_file.exists():
            self.engine = ContextEngine(str(rules_file))
            self.has_real_rules = True
        else:
            self.has_real_rules = False
            self.skipTest("Real context_rules.json not found")
    
    def test_all_contexts_loadable(self):
        """Test that all contexts in real file are loadable"""
        if not self.has_real_rules:
            self.skipTest("Real rules file not available")
        
        self.assertGreater(len(self.engine.rules), 10)
        self.assertIn('default', self.engine.rules)
    
    def test_real_rules_validation(self):
        """Test validation of real rules file"""
        if not self.has_real_rules:
            self.skipTest("Real rules file not available")
        
        is_valid, errors = self.engine.validate_rules()
        
        if not is_valid:
            print(f"Validation errors: {errors}")
        
        self.assertTrue(is_valid, f"Rules validation failed: {errors}")


if __name__ == '__main__':
    unittest.main()
