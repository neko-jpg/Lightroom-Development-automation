# Configuration Management

This directory contains configuration files for the Junmai AutoDev system.

## Files

- `config.json` - Main system configuration file
- `presets/` - Directory for Lightroom preset files
- `context_rules.json` - Context recognition rules (future implementation)

## Configuration Structure

The `config.json` file follows the schema defined in `config_manager.py` and includes:

### System Settings
- Hot folder paths for automatic photo monitoring
- Lightroom catalog location
- Temporary folder for processing
- Logging level

### AI Settings
- LLM provider and model configuration
- Ollama host URL
- GPU memory limits
- Model quantization options
- AI selection threshold

### Processing Settings
- Auto-import, auto-select, auto-develop, auto-export flags
- Maximum concurrent jobs
- CPU and GPU resource limits

### Export Settings
- Multiple export presets (SNS, Print, Archive)
- Format, quality, dimensions, color space
- Cloud sync configuration (Dropbox, Google Drive, OneDrive)

### Notification Settings
- Desktop notifications
- Email notifications (SMTP configuration)
- LINE Notify integration

### UI Settings
- Theme (light/dark/auto)
- Language (ja/en)
- Advanced settings visibility

## Usage

### Python API

```python
from config_manager import ConfigManager

# Initialize configuration manager
config_mgr = ConfigManager()

# Load configuration
config = config_mgr.load()

# Get specific value
llm_model = config_mgr.get('ai.llm_model')

# Update value
config_mgr.set('ai.llm_model', 'llama3.1:11b')

# Save changes
config_mgr.save()

# Reset to defaults
config_mgr.reset_to_default()
```

### Command Line Testing

```bash
cd local_bridge
python config_manager.py
```

## Default Configuration

When no configuration file exists, the system automatically generates a default configuration with sensible defaults:

- LLM: Ollama with Llama 3.1 8B
- GPU Memory: 6GB limit
- Processing: Auto-import and auto-select enabled
- Export: Disabled by default
- Notifications: Desktop only

## Validation

All configuration changes are validated against the JSON schema before saving. Invalid configurations will be rejected with detailed error messages.

## Requirements

This configuration system implements requirements:
- 8.2: Configuration file reading and saving
- 8.3: Configuration validation
- 8.4: Default configuration generation
- 8.5: Configuration schema definition
