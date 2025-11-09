"""
Tests for Multi-Model Management System.

Requirements: 18.1, 18.2, 18.3, 18.4
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from model_manager import ModelManager, ModelMetadata, ModelPurpose


@pytest.fixture
def temp_metadata_file():
    """Create temporary metadata file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    return {
        'models': [
            {'name': 'llama3.1:8b-instruct'},
            {'name': 'llama3.2:3b-instruct'}
        ]
    }


@pytest.fixture
def model_manager(temp_metadata_file):
    """Create ModelManager instance with temp file."""
    with patch('model_manager.ModelManager._sync_with_ollama'):
        manager = ModelManager(metadata_file=temp_metadata_file)
    return manager


class TestModelMetadata:
    """Test ModelMetadata dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = ModelMetadata(
            name="test-model",
            size="8b",
            purpose=ModelPurpose.BALANCED,
            description="Test model",
            recommended_use="Testing",
            min_vram_gb=4.0,
            quantization_support=["q4", "q8"]
        )
        
        data = metadata.to_dict()
        
        assert data['name'] == "test-model"
        assert data['purpose'] == "balanced"
        assert data['min_vram_gb'] == 4.0
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'name': "test-model",
            'size': "8b",
            'purpose': "balanced",
            'description': "Test model",
            'recommended_use': "Testing",
            'min_vram_gb': 4.0,
            'quantization_support': ["q4", "q8"]
        }
        
        metadata = ModelMetadata.from_dict(data)
        
        assert metadata.name == "test-model"
        assert metadata.purpose == ModelPurpose.BALANCED
        assert metadata.min_vram_gb == 4.0


class TestModelManager:
    """Test ModelManager class."""
    
    def test_initialization(self, model_manager):
        """Test manager initialization."""
        assert model_manager is not None
        assert model_manager.current_model is not None
        assert len(model_manager.models) > 0
    
    def test_list_available_models(self, model_manager):
        """Test listing available models."""
        models = model_manager.list_available_models()
        
        assert len(models) > 0
        assert all(isinstance(m, ModelMetadata) for m in models)
    
    def test_list_available_models_by_purpose(self, model_manager):
        """Test filtering models by purpose."""
        speed_models = model_manager.list_available_models(purpose=ModelPurpose.SPEED)
        
        assert all(m.purpose == ModelPurpose.SPEED for m in speed_models)
    
    def test_list_available_models_by_vram(self, model_manager):
        """Test filtering models by VRAM."""
        models = model_manager.list_available_models(max_vram_gb=4.0)
        
        assert all(m.min_vram_gb <= 4.0 for m in models)
    
    def test_list_available_models_installed_only(self, model_manager):
        """Test filtering installed models."""
        # Mark some models as installed
        for model in list(model_manager.models.values())[:2]:
            model.installed = True
        
        installed = model_manager.list_available_models(installed_only=True)
        
        assert all(m.installed for m in installed)
    
    @patch('requests.get')
    def test_list_installed_models(self, mock_get, model_manager, mock_ollama_response):
        """Test listing installed models from Ollama."""
        mock_response = Mock()
        mock_response.json.return_value = mock_ollama_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        installed = model_manager.list_installed_models()
        
        assert len(installed) == 2
        assert 'llama3.1:8b-instruct' in installed
        assert 'llama3.2:3b-instruct' in installed
    
    def test_get_model_info(self, model_manager):
        """Test getting model information."""
        info = model_manager.get_model_info("llama3.1:8b-instruct")
        
        assert info is not None
        assert info.name == "llama3.1:8b-instruct"
        assert info.size == "8b"
    
    def test_get_model_info_not_found(self, model_manager):
        """Test getting info for non-existent model."""
        info = model_manager.get_model_info("non-existent-model")
        
        assert info is None
    
    def test_get_current_model(self, model_manager):
        """Test getting current model."""
        current = model_manager.get_current_model()
        
        assert current is not None
        assert current in model_manager.models
    
    def test_switch_model(self, model_manager):
        """Test switching models."""
        # Mark model as installed
        model_manager.models["llama3.1:8b-instruct"].installed = True
        
        success = model_manager.switch_model("llama3.1:8b-instruct")
        
        assert success is True
        assert model_manager.current_model == "llama3.1:8b-instruct"
    
    def test_switch_model_not_installed(self, model_manager):
        """Test switching to non-installed model."""
        # Ensure model is not installed
        model_manager.models["llama3.1:70b-instruct"].installed = False
        
        success = model_manager.switch_model("llama3.1:70b-instruct")
        
        assert success is False
    
    def test_switch_model_not_found(self, model_manager):
        """Test switching to non-existent model."""
        success = model_manager.switch_model("non-existent-model")
        
        assert success is False
    
    @patch('requests.post')
    def test_download_model_success(self, mock_post, model_manager):
        """Test successful model download."""
        # Mock streaming response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_lines.return_value = [
            b'{"status": "downloading", "completed": 1000, "total": 2000}',
            b'{"status": "success"}'
        ]
        mock_post.return_value = mock_response
        
        success, message = model_manager.download_model("llama3.2:3b-instruct")
        
        assert success is True
        assert "Successfully downloaded" in message
    
    @patch('requests.post')
    def test_download_model_already_installed(self, mock_post, model_manager):
        """Test downloading already installed model."""
        # Mark as installed
        model_manager.models["llama3.1:8b-instruct"].installed = True
        
        success, message = model_manager.download_model("llama3.1:8b-instruct")
        
        assert success is True
        assert "already installed" in message
    
    def test_download_model_not_found(self, model_manager):
        """Test downloading non-existent model."""
        success, message = model_manager.download_model("non-existent-model")
        
        assert success is False
        assert "not found" in message
    
    @patch('requests.delete')
    def test_delete_model_success(self, mock_delete, model_manager):
        """Test successful model deletion."""
        # Setup
        model_manager.models["llama3.2:3b-instruct"].installed = True
        model_manager.current_model = "llama3.1:8b-instruct"
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response
        
        success, message = model_manager.delete_model("llama3.2:3b-instruct")
        
        assert success is True
        assert "Successfully deleted" in message
    
    def test_delete_model_current(self, model_manager):
        """Test deleting currently selected model."""
        model_manager.current_model = "llama3.1:8b-instruct"
        model_manager.models["llama3.1:8b-instruct"].installed = True
        
        success, message = model_manager.delete_model("llama3.1:8b-instruct")
        
        assert success is False
        assert "currently selected" in message
    
    def test_record_usage(self, model_manager):
        """Test recording model usage."""
        model_name = "llama3.1:8b-instruct"
        
        # Record successful usage
        model_manager.record_usage(model_name, 2.5, success=True)
        
        model = model_manager.models[model_name]
        assert model.usage_count == 1
        assert model.avg_inference_time == 2.5
        assert model.success_rate == 1.0
        
        # Record another successful usage
        model_manager.record_usage(model_name, 3.0, success=True)
        
        assert model.usage_count == 2
        assert model.avg_inference_time > 2.5  # Moving average
        assert model.success_rate == 1.0
        
        # Record a failure
        model_manager.record_usage(model_name, 0.0, success=False)
        
        assert model.usage_count == 3
        assert model.success_rate < 1.0
    
    def test_get_model_statistics(self, model_manager):
        """Test getting model statistics."""
        model_name = "llama3.1:8b-instruct"
        
        # Reset usage count first
        model_manager.models[model_name].usage_count = 0
        model_manager.models[model_name].avg_inference_time = None
        model_manager.models[model_name].success_rate = None
        
        # Record some usage
        model_manager.record_usage(model_name, 2.5, success=True)
        
        stats = model_manager.get_model_statistics(model_name)
        
        assert stats is not None
        assert stats['name'] == model_name
        assert stats['usage_count'] == 1
        assert stats['avg_inference_time'] == 2.5
        assert stats['success_rate'] == 1.0
    
    def test_get_all_statistics(self, model_manager):
        """Test getting all model statistics."""
        # Record usage for multiple models
        model_manager.record_usage("llama3.1:8b-instruct", 2.5, success=True)
        model_manager.record_usage("llama3.2:3b-instruct", 1.5, success=True)
        
        stats = model_manager.get_all_statistics()
        
        assert len(stats) > 0
        assert "llama3.1:8b-instruct" in stats
        assert "llama3.2:3b-instruct" in stats
    
    def test_recommend_model_balanced(self, model_manager):
        """Test model recommendation with balanced priority."""
        # Mark some models as installed
        model_manager.models["llama3.1:8b-instruct"].installed = True
        model_manager.models["llama3.2:3b-instruct"].installed = True
        
        recommended = model_manager.recommend_model(8.0, "balanced")
        
        assert recommended is not None
        assert recommended in model_manager.models
    
    def test_recommend_model_speed(self, model_manager):
        """Test model recommendation with speed priority."""
        # Mark speed models as installed
        model_manager.models["llama3.2:1b-instruct"].installed = True
        model_manager.models["llama3.2:3b-instruct"].installed = True
        
        recommended = model_manager.recommend_model(4.0, "speed")
        
        assert recommended is not None
        model = model_manager.models[recommended]
        assert model.purpose == ModelPurpose.SPEED
    
    def test_recommend_model_quality(self, model_manager):
        """Test model recommendation with quality priority."""
        # Mark quality models as installed
        model_manager.models["llama3.1:13b-instruct"].installed = True
        
        recommended = model_manager.recommend_model(16.0, "quality")
        
        assert recommended is not None
    
    def test_recommend_model_no_suitable(self, model_manager):
        """Test recommendation when no suitable model exists."""
        # Mark all models as not installed
        for model in model_manager.models.values():
            model.installed = False
        
        recommended = model_manager.recommend_model(8.0, "balanced")
        
        assert recommended is None
    
    def test_check_model_compatibility_compatible(self, model_manager):
        """Test compatibility check for compatible model."""
        compatible, message = model_manager.check_model_compatibility(
            "llama3.1:8b-instruct",
            8.0
        )
        
        assert compatible is True
        assert "compatible" in message.lower()
    
    def test_check_model_compatibility_insufficient_vram(self, model_manager):
        """Test compatibility check with insufficient VRAM."""
        compatible, message = model_manager.check_model_compatibility(
            "llama3.1:70b-instruct",
            8.0
        )
        
        assert compatible is False
        assert "insufficient" in message.lower()
    
    def test_export_metadata(self, model_manager, temp_metadata_file):
        """Test exporting metadata."""
        export_file = temp_metadata_file + ".export"
        
        model_manager.export_metadata(export_file)
        
        assert Path(export_file).exists()
        
        # Verify content
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        assert 'current_model' in data
        assert 'models' in data
        assert len(data['models']) > 0
        
        # Cleanup
        Path(export_file).unlink()
    
    def test_import_metadata(self, model_manager, temp_metadata_file):
        """Test importing metadata."""
        # Create test metadata file
        test_data = {
            'current_model': 'llama3.1:8b-instruct',
            'models': {
                'llama3.1:8b-instruct': {
                    'name': 'llama3.1:8b-instruct',
                    'size': '8b',
                    'purpose': 'balanced',
                    'description': 'Test',
                    'recommended_use': 'Testing',
                    'min_vram_gb': 6.0,
                    'quantization_support': ['q4', 'q8'],
                    'installed': True,
                    'usage_count': 10
                }
            }
        }
        
        import_file = temp_metadata_file + ".import"
        with open(import_file, 'w') as f:
            json.dump(test_data, f)
        
        model_manager.import_metadata(import_file)
        
        # Verify import
        assert model_manager.current_model == 'llama3.1:8b-instruct'
        model = model_manager.models['llama3.1:8b-instruct']
        assert model.usage_count == 10
        
        # Cleanup
        Path(import_file).unlink()
    
    def test_save_and_load_metadata(self, model_manager, temp_metadata_file):
        """Test saving and loading metadata."""
        # Modify some data
        model_manager.current_model = "llama3.1:8b-instruct"
        model_manager.models["llama3.1:8b-instruct"].usage_count = 5
        
        # Save
        model_manager._save_metadata()
        
        # Create new manager with same file
        with patch('model_manager.ModelManager._sync_with_ollama'):
            new_manager = ModelManager(metadata_file=temp_metadata_file)
        
        # Verify loaded data
        assert new_manager.current_model == "llama3.1:8b-instruct"
        assert new_manager.models["llama3.1:8b-instruct"].usage_count == 5


def test_model_catalog_completeness():
    """Test that model catalog has all required fields."""
    for model_name, metadata in ModelManager.MODEL_CATALOG.items():
        assert metadata.name == model_name
        assert metadata.size
        assert metadata.purpose
        assert metadata.description
        assert metadata.recommended_use
        assert metadata.min_vram_gb > 0
        assert isinstance(metadata.quantization_support, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
