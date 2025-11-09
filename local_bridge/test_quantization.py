"""
Test suite for model quantization functionality.

Tests:
- Quantization settings management
- Model name transformation
- Performance tracking
- Quantization comparison
- Integration with AI Selector

Requirements: 17.4
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from ollama_client import OllamaClient
from ai_selector import AISelector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestOllamaClientQuantization:
    """Test OllamaClient quantization features."""
    
    def test_initialization_default(self):
        """Test default initialization without quantization."""
        client = OllamaClient()
        
        assert client.enable_quantization == False
        assert client.quantization_bits == 8
        assert client.host == 'http://localhost:11434'
    
    def test_initialization_with_quantization(self):
        """Test initialization with quantization enabled."""
        client = OllamaClient(
            enable_quantization=True,
            quantization_bits=4
        )
        
        assert client.enable_quantization == True
        assert client.quantization_bits == 4
    
    def test_quantized_model_name_disabled(self):
        """Test model name when quantization is disabled."""
        client = OllamaClient(enable_quantization=False)
        
        model = "llama3.1:8b-instruct"
        result = client._get_quantized_model_name(model)
        
        assert result == model
    
    def test_quantized_model_name_8bit(self):
        """Test 8-bit quantized model name generation."""
        client = OllamaClient(enable_quantization=True, quantization_bits=8)
        
        model = "llama3.1:8b-instruct"
        result = client._get_quantized_model_name(model)
        
        assert result == "llama3.1:q8_8b-instruct"
    
    def test_quantized_model_name_4bit(self):
        """Test 4-bit quantized model name generation."""
        client = OllamaClient(enable_quantization=True, quantization_bits=4)
        
        model = "llama3.1:8b-instruct"
        result = client._get_quantized_model_name(model)
        
        assert result == "llama3.1:q4_8b-instruct"
    
    def test_quantized_model_name_no_tag(self):
        """Test quantized model name for model without tag."""
        client = OllamaClient(enable_quantization=True, quantization_bits=8)
        
        model = "llama3.1"
        result = client._get_quantized_model_name(model)
        
        assert result == "llama3.1:q8"
    
    def test_quantized_model_name_already_quantized(self):
        """Test that already quantized models are not modified."""
        client = OllamaClient(enable_quantization=True, quantization_bits=8)
        
        model = "llama3.1:q4_8b-instruct"
        result = client._get_quantized_model_name(model)
        
        assert result == model
    
    def test_set_quantization_enable(self):
        """Test enabling quantization."""
        client = OllamaClient()
        
        client.set_quantization(True, 4)
        
        assert client.enable_quantization == True
        assert client.quantization_bits == 4
    
    def test_set_quantization_disable(self):
        """Test disabling quantization."""
        client = OllamaClient(enable_quantization=True, quantization_bits=4)
        
        client.set_quantization(False)
        
        assert client.enable_quantization == False
    
    def test_set_quantization_invalid_bits(self):
        """Test that invalid quantization bits raise error."""
        client = OllamaClient()
        
        with pytest.raises(ValueError, match="Quantization bits must be 4 or 8"):
            client.set_quantization(True, 16)
    
    def test_get_quantization_settings_disabled(self):
        """Test getting quantization settings when disabled."""
        client = OllamaClient(enable_quantization=False)
        
        settings = client.get_quantization_settings()
        
        assert settings['enabled'] == False
        assert settings['bits'] is None
        assert settings['memory_reduction'] is None
    
    def test_get_quantization_settings_8bit(self):
        """Test getting 8-bit quantization settings."""
        client = OllamaClient(enable_quantization=True, quantization_bits=8)
        
        settings = client.get_quantization_settings()
        
        assert settings['enabled'] == True
        assert settings['bits'] == 8
        assert settings['memory_reduction'] == "~50% (8-bit quantization)"
    
    def test_get_quantization_settings_4bit(self):
        """Test getting 4-bit quantization settings."""
        client = OllamaClient(enable_quantization=True, quantization_bits=4)
        
        settings = client.get_quantization_settings()
        
        assert settings['enabled'] == True
        assert settings['bits'] == 4
        assert settings['memory_reduction'] == "~75% (4-bit quantization)"
    
    def test_performance_tracking(self):
        """Test performance metrics tracking."""
        client = OllamaClient()
        
        # Record some performance data
        client._record_performance("llama3.1:8b", 2.5, success=True)
        client._record_performance("llama3.1:8b", 2.3, success=True)
        client._record_performance("llama3.1:8b", 0.0, success=False)
        
        stats = client.get_performance_stats("llama3.1:8b")
        
        assert stats['total_calls'] == 3
        assert stats['successful_calls'] == 2
        assert stats['failed_calls'] == 1
        assert stats['avg_time'] == pytest.approx(2.4, rel=0.01)
        assert stats['min_time'] == 2.3
        assert stats['max_time'] == 2.5
    
    @patch('ollama_client.requests.post')
    def test_generate_with_quantization(self, mock_post):
        """Test generate method uses quantized model name."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': 'Test response'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        client = OllamaClient(enable_quantization=True, quantization_bits=4)
        
        result = client.generate(
            model="llama3.1:8b-instruct",
            prompt="Test prompt"
        )
        
        # Verify quantized model name was used
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "llama3.1:q4_8b-instruct"
        assert result == 'Test response'
    
    @patch('ollama_client.requests.get')
    def test_list_available_models(self, mock_get):
        """Test listing available models."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3.1:8b-instruct'},
                {'name': 'llama3.1:q4_8b-instruct'},
                {'name': 'mixtral:8x7b'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        models = client.list_available_models()
        
        assert len(models) == 3
        assert models[0]['name'] == 'llama3.1:8b-instruct'
    
    @patch('ollama_client.requests.get')
    def test_check_model_exists(self, mock_get):
        """Test checking if model exists."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3.1:8b-instruct'},
                {'name': 'llama3.1:q4_8b-instruct'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        
        assert client.check_model_exists('llama3.1:8b-instruct') == True
        assert client.check_model_exists('mixtral:8x7b') == False


class TestAISelectorQuantization:
    """Test AISelector quantization integration."""
    
    def test_initialization_with_quantization(self):
        """Test AISelector initialization with quantization."""
        selector = AISelector(
            enable_quantization=True,
            quantization_bits=4
        )
        
        settings = selector.get_quantization_settings()
        assert settings['enabled'] == True
        assert settings['bits'] == 4
    
    def test_set_quantization(self):
        """Test setting quantization on AISelector."""
        selector = AISelector()
        
        selector.set_quantization(True, 8)
        
        settings = selector.get_quantization_settings()
        assert settings['enabled'] == True
        assert settings['bits'] == 8
    
    def test_get_performance_stats(self):
        """Test getting performance stats from AISelector."""
        selector = AISelector()
        
        # Record some performance
        selector.ollama_client._record_performance("test_model", 1.5, True)
        
        stats = selector.get_performance_stats()
        assert 'test_model' in stats
        assert stats['test_model']['total_calls'] == 1


def test_memory_reduction_estimation():
    """Test memory reduction estimation."""
    client = OllamaClient(enable_quantization=True, quantization_bits=4)
    
    reduction = client._estimate_memory_reduction()
    assert reduction == "~75% (4-bit quantization)"
    
    client.set_quantization(True, 8)
    reduction = client._estimate_memory_reduction()
    assert reduction == "~50% (8-bit quantization)"
    
    client.set_quantization(False)
    reduction = client._estimate_memory_reduction()
    assert reduction is None


def test_quantization_integration():
    """Integration test for quantization workflow."""
    # Create client with quantization
    client = OllamaClient(enable_quantization=True, quantization_bits=8)
    
    # Verify settings
    settings = client.get_quantization_settings()
    assert settings['enabled'] == True
    assert settings['bits'] == 8
    assert '50%' in settings['memory_reduction']
    
    # Test model name transformation
    model = "llama3.1:8b-instruct"
    quantized = client._get_quantized_model_name(model)
    assert 'q8' in quantized
    
    # Switch to 4-bit
    client.set_quantization(True, 4)
    quantized = client._get_quantized_model_name(model)
    assert 'q4' in quantized
    
    # Disable quantization
    client.set_quantization(False)
    quantized = client._get_quantized_model_name(model)
    assert quantized == model


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
