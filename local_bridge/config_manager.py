"""
Configuration Management System for Junmai AutoDev

This module provides comprehensive configuration management including:
- config.json schema definition
- Configuration file loading and saving
- Configuration validation
- Default configuration generation

Requirements: 8.2, 8.3, 8.4, 8.5
"""

import json
import pathlib
import logging
from typing import Dict, Any, Optional, Tuple
from copy import deepcopy
import jsonschema

logger = logging.getLogger(__name__)


# Configuration Schema Definition
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {
            "type": "string",
            "const": "2.0",
            "description": "Configuration version"
        },
        "system": {
            "type": "object",
            "properties": {
                "hot_folders": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of folders to monitor for new photos"
                },
                "lightroom_catalog": {
                    "type": "string",
                    "description": "Path to Lightroom catalog file"
                },
                "temp_folder": {
                    "type": "string",
                    "description": "Temporary folder for processing"
                },
                "log_level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    "description": "Logging level"
                }
            },
            "required": ["hot_folders", "lightroom_catalog", "temp_folder", "log_level"]
        },
        "ai": {
            "type": "object",
            "properties": {
                "llm_provider": {
                    "type": "string",
                    "enum": ["ollama", "lm_studio", "llama_cpp"],
                    "description": "LLM provider"
                },
                "llm_model": {
                    "type": "string",
                    "description": "LLM model name"
                },
                "ollama_host": {
                    "type": "string",
                    "description": "Ollama server host URL"
                },
                "gpu_memory_limit_mb": {
                    "type": "integer",
                    "minimum": 1024,
                    "maximum": 24576,
                    "description": "GPU memory limit in MB"
                },
                "enable_quantization": {
                    "type": "boolean",
                    "description": "Enable model quantization (4bit/8bit)"
                },
                "selection_threshold": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 5.0,
                    "description": "Minimum AI score for auto-selection"
                }
            },
            "required": ["llm_provider", "llm_model", "ollama_host", "gpu_memory_limit_mb", 
                        "enable_quantization", "selection_threshold"]
        },
        "processing": {
            "type": "object",
            "properties": {
                "auto_import": {
                    "type": "boolean",
                    "description": "Automatically import detected photos"
                },
                "auto_select": {
                    "type": "boolean",
                    "description": "Automatically select photos based on AI evaluation"
                },
                "auto_develop": {
                    "type": "boolean",
                    "description": "Automatically develop selected photos"
                },
                "auto_export": {
                    "type": "boolean",
                    "description": "Automatically export developed photos"
                },
                "max_concurrent_jobs": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Maximum number of concurrent processing jobs"
                },
                "cpu_limit_percent": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "description": "CPU usage limit percentage"
                },
                "gpu_temp_limit_celsius": {
                    "type": "integer",
                    "minimum": 60,
                    "maximum": 90,
                    "description": "GPU temperature limit in Celsius"
                }
            },
            "required": ["auto_import", "auto_select", "auto_develop", "auto_export",
                        "max_concurrent_jobs", "cpu_limit_percent", "gpu_temp_limit_celsius"]
        },
        "export": {
            "type": "object",
            "properties": {
                "presets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "enabled": {"type": "boolean"},
                            "format": {
                                "type": "string",
                                "enum": ["JPEG", "PNG", "TIFF", "DNG"]
                            },
                            "quality": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100
                            },
                            "max_dimension": {
                                "type": "integer",
                                "minimum": 512,
                                "maximum": 8192
                            },
                            "color_space": {
                                "type": "string",
                                "enum": ["sRGB", "AdobeRGB", "ProPhotoRGB"]
                            },
                            "destination": {"type": "string"}
                        },
                        "required": ["name", "enabled", "format", "quality", 
                                    "max_dimension", "color_space", "destination"]
                    }
                },
                "cloud_sync": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "provider": {
                            "type": "string",
                            "enum": ["dropbox", "google_drive", "onedrive", "none"]
                        },
                        "remote_path": {"type": "string"}
                    },
                    "required": ["enabled", "provider", "remote_path"]
                }
            },
            "required": ["presets", "cloud_sync"]
        },
        "notifications": {
            "type": "object",
            "properties": {
                "desktop": {
                    "type": "boolean",
                    "description": "Enable desktop notifications"
                },
                "email": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "smtp_server": {"type": "string"},
                        "smtp_port": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 65535
                        },
                        "use_tls": {"type": "boolean"},
                        "from_address": {"type": "string"},
                        "to_address": {"type": "string"}
                    },
                    "required": ["enabled", "smtp_server", "smtp_port", "use_tls",
                                "from_address", "to_address"]
                },
                "line": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "token": {"type": "string"}
                    },
                    "required": ["enabled", "token"]
                }
            },
            "required": ["desktop", "email", "line"]
        },
        "ui": {
            "type": "object",
            "properties": {
                "theme": {
                    "type": "string",
                    "enum": ["light", "dark", "auto"]
                },
                "language": {
                    "type": "string",
                    "enum": ["ja", "en"]
                },
                "show_advanced_settings": {"type": "boolean"}
            },
            "required": ["theme", "language", "show_advanced_settings"]
        }
    },
    "required": ["version", "system", "ai", "processing", "export", "notifications", "ui"]
}


# Default Configuration
DEFAULT_CONFIG = {
    "version": "2.0",
    "system": {
        "hot_folders": [],
        "lightroom_catalog": "",
        "temp_folder": "C:/Temp/JunmaiAutoDev",
        "log_level": "INFO"
    },
    "ai": {
        "llm_provider": "ollama",
        "llm_model": "llama3.1:8b-instruct",
        "ollama_host": "http://localhost:11434",
        "gpu_memory_limit_mb": 6144,
        "enable_quantization": False,
        "selection_threshold": 3.5
    },
    "processing": {
        "auto_import": True,
        "auto_select": True,
        "auto_develop": True,
        "auto_export": False,
        "max_concurrent_jobs": 3,
        "cpu_limit_percent": 80,
        "gpu_temp_limit_celsius": 75
    },
    "export": {
        "presets": [
            {
                "name": "SNS",
                "enabled": True,
                "format": "JPEG",
                "quality": 85,
                "max_dimension": 2048,
                "color_space": "sRGB",
                "destination": "D:/Export/SNS"
            },
            {
                "name": "Print",
                "enabled": False,
                "format": "JPEG",
                "quality": 95,
                "max_dimension": 4096,
                "color_space": "AdobeRGB",
                "destination": "D:/Export/Print"
            },
            {
                "name": "Archive",
                "enabled": False,
                "format": "TIFF",
                "quality": 100,
                "max_dimension": 8192,
                "color_space": "ProPhotoRGB",
                "destination": "D:/Export/Archive"
            }
        ],
        "cloud_sync": {
            "enabled": False,
            "provider": "none",
            "remote_path": "/Photos/Processed"
        }
    },
    "notifications": {
        "desktop": True,
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "from_address": "",
            "to_address": ""
        },
        "line": {
            "enabled": False,
            "token": ""
        }
    },
    "ui": {
        "theme": "dark",
        "language": "ja",
        "show_advanced_settings": False
    }
}


class ConfigManager:
    """
    Configuration Manager for Junmai AutoDev System
    
    Handles loading, saving, validation, and default configuration generation.
    """
    
    def __init__(self, config_path: Optional[pathlib.Path] = None):
        """
        Initialize ConfigManager
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path is None:
            base_dir = pathlib.Path(__file__).parent
            config_path = base_dir / "config" / "config.json"
        
        self.config_path = pathlib.Path(config_path)
        self.config: Dict[str, Any] = {}
        self._ensure_config_directory()
    
    def _ensure_config_directory(self) -> None:
        """Ensure configuration directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            jsonschema.ValidationError: If config doesn't match schema
        """
        if not self.config_path.exists():
            logger.warning(f"Configuration file not found: {self.config_path}")
            logger.info("Generating default configuration...")
            self.config = self.generate_default()
            self.save()
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            logger.info(f"Configuration loaded from: {self.config_path}")
            
            # Validate loaded configuration
            is_valid, error_msg = self.validate(self.config)
            if not is_valid:
                logger.error(f"Configuration validation failed: {error_msg}")
                raise jsonschema.ValidationError(error_msg)
            
            return self.config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save configuration to file
        
        Args:
            config: Configuration dictionary to save. If None, saves current config.
            
        Raises:
            jsonschema.ValidationError: If config doesn't match schema
            IOError: If file cannot be written
        """
        if config is not None:
            self.config = config
        
        # Validate before saving
        is_valid, error_msg = self.validate(self.config)
        if not is_valid:
            logger.error(f"Cannot save invalid configuration: {error_msg}")
            raise jsonschema.ValidationError(error_msg)
        
        try:
            self._ensure_config_directory()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Configuration saved to: {self.config_path}")
            
        except IOError as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate configuration against schema
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            jsonschema.validate(instance=config, schema=CONFIG_SCHEMA)
            logger.debug("Configuration validation successful")
            return True, None
            
        except jsonschema.exceptions.ValidationError as e:
            error_path = '.'.join(map(str, e.path)) if e.path else 'root'
            error_message = f"Validation failed at '{error_path}': {e.message}"
            logger.error(error_message)
            return False, error_message
            
        except Exception as e:
            error_message = f"Validation error: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def generate_default(self) -> Dict[str, Any]:
        """
        Generate default configuration
        
        Returns:
            Default configuration dictionary
        """
        logger.info("Generating default configuration")
        self.config = deepcopy(DEFAULT_CONFIG)
        return self.config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key path
        
        Args:
            key_path: Dot-separated path (e.g., 'system.log_level')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config_manager.get('ai.llm_model')
            'llama3.1:8b-instruct'
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Configuration key not found: {key_path}, using default: {default}")
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value by dot-separated key path
        
        Args:
            key_path: Dot-separated path (e.g., 'system.log_level')
            value: Value to set
            
        Example:
            >>> config_manager.set('ai.llm_model', 'llama3.1:11b')
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        logger.debug(f"Configuration updated: {key_path} = {value}")
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with partial updates
        
        Args:
            updates: Dictionary of updates to apply
            
        Example:
            >>> config_manager.update({'ai': {'llm_model': 'llama3.1:11b'}})
        """
        def deep_update(base: Dict, updates: Dict) -> Dict:
            """Recursively update nested dictionaries"""
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    base[key] = deep_update(base[key], value)
                else:
                    base[key] = value
            return base
        
        self.config = deep_update(self.config, updates)
        logger.info("Configuration updated with partial changes")
    
    def reset_to_default(self) -> Dict[str, Any]:
        """
        Reset configuration to default values
        
        Returns:
            Default configuration dictionary
        """
        logger.warning("Resetting configuration to default values")
        self.config = self.generate_default()
        return self.config
    
    def export_to_file(self, export_path: pathlib.Path) -> None:
        """
        Export current configuration to a different file
        
        Args:
            export_path: Path to export configuration to
        """
        export_path = pathlib.Path(export_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Configuration exported to: {export_path}")
            
        except IOError as e:
            logger.error(f"Failed to export configuration: {e}")
            raise
    
    def import_from_file(self, import_path: pathlib.Path) -> Dict[str, Any]:
        """
        Import configuration from a different file
        
        Args:
            import_path: Path to import configuration from
            
        Returns:
            Imported configuration dictionary
            
        Raises:
            FileNotFoundError: If import file doesn't exist
            jsonschema.ValidationError: If imported config is invalid
        """
        import_path = pathlib.Path(import_path)
        
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")
        
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate imported configuration
            is_valid, error_msg = self.validate(imported_config)
            if not is_valid:
                raise jsonschema.ValidationError(f"Invalid configuration: {error_msg}")
            
            self.config = imported_config
            logger.info(f"Configuration imported from: {import_path}")
            
            return self.config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in import file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise


# Convenience function for quick access
def get_config_manager(config_path: Optional[pathlib.Path] = None) -> ConfigManager:
    """
    Get a ConfigManager instance
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_path)


if __name__ == '__main__':
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test configuration manager
    print("=== Testing Configuration Manager ===\n")
    
    # Test 1: Generate default configuration
    print("Test 1: Generate default configuration")
    config_mgr = ConfigManager(pathlib.Path("test_config.json"))
    default_config = config_mgr.generate_default()
    print(f"✓ Default configuration generated with version: {default_config['version']}")
    
    # Test 2: Validate configuration
    print("\nTest 2: Validate configuration")
    is_valid, error = config_mgr.validate(default_config)
    print(f"✓ Validation result: {is_valid}, Error: {error}")
    
    # Test 3: Save configuration
    print("\nTest 3: Save configuration")
    config_mgr.save()
    print(f"✓ Configuration saved to: {config_mgr.config_path}")
    
    # Test 4: Load configuration
    print("\nTest 4: Load configuration")
    loaded_config = config_mgr.load()
    print(f"✓ Configuration loaded, version: {loaded_config['version']}")
    
    # Test 5: Get configuration value
    print("\nTest 5: Get configuration value")
    llm_model = config_mgr.get('ai.llm_model')
    print(f"✓ LLM Model: {llm_model}")
    
    # Test 6: Set configuration value
    print("\nTest 6: Set configuration value")
    config_mgr.set('ai.llm_model', 'llama3.1:11b')
    new_model = config_mgr.get('ai.llm_model')
    print(f"✓ Updated LLM Model: {new_model}")
    
    # Test 7: Update configuration
    print("\nTest 7: Update configuration")
    config_mgr.update({
        'processing': {
            'max_concurrent_jobs': 5
        }
    })
    jobs = config_mgr.get('processing.max_concurrent_jobs')
    print(f"✓ Updated max concurrent jobs: {jobs}")
    
    # Test 8: Invalid configuration
    print("\nTest 8: Validate invalid configuration")
    invalid_config = {"version": "2.0"}  # Missing required fields
    is_valid, error = config_mgr.validate(invalid_config)
    print(f"✓ Invalid config detected: {not is_valid}, Error: {error[:50]}...")
    
    # Cleanup
    import os
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
        print("\n✓ Test file cleaned up")
    
    print("\n=== All tests passed! ===")
