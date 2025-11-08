"""
Test suite for Configuration Manager

Tests all functionality of the configuration management system:
- Schema validation
- Loading and saving
- Default generation
- Get/Set operations
- Import/Export
- Error handling
"""

import json
import pathlib
import tempfile
import shutil
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    pytest = None

from config_manager import ConfigManager, DEFAULT_CONFIG, CONFIG_SCHEMA


if PYTEST_AVAILABLE:
    class TestConfigManager:
        """Test suite for ConfigManager class"""
        
        @pytest.fixture
        def temp_dir(self):
            """Create a temporary directory for test files"""
            temp_path = pathlib.Path(tempfile.mkdtemp())
            yield temp_path
            shutil.rmtree(temp_path)
        
        @pytest.fixture
        def config_manager(self, temp_dir):
            """Create a ConfigManager instance with temporary config path"""
            config_path = temp_dir / "test_config.json"
            return ConfigManager(config_path)
    
    def test_generate_default_config(self, config_manager):
        """Test default configuration generation"""
        config = config_manager.generate_default()
        
        assert config is not None
        assert config['version'] == '2.0'
        assert 'system' in config
        assert 'ai' in config
        assert 'processing' in config
        assert 'export' in config
        assert 'notifications' in config
        assert 'ui' in config
    
    def test_validate_valid_config(self, config_manager):
        """Test validation of valid configuration"""
        config = config_manager.generate_default()
        is_valid, error = config_manager.validate(config)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_invalid_config_missing_required(self, config_manager):
        """Test validation of invalid configuration (missing required fields)"""
        invalid_config = {
            "version": "2.0"
            # Missing required fields
        }
        
        is_valid, error = config_manager.validate(invalid_config)
        
        assert is_valid is False
        assert error is not None
        assert 'required' in error.lower()
    
    def test_validate_invalid_config_wrong_type(self, config_manager):
        """Test validation of invalid configuration (wrong type)"""
        config = config_manager.generate_default()
        config['processing']['max_concurrent_jobs'] = "not_a_number"  # Should be integer
        
        is_valid, error = config_manager.validate(config)
        
        assert is_valid is False
        assert error is not None
    
    def test_validate_invalid_config_out_of_range(self, config_manager):
        """Test validation of invalid configuration (out of range)"""
        config = config_manager.generate_default()
        config['processing']['max_concurrent_jobs'] = 100  # Max is 10
        
        is_valid, error = config_manager.validate(config)
        
        assert is_valid is False
        assert error is not None
    
    def test_save_and_load_config(self, config_manager):
        """Test saving and loading configuration"""
        # Generate and save
        original_config = config_manager.generate_default()
        config_manager.save()
        
        # Load
        loaded_config = config_manager.load()
        
        assert loaded_config == original_config
        assert loaded_config['version'] == '2.0'
    
    def test_load_creates_default_if_not_exists(self, config_manager):
        """Test that load creates default config if file doesn't exist"""
        # Ensure file doesn't exist
        assert not config_manager.config_path.exists()
        
        # Load should create default
        config = config_manager.load()
        
        assert config is not None
        assert config_manager.config_path.exists()
        assert config['version'] == '2.0'
    
    def test_get_config_value(self, config_manager):
        """Test getting configuration value by key path"""
        config_manager.generate_default()
        
        # Test simple path
        llm_model = config_manager.get('ai.llm_model')
        assert llm_model == 'llama3.1:8b-instruct'
        
        # Test nested path
        max_jobs = config_manager.get('processing.max_concurrent_jobs')
        assert max_jobs == 3
        
        # Test with default
        non_existent = config_manager.get('non.existent.key', 'default_value')
        assert non_existent == 'default_value'
    
    def test_set_config_value(self, config_manager):
        """Test setting configuration value by key path"""
        config_manager.generate_default()
        
        # Set value
        config_manager.set('ai.llm_model', 'llama3.1:11b')
        
        # Verify
        assert config_manager.get('ai.llm_model') == 'llama3.1:11b'
    
    def test_update_config(self, config_manager):
        """Test updating configuration with partial updates"""
        config_manager.generate_default()
        
        # Update
        updates = {
            'ai': {
                'llm_model': 'llama3.1:11b',
                'gpu_memory_limit_mb': 8192
            },
            'processing': {
                'max_concurrent_jobs': 5
            }
        }
        config_manager.update(updates)
        
        # Verify
        assert config_manager.get('ai.llm_model') == 'llama3.1:11b'
        assert config_manager.get('ai.gpu_memory_limit_mb') == 8192
        assert config_manager.get('processing.max_concurrent_jobs') == 5
        
        # Verify other values unchanged
        assert config_manager.get('ai.llm_provider') == 'ollama'
    
    def test_reset_to_default(self, config_manager):
        """Test resetting configuration to defaults"""
        config_manager.generate_default()
        
        # Modify config
        config_manager.set('ai.llm_model', 'modified_model')
        assert config_manager.get('ai.llm_model') == 'modified_model'
        
        # Reset
        config_manager.reset_to_default()
        
        # Verify reset
        assert config_manager.get('ai.llm_model') == 'llama3.1:8b-instruct'
    
    def test_export_to_file(self, config_manager, temp_dir):
        """Test exporting configuration to file"""
        config_manager.generate_default()
        export_path = temp_dir / "exported_config.json"
        
        # Export
        config_manager.export_to_file(export_path)
        
        # Verify file exists and content
        assert export_path.exists()
        
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_config = json.load(f)
        
        assert exported_config == config_manager.config
    
    def test_import_from_file(self, config_manager, temp_dir):
        """Test importing configuration from file"""
        # Create a config file to import
        import_config = config_manager.generate_default()
        import_config['ai']['llm_model'] = 'imported_model'
        
        import_path = temp_dir / "import_config.json"
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(import_config, f)
        
        # Import
        imported_config = config_manager.import_from_file(import_path)
        
        # Verify
        assert imported_config['ai']['llm_model'] == 'imported_model'
        assert config_manager.get('ai.llm_model') == 'imported_model'
    
    def test_import_invalid_file_raises_error(self, config_manager, temp_dir):
        """Test that importing invalid file raises error"""
        # Create invalid JSON file
        invalid_path = temp_dir / "invalid.json"
        with open(invalid_path, 'w') as f:
            f.write("not valid json {")
        
        # Should raise error
        with pytest.raises(json.JSONDecodeError):
            config_manager.import_from_file(invalid_path)
    
    def test_import_nonexistent_file_raises_error(self, config_manager, temp_dir):
        """Test that importing non-existent file raises error"""
        nonexistent_path = temp_dir / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            config_manager.import_from_file(nonexistent_path)
    
    def test_save_invalid_config_raises_error(self, config_manager):
        """Test that saving invalid configuration raises error"""
        config_manager.config = {"version": "2.0"}  # Invalid - missing required fields
        
        with pytest.raises(Exception):  # Should raise validation error
            config_manager.save()
    
    def test_export_presets_structure(self, config_manager):
        """Test that export presets have correct structure"""
        config = config_manager.generate_default()
        presets = config['export']['presets']
        
        assert len(presets) == 3  # SNS, Print, Archive
        
        for preset in presets:
            assert 'name' in preset
            assert 'enabled' in preset
            assert 'format' in preset
            assert 'quality' in preset
            assert 'max_dimension' in preset
            assert 'color_space' in preset
            assert 'destination' in preset
    
        def test_notification_settings_structure(self, config_manager):
            """Test that notification settings have correct structure"""
            config = config_manager.generate_default()
            notifications = config['notifications']
            
            assert 'desktop' in notifications
            assert 'email' in notifications
            assert 'line' in notifications
            
            # Email settings
            email = notifications['email']
            assert 'enabled' in email
            assert 'smtp_server' in email
            assert 'smtp_port' in email
            assert 'use_tls' in email
            assert 'from_address' in email
            assert 'to_address' in email
else:
    # Dummy class when pytest is not available
    class TestConfigManager:
        pass


def run_manual_tests():
    """Run manual tests without pytest"""
    print("=== Running Manual Configuration Manager Tests ===\n")
    
    # Create temporary directory
    temp_dir = pathlib.Path(tempfile.mkdtemp())
    config_path = temp_dir / "test_config.json"
    
    try:
        config_mgr = ConfigManager(config_path)
        
        # Test 1: Generate default
        print("Test 1: Generate default configuration")
        config = config_mgr.generate_default()
        assert config['version'] == '2.0'
        print("✓ Passed")
        
        # Test 2: Validate
        print("\nTest 2: Validate configuration")
        is_valid, error = config_mgr.validate(config)
        assert is_valid is True
        print("✓ Passed")
        
        # Test 3: Save and load
        print("\nTest 3: Save and load configuration")
        config_mgr.save()
        loaded = config_mgr.load()
        assert loaded == config
        print("✓ Passed")
        
        # Test 4: Get/Set
        print("\nTest 4: Get and set values")
        config_mgr.set('ai.llm_model', 'test_model')
        assert config_mgr.get('ai.llm_model') == 'test_model'
        print("✓ Passed")
        
        # Test 5: Update
        print("\nTest 5: Update configuration")
        config_mgr.update({'processing': {'max_concurrent_jobs': 7}})
        assert config_mgr.get('processing.max_concurrent_jobs') == 7
        print("✓ Passed")
        
        # Test 6: Export/Import
        print("\nTest 6: Export and import")
        export_path = temp_dir / "export.json"
        config_mgr.export_to_file(export_path)
        assert export_path.exists()
        
        import_path = temp_dir / "import.json"
        with open(import_path, 'w', encoding='utf-8') as f:
            json.dump(config_mgr.generate_default(), f)
        config_mgr.import_from_file(import_path)
        print("✓ Passed")
        
        # Test 7: Invalid config
        print("\nTest 7: Validate invalid configuration")
        invalid = {"version": "2.0"}
        is_valid, error = config_mgr.validate(invalid)
        assert is_valid is False
        print("✓ Passed")
        
        print("\n=== All manual tests passed! ===")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    # Run manual tests if pytest is not available
    if PYTEST_AVAILABLE:
        print("Running tests with pytest...")
        pytest.main([__file__, '-v'])
    else:
        print("pytest not available, running manual tests...")
        run_manual_tests()
