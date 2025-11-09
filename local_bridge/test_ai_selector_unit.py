"""
Unit tests for AI Selection Engine.

Tests AI-powered photo selection, quality evaluation integration,
LLM-based assessment, and recommendation generation.

Requirements: 2.1, 2.2, 2.3, 2.5
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from ai_selector import AISelector


class TestAISelector:
    """Test suite for AISelector class."""
    
    @pytest.fixture
    def mock_quality_evaluator(self):
        """Create mock quality evaluator."""
        evaluator = Mock()
        evaluator.evaluate.return_value = {
            'overall_score': 4.2,
            'focus_score': 4.5,
            'exposure_score': 4.0,
            'composition_score': 4.1,
            'faces_detected': 1,
            'metrics': {
                'focus': {'sharpness_category': 'sharp'},
                'exposure': {'exposure_category': 'well_exposed'},
                'composition': {'composition_category': 'good'}
            }
        }
        return evaluator
    
    @pytest.fixture
    def mock_exif_analyzer(self):
        """Create mock EXIF analyzer."""
        analyzer = Mock()
        analyzer.analyze.return_value = {
            'camera': {
                'make': 'Canon',
                'model': 'EOS R5',
                'lens': 'RF 50mm F1.2'
            },
            'settings': {
                'iso': 800,
                'focal_length': 50.0,
                'aperture': 1.8,
                'shutter_speed': '1/250',
                'lens_model': 'RF 50mm F1.2'
            },
            'location': {
                'location_type': 'outdoor',
                'has_gps': True
            },
            'datetime': {
                'time_of_day': 'golden_hour_evening'
            },
            'context_hints': {
                'lighting': 'good_light',
                'subject_type': 'portrait'
            }
        }
        return analyzer
    
    @pytest.fixture
    def mock_context_engine(self):
        """Create mock context engine."""
        engine = Mock()
        engine.determine_context.return_value = {
            'context': 'backlit_portrait',
            'score': 0.85,
            'subject_type': 'portrait',
            'lighting': 'backlit',
            'location': 'outdoor',
            'time_of_day': 'golden_hour_evening'
        }
        return engine
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create mock Ollama client."""
        client = Mock()
        client.generate.return_value = """SCORE: 4.5
REASONING: 優れたポートレート写真。ピントが正確で、ゴールデンアワーの柔らかい光が被写体を美しく照らしています。
STRENGTHS: シャープなフォーカス, 美しい光, 良い構図
WEAKNESSES: わずかな露出オーバー
TAGS: ポートレート, ゴールデンアワー, 屋外, 自然光, 人物"""
        return client
    
    @pytest.fixture
    def ai_selector(self, mock_quality_evaluator, mock_exif_analyzer, 
                    mock_context_engine, mock_ollama_client):
        """Create AISelector instance with mocked dependencies."""
        return AISelector(
            quality_evaluator=mock_quality_evaluator,
            exif_analyzer=mock_exif_analyzer,
            context_engine=mock_context_engine,
            ollama_client=mock_ollama_client,
            enable_llm=True
        )
    
    # ========== Initialization Tests ==========
    
    def test_initialization_with_defaults(self):
        """Test AISelector initialization with default parameters."""
        with patch('ai_selector.ImageQualityEvaluator'), \
             patch('ai_selector.EXIFAnalyzer'), \
             patch('ai_selector.ContextEngine'), \
             patch('ai_selector.OllamaClient'):
            selector = AISelector()
            
            assert selector is not None
            assert selector.enable_llm is True
            assert selector.llm_model == "llama3.1:8b-instruct"
    
    def test_initialization_with_quantization(self):
        """Test AISelector initialization with quantization enabled."""
        with patch('ai_selector.ImageQualityEvaluator'), \
             patch('ai_selector.EXIFAnalyzer'), \
             patch('ai_selector.ContextEngine'), \
             patch('ai_selector.OllamaClient') as mock_ollama:
            selector = AISelector(
                enable_quantization=True,
                quantization_bits=4
            )
            
            mock_ollama.assert_called_once_with(
                enable_quantization=True,
                quantization_bits=4
            )
    
    # ========== Evaluation Tests ==========
    
    def test_evaluate_basic(self, ai_selector, mock_quality_evaluator,
                           mock_exif_analyzer, mock_context_engine):
        """Test basic photo evaluation."""
        result = ai_selector.evaluate('test_photo.jpg')
        
        # Verify all components were called
        mock_quality_evaluator.evaluate.assert_called_once_with('test_photo.jpg')
        mock_exif_analyzer.analyze.assert_called_once_with('test_photo.jpg')
        mock_context_engine.determine_context.assert_called_once()
        
        # Verify result structure
        assert 'overall_score' in result
        assert 'quality' in result
        assert 'exif' in result
        assert 'context' in result
        assert 'recommendation' in result
        assert 'tags' in result
        assert 'metrics' in result
    
    def test_evaluate_with_llm(self, ai_selector, mock_ollama_client):
        """Test evaluation with LLM enabled."""
        result = ai_selector.evaluate('test_photo.jpg')
        
        # Verify LLM was called
        mock_ollama_client.generate.assert_called_once()
        
        # Verify LLM evaluation is included
        assert 'llm_evaluation' in result
        assert result['llm_evaluation']['llm_score'] == 4.5
    
    def test_evaluate_without_llm(self, mock_quality_evaluator, mock_exif_analyzer,
                                  mock_context_engine):
        """Test evaluation with LLM disabled."""
        selector = AISelector(
            quality_evaluator=mock_quality_evaluator,
            exif_analyzer=mock_exif_analyzer,
            context_engine=mock_context_engine,
            enable_llm=False
        )
        
        result = selector.evaluate('test_photo.jpg')
        
        # Verify LLM evaluation is not included
        assert 'llm_evaluation' not in result
    
    def test_evaluate_llm_failure_graceful(self, ai_selector, mock_ollama_client):
        """Test graceful handling of LLM failure."""
        mock_ollama_client.generate.side_effect = Exception("LLM error")
        
        # Should not raise exception
        result = ai_selector.evaluate('test_photo.jpg')
        
        # Should still return valid result without LLM evaluation
        assert 'overall_score' in result
        assert 'llm_evaluation' not in result
    
    # ========== LLM Evaluation Tests ==========
    
    def test_build_evaluation_prompt(self, ai_selector):
        """Test LLM evaluation prompt building."""
        quality_results = {
            'focus_score': 4.5,
            'exposure_score': 4.0,
            'composition_score': 4.1,
            'faces_detected': 1,
            'metrics': {
                'focus': {'sharpness_category': 'sharp'},
                'exposure': {'exposure_category': 'well_exposed'},
                'composition': {'composition_category': 'good'}
            }
        }
        
        exif_data = {
            'camera': {'make': 'Canon', 'model': 'EOS R5'},
            'settings': {
                'iso': 800,
                'focal_length': 50.0,
                'aperture': 1.8,
                'shutter_speed': '1/250',
                'lens_model': 'RF 50mm F1.2'
            }
        }
        
        context = {
            'subject_type': 'portrait',
            'lighting': 'good_light',
            'location': 'outdoor',
            'time_of_day': 'golden_hour'
        }
        
        prompt = ai_selector._build_evaluation_prompt(quality_results, exif_data, context)
        
        # Verify prompt contains key information
        assert 'Canon' in prompt
        assert 'EOS R5' in prompt
        assert '800' in prompt  # ISO
        assert '50' in prompt  # Focal length
        assert 'portrait' in prompt
        assert 'golden_hour' in prompt
    
    def test_parse_llm_response(self, ai_selector):
        """Test LLM response parsing."""
        response = """SCORE: 4.5
REASONING: 優れた写真です。
STRENGTHS: シャープ, 良い露出, 美しい構図
WEAKNESSES: わずかなノイズ
TAGS: ポートレート, 屋外, 自然光"""
        
        evaluation = ai_selector._parse_llm_response(response)
        
        assert evaluation['llm_score'] == 4.5
        assert '優れた写真です' in evaluation['reasoning']
        assert len(evaluation['strengths']) == 3
        assert 'シャープ' in evaluation['strengths']
        assert len(evaluation['weaknesses']) == 1
        assert len(evaluation['suggested_tags']) == 3
    
    def test_parse_llm_response_invalid_score(self, ai_selector):
        """Test LLM response parsing with invalid score."""
        response = "SCORE: invalid\nREASONING: Test"
        
        evaluation = ai_selector._parse_llm_response(response)
        
        # Should use default score
        assert evaluation['llm_score'] == 3.0
    
    def test_parse_llm_response_out_of_range_score(self, ai_selector):
        """Test LLM response parsing with out-of-range score."""
        response = "SCORE: 10.0\nREASONING: Test"
        
        evaluation = ai_selector._parse_llm_response(response)
        
        # Should clamp to valid range
        assert evaluation['llm_score'] == 5.0
    
    # ========== Score Calculation Tests ==========
    
    def test_calculate_final_score_basic(self, ai_selector):
        """Test final score calculation without LLM."""
        quality_results = {'overall_score': 4.0}
        exif_data = {'settings': {'iso': 400}}
        context = {'lighting': 'good_light'}
        
        score = ai_selector._calculate_final_score(
            quality_results, exif_data, context, None
        )
        
        assert 1.0 <= score <= 5.0
        assert score >= 4.0  # Should be at least base score
    
    def test_calculate_final_score_with_llm(self, ai_selector):
        """Test final score calculation with LLM evaluation."""
        quality_results = {'overall_score': 4.0}
        exif_data = {'settings': {'iso': 400}}
        context = {'lighting': 'good_light'}
        llm_evaluation = {'llm_score': 4.5}
        
        score = ai_selector._calculate_final_score(
            quality_results, exif_data, context, llm_evaluation
        )
        
        # Should blend technical (70%) and LLM (30%) scores
        expected = 4.0 * 0.7 + 4.5 * 0.3
        assert abs(score - expected) < 0.5  # Allow for adjustments
    
    def test_calculate_final_score_iso_bonus(self, ai_selector):
        """Test score adjustment for good ISO usage."""
        quality_results = {'overall_score': 4.0}
        exif_data = {'settings': {'iso': 400}}  # Good ISO
        context = {}
        
        score = ai_selector._calculate_final_score(
            quality_results, exif_data, context, None
        )
        
        # Should get bonus for good ISO
        assert score >= 4.0
    
    def test_calculate_final_score_high_iso_penalty(self, ai_selector):
        """Test score adjustment for high ISO."""
        quality_results = {'overall_score': 4.0}
        exif_data = {'settings': {'iso': 6400}}  # High ISO
        context = {}
        
        score = ai_selector._calculate_final_score(
            quality_results, exif_data, context, None
        )
        
        # May get penalty for high ISO
        assert 1.0 <= score <= 5.0
    
    def test_calculate_final_score_low_light_bonus(self, ai_selector):
        """Test bonus for good low-light handling."""
        quality_results = {'overall_score': 4.0, 'exposure_score': 4.0}
        exif_data = {'settings': {}}
        context = {'lighting': 'low_light'}
        
        score = ai_selector._calculate_final_score(
            quality_results, exif_data, context, None
        )
        
        # Should get bonus for handling low light well
        assert score >= 4.0
    
    # ========== Recommendation Tests ==========
    
    def test_generate_recommendation_approve(self, ai_selector):
        """Test recommendation generation for high-quality photo."""
        quality_results = {
            'focus_score': 4.5,
            'exposure_score': 4.5,
            'composition_score': 4.5
        }
        
        recommendation = ai_selector._generate_recommendation(4.5, quality_results, None)
        
        assert recommendation == 'approve'
    
    def test_generate_recommendation_review(self, ai_selector):
        """Test recommendation generation for medium-quality photo."""
        quality_results = {
            'focus_score': 3.5,
            'exposure_score': 3.5,
            'composition_score': 3.5
        }
        
        recommendation = ai_selector._generate_recommendation(3.5, quality_results, None)
        
        assert recommendation == 'review'
    
    def test_generate_recommendation_reject(self, ai_selector):
        """Test recommendation generation for low-quality photo."""
        quality_results = {
            'focus_score': 2.0,
            'exposure_score': 2.0,
            'composition_score': 2.0
        }
        
        recommendation = ai_selector._generate_recommendation(2.0, quality_results, None)
        
        assert recommendation == 'reject'
    
    def test_generate_recommendation_reject_poor_focus(self, ai_selector):
        """Test rejection for poor focus despite good score."""
        quality_results = {
            'focus_score': 2.0,  # Poor focus
            'exposure_score': 4.0,
            'composition_score': 4.0
        }
        
        recommendation = ai_selector._generate_recommendation(3.5, quality_results, None)
        
        assert recommendation == 'reject'
    
    def test_generate_recommendation_with_llm_weaknesses(self, ai_selector):
        """Test recommendation considering LLM weaknesses."""
        quality_results = {
            'focus_score': 4.0,
            'exposure_score': 4.0,
            'composition_score': 4.0
        }
        llm_evaluation = {
            'weaknesses': ['ぼけている', '露出オーバー']
        }
        
        recommendation = ai_selector._generate_recommendation(
            4.0, quality_results, llm_evaluation
        )
        
        # Should reject due to critical weaknesses
        assert recommendation == 'reject'
    
    # ========== Tag Generation Tests ==========
    
    def test_generate_tags_basic(self, ai_selector):
        """Test basic tag generation."""
        quality_results = {
            'overall_score': 4.5,
            'faces_detected': 1,
            'metrics': {
                'focus': {'sharpness_category': 'sharp'},
                'exposure': {'exposure_category': 'well_exposed'},
                'composition': {'composition_category': 'good'}
            }
        }
        exif_data = {'camera': {'make': 'Canon'}}
        context = {'subject_type': 'portrait', 'lighting': 'good_light'}
        
        tags = ai_selector._generate_tags(quality_results, exif_data, context, None)
        
        assert 'excellent_quality' in tags
        assert 'sharp' in tags
        assert 'portrait' in tags
        assert 'single_person' in tags
        assert 'canon' in tags
    
    def test_generate_tags_with_llm(self, ai_selector):
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
        exif_data = {'camera': {}}
        context = {}
        llm_evaluation = {
            'suggested_tags': ['自然光', 'ゴールデンアワー', '屋外']
        }
        
        tags = ai_selector._generate_tags(
            quality_results, exif_data, context, llm_evaluation
        )
        
        # Should include LLM tags
        assert '自然光' in tags
        assert 'ゴールデンアワー' in tags
    
    def test_generate_tags_group_photo(self, ai_selector):
        """Test tag generation for group photos."""
        quality_results = {
            'overall_score': 4.0,
            'faces_detected': 5,
            'metrics': {
                'focus': {'sharpness_category': 'sharp'},
                'exposure': {'exposure_category': 'well_exposed'},
                'composition': {'composition_category': 'good'}
            }
        }
        exif_data = {'camera': {}}
        context = {}
        
        tags = ai_selector._generate_tags(quality_results, exif_data, context, None)
        
        assert 'portrait' in tags
        assert 'group' in tags
    
    # ========== Batch Processing Tests ==========
    
    def test_batch_evaluate(self, ai_selector):
        """Test batch evaluation of multiple images."""
        image_paths = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
        
        results = ai_selector.batch_evaluate(image_paths)
        
        assert len(results) == 3
        for result in results:
            assert 'file_path' in result
            assert 'overall_score' in result
    
    def test_batch_evaluate_with_error(self, ai_selector, mock_quality_evaluator):
        """Test batch evaluation with one failing image."""
        mock_quality_evaluator.evaluate.side_effect = [
            {'overall_score': 4.0, 'focus_score': 4.0, 'exposure_score': 4.0,
             'composition_score': 4.0, 'faces_detected': 0,
             'metrics': {'focus': {}, 'exposure': {}, 'composition': {}}},
            Exception("Processing error"),
            {'overall_score': 3.5, 'focus_score': 3.5, 'exposure_score': 3.5,
             'composition_score': 3.5, 'faces_detected': 0,
             'metrics': {'focus': {}, 'exposure': {}, 'composition': {}}}
        ]
        
        image_paths = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
        results = ai_selector.batch_evaluate(image_paths)
        
        assert len(results) == 3
        assert results[1]['recommendation'] == 'error'
        assert 'error' in results[1]
    
    def test_filter_by_quality(self, ai_selector):
        """Test filtering images by quality threshold."""
        with patch.object(ai_selector, 'batch_evaluate') as mock_batch:
            mock_batch.return_value = [
                {'file_path': 'photo1.jpg', 'overall_score': 4.5},
                {'file_path': 'photo2.jpg', 'overall_score': 3.0},
                {'file_path': 'photo3.jpg', 'overall_score': 4.0}
            ]
            
            image_paths = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
            filtered = ai_selector.filter_by_quality(image_paths, min_score=3.5)
            
            assert len(filtered) == 2
            assert 'photo1.jpg' in filtered
            assert 'photo3.jpg' in filtered
            assert 'photo2.jpg' not in filtered
    
    # ========== Quantization Tests ==========
    
    def test_set_quantization(self, ai_selector, mock_ollama_client):
        """Test setting quantization."""
        ai_selector.set_quantization(True, 4)
        
        mock_ollama_client.set_quantization.assert_called_once_with(True, 4)
    
    def test_get_quantization_settings(self, ai_selector, mock_ollama_client):
        """Test getting quantization settings."""
        mock_ollama_client.get_quantization_settings.return_value = {
            'enabled': True,
            'bits': 8
        }
        
        settings = ai_selector.get_quantization_settings()
        
        assert settings['enabled'] is True
        assert settings['bits'] == 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
