"""
Test LLM-based evaluation functionality

Tests the _llm_evaluate method and related LLM integration.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_selector import AISelector


class TestLLMEvaluation(unittest.TestCase):
    """Test LLM evaluation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock Ollama client
        self.mock_ollama = Mock()
        
        # Create AI Selector with mocked Ollama client
        self.selector = AISelector(
            ollama_client=self.mock_ollama,
            enable_llm=True,
            llm_model="llama3.1:8b-instruct"
        )
    
    def test_build_evaluation_prompt(self):
        """Test evaluation prompt generation."""
        quality_results = {
            'focus_score': 4.2,
            'exposure_score': 3.8,
            'composition_score': 4.5,
            'faces_detected': 1,
            'metrics': {
                'focus': {'sharpness_category': 'sharp'},
                'exposure': {'exposure_category': 'well_exposed'},
                'composition': {'composition_category': 'excellent'}
            }
        }
        
        exif_data = {
            'camera': {'make': 'Canon', 'model': 'EOS R5'},
            'settings': {
                'iso': 400,
                'aperture': 2.8,
                'shutter_speed': '1/250',
                'focal_length': 85,
                'lens_model': 'RF 85mm f/1.2'
            }
        }
        
        context = {
            'subject_type': 'portrait',
            'lighting': 'natural',
            'location': 'outdoor',
            'time_of_day': 'afternoon'
        }
        
        prompt = self.selector._build_evaluation_prompt(
            quality_results, exif_data, context
        )
        
        # Check that prompt contains key information
        self.assertIn('4.2', prompt)  # Focus score
        self.assertIn('Canon', prompt)  # Camera make
        self.assertIn('portrait', prompt)  # Subject type
        self.assertIn('ISO: 400', prompt)  # ISO
        self.assertIn('f/2.8', prompt)  # Aperture
    
    def test_parse_llm_response_complete(self):
        """Test parsing complete LLM response."""
        response = """
SCORE: 4.5
REASONING: 優れたポートレート写真。シャープなフォーカスと適切な露出。
STRENGTHS: シャープなフォーカス, 良好な露出, 優れた構図
WEAKNESSES: わずかに暗い影, 背景がやや雑然
TAGS: portrait, natural_light, outdoor, professional, high_quality
"""
        
        evaluation = self.selector._parse_llm_response(response)
        
        self.assertEqual(evaluation['llm_score'], 4.5)
        self.assertIn('優れたポートレート', evaluation['reasoning'])
        self.assertEqual(len(evaluation['strengths']), 3)
        self.assertEqual(len(evaluation['weaknesses']), 2)
        self.assertEqual(len(evaluation['suggested_tags']), 5)
        self.assertIn('portrait', evaluation['suggested_tags'])
    
    def test_parse_llm_response_partial(self):
        """Test parsing partial LLM response."""
        response = """
SCORE: 3.0
REASONING: 平均的な品質
"""
        
        evaluation = self.selector._parse_llm_response(response)
        
        self.assertEqual(evaluation['llm_score'], 3.0)
        self.assertIn('平均的', evaluation['reasoning'])
        self.assertEqual(len(evaluation['strengths']), 0)
        self.assertEqual(len(evaluation['weaknesses']), 0)
        self.assertEqual(len(evaluation['suggested_tags']), 0)
    
    def test_parse_llm_response_invalid_score(self):
        """Test parsing LLM response with invalid score."""
        response = """
SCORE: invalid
REASONING: Test
"""
        
        evaluation = self.selector._parse_llm_response(response)
        
        # Should default to 3.0
        self.assertEqual(evaluation['llm_score'], 3.0)
    
    def test_parse_llm_response_out_of_range(self):
        """Test parsing LLM response with out-of-range score."""
        response = """
SCORE: 10.0
REASONING: Test
"""
        
        evaluation = self.selector._parse_llm_response(response)
        
        # Should clamp to 5.0
        self.assertEqual(evaluation['llm_score'], 5.0)
    
    def test_calculate_final_score_with_llm(self):
        """Test final score calculation with LLM evaluation."""
        quality_results = {
            'overall_score': 4.0,
            'focus_score': 4.0,
            'exposure_score': 4.0,
            'composition_score': 4.0,
            'metrics': {
                'focus': {},
                'exposure': {},
                'composition': {}
            }
        }
        
        exif_data = {'settings': {}}
        context = {}
        
        llm_evaluation = {
            'llm_score': 5.0,
            'reasoning': 'Excellent photo'
        }
        
        # Without LLM
        score_without_llm = self.selector._calculate_final_score(
            quality_results, exif_data, context, None
        )
        
        # With LLM
        score_with_llm = self.selector._calculate_final_score(
            quality_results, exif_data, context, llm_evaluation
        )
        
        # LLM should increase the score
        self.assertGreater(score_with_llm, score_without_llm)
        
        # Score should be blend: 4.0 * 0.7 + 5.0 * 0.3 = 4.3
        self.assertAlmostEqual(score_with_llm, 4.3, places=1)
    
    def test_generate_recommendation_with_llm_weaknesses(self):
        """Test recommendation generation with LLM weaknesses."""
        quality_results = {
            'focus_score': 3.5,
            'exposure_score': 3.5
        }
        
        # Without critical weaknesses
        llm_evaluation_ok = {
            'weaknesses': ['背景がやや雑然', '色温度が高め']
        }
        
        recommendation = self.selector._generate_recommendation(
            4.2, quality_results, llm_evaluation_ok
        )
        self.assertEqual(recommendation, 'approve')
        
        # With critical weaknesses
        llm_evaluation_critical = {
            'weaknesses': ['ピントがぼけている', '露出オーバー']
        }
        
        recommendation = self.selector._generate_recommendation(
            4.2, quality_results, llm_evaluation_critical
        )
        self.assertEqual(recommendation, 'reject')
    
    def test_generate_tags_with_llm(self):
        """Test tag generation with LLM suggestions."""
        quality_results = {
            'overall_score': 4.0,
            'faces_detected': 0,
            'metrics': {
                'focus': {'sharpness_category': 'sharp'},
                'exposure': {'exposure_category': 'well_exposed'},
                'composition': {'composition_category': 'good'}
            }
        }
        
        exif_data = {'camera': {'make': 'Canon'}}
        context = {'subject_type': 'landscape', 'lighting': 'golden_hour'}
        
        # Without LLM
        tags_without_llm = self.selector._generate_tags(
            quality_results, exif_data, context, None
        )
        
        # With LLM
        llm_evaluation = {
            'suggested_tags': ['sunset', 'mountains', 'scenic', 'vibrant colors']
        }
        
        tags_with_llm = self.selector._generate_tags(
            quality_results, exif_data, context, llm_evaluation
        )
        
        # LLM tags should be added
        self.assertGreater(len(tags_with_llm), len(tags_without_llm))
        self.assertIn('sunset', tags_with_llm)
        self.assertIn('mountains', tags_with_llm)
    
    def test_llm_evaluate_integration(self):
        """Test full LLM evaluation integration."""
        # Mock Ollama response
        self.mock_ollama.generate.return_value = """
SCORE: 4.5
REASONING: 素晴らしいポートレート写真です。
STRENGTHS: シャープ, 良好な露出, 優れた構図
WEAKNESSES: 背景がやや明るい
TAGS: portrait, professional, natural_light
"""
        
        quality_results = {
            'focus_score': 4.5,
            'exposure_score': 4.0,
            'composition_score': 4.5,
            'faces_detected': 1,
            'metrics': {
                'focus': {'sharpness_category': 'sharp'},
                'exposure': {'exposure_category': 'well_exposed'},
                'composition': {'composition_category': 'excellent'}
            }
        }
        
        exif_data = {
            'camera': {'make': 'Canon', 'model': 'EOS R5'},
            'settings': {'iso': 400, 'aperture': 2.8}
        }
        
        context = {'subject_type': 'portrait', 'lighting': 'natural'}
        
        evaluation = self.selector._llm_evaluate(
            quality_results, exif_data, context, 'test.jpg'
        )
        
        # Check evaluation results
        self.assertEqual(evaluation['llm_score'], 4.5)
        self.assertIn('ポートレート', evaluation['reasoning'])
        self.assertEqual(len(evaluation['strengths']), 3)
        self.assertEqual(len(evaluation['weaknesses']), 1)
        self.assertIn('portrait', evaluation['suggested_tags'])
        
        # Verify Ollama was called
        self.mock_ollama.generate.assert_called_once()
        call_args = self.mock_ollama.generate.call_args
        self.assertEqual(call_args[1]['model'], 'llama3.1:8b-instruct')
        self.assertEqual(call_args[1]['temperature'], 0.2)


def run_tests():
    """Run all LLM evaluation tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLLMEvaluation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
