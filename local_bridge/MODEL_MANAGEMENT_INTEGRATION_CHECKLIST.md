# Multi-Model Management - Integration Checklist

## Prerequisites

- ✅ Task 43 completed
- ✅ All tests passing (32/32)
- ✅ Documentation complete
- ✅ Example code provided

## Integration Steps

### 1. Update Flask Application

Add model management API to main Flask app:

```python
# In local_bridge/app.py

from api_model_management import model_bp, init_model_api
from model_manager import ModelManager

# Initialize model manager
model_manager = ModelManager()

# Initialize API
init_model_api(model_manager)

# Register blueprint
app.register_blueprint(model_bp)
```

### 2. Update OllamaClient Integration

Modify OllamaClient to use ModelManager:

```python
# In local_bridge/ollama_client.py or usage code

from model_manager import ModelManager

# Initialize manager
model_manager = ModelManager()

# Get current or recommended model
model = model_manager.get_current_model()

# Use with OllamaClient
client = OllamaClient()
response = client.generate(model, prompt)

# Track usage
manager.record_usage(model, inference_time, success=True)
```

### 3. Update AI Selector Integration

Integrate with AI Selector:

```python
# In local_bridge/ai_selector.py

from model_manager import ModelManager

class AISelector:
    def __init__(self, ...):
        self.model_manager = ModelManager()
        self.llm_model = self.model_manager.get_current_model()
        # ... rest of initialization
    
    def evaluate(self, image_path):
        # ... evaluation code
        
        # Track model usage
        self.model_manager.record_usage(
            self.llm_model,
            inference_time,
            success=True
        )
```

### 4. Update Configuration System

Add model settings to config.json:

```json
{
  "ai": {
    "llm_provider": "ollama",
    "llm_model": "llama3.1:8b-instruct",
    "ollama_host": "http://localhost:11434",
    "auto_select_model": true,
    "model_priority": "balanced"
  }
}
```

### 5. Add GUI Integration (PyQt6)

Create model management UI:

```python
# In gui_qt/widgets/model_widgets.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton
from model_manager import ModelManager

class ModelManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = ModelManager()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Model list
        self.model_list = QListWidget()
        self.refresh_models()
        layout.addWidget(self.model_list)
        
        # Buttons
        self.switch_btn = QPushButton("Switch Model")
        self.switch_btn.clicked.connect(self.switch_model)
        layout.addWidget(self.switch_btn)
        
        self.setLayout(layout)
    
    def refresh_models(self):
        self.model_list.clear()
        models = self.manager.list_available_models()
        for model in models:
            status = "✓" if model.installed else "✗"
            self.model_list.addItem(f"{status} {model.name}")
```

### 6. Add Mobile Web Integration

Create model management page:

```javascript
// In mobile_web/src/pages/ModelManagement.js

import React, { useState, useEffect } from 'react';
import api from '../services/api';

function ModelManagement() {
  const [models, setModels] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);
  
  useEffect(() => {
    loadModels();
    loadCurrentModel();
  }, []);
  
  const loadModels = async () => {
    const response = await api.get('/api/model/list');
    setModels(response.data.models);
  };
  
  const loadCurrentModel = async () => {
    const response = await api.get('/api/model/current');
    setCurrentModel(response.data.model);
  };
  
  const switchModel = async (modelName) => {
    await api.post('/api/model/switch', { model: modelName });
    loadCurrentModel();
  };
  
  return (
    <div>
      <h2>Model Management</h2>
      <p>Current: {currentModel}</p>
      <ul>
        {models.map(model => (
          <li key={model.name}>
            {model.name} - {model.purpose}
            {model.installed && (
              <button onClick={() => switchModel(model.name)}>
                Switch
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ModelManagement;
```

### 7. Update Settings UI

Add model settings to settings page:

```python
# In gui_qt/widgets/settings_widgets.py

class AISettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = ModelManager()
        
        # Model selection dropdown
        self.model_combo = QComboBox()
        models = self.manager.list_available_models(installed_only=True)
        for model in models:
            self.model_combo.addItem(model.name)
        
        # Priority selection
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["speed", "balanced", "quality"])
        
        # Auto-select checkbox
        self.auto_select = QCheckBox("Auto-select best model")
```

### 8. Add Startup Initialization

Initialize model manager on app startup:

```python
# In local_bridge/app.py or main.py

def initialize_app():
    # Initialize model manager
    model_manager = ModelManager()
    
    # Check if any models installed
    installed = model_manager.list_installed_models()
    
    if not installed:
        logger.warning("No models installed!")
        # Optionally download default model
        recommended = model_manager.recommend_model(8.0, "balanced")
        if recommended:
            logger.info(f"Downloading recommended model: {recommended}")
            model_manager.download_model(recommended)
    
    # Set current model if not set
    if not model_manager.get_current_model():
        if installed:
            model_manager.switch_model(installed[0])
    
    return model_manager
```

### 9. Add Monitoring and Logging

Track model performance:

```python
# In your processing code

import time
from model_manager import ModelManager

manager = ModelManager()

def process_with_tracking(func, *args, **kwargs):
    model = manager.get_current_model()
    start = time.time()
    
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        manager.record_usage(model, elapsed, success=True)
        return result
    except Exception as e:
        elapsed = time.time() - start
        manager.record_usage(model, elapsed, success=False)
        raise
```

### 10. Add Periodic Statistics Review

Create scheduled task for statistics:

```python
# In your scheduler or background task

def review_model_statistics():
    manager = ModelManager()
    stats = manager.get_all_statistics()
    
    # Log statistics
    for model_name, stat in stats.items():
        if stat['usage_count'] > 0:
            logger.info(
                f"Model {model_name}: "
                f"{stat['usage_count']} uses, "
                f"{stat['success_rate']*100:.1f}% success, "
                f"{stat['avg_inference_time']:.2f}s avg"
            )
    
    # Optionally recommend model switch
    current = manager.get_current_model()
    recommended = manager.recommend_model(8.0, "balanced")
    
    if recommended != current:
        logger.info(f"Consider switching from {current} to {recommended}")
```

## Testing Integration

### 1. Test Model Listing
```bash
curl http://localhost:5100/api/model/list
```

### 2. Test Model Switching
```bash
curl -X POST http://localhost:5100/api/model/switch \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b-instruct"}'
```

### 3. Test Recommendation
```bash
curl -X POST http://localhost:5100/api/model/recommend \
  -H "Content-Type: application/json" \
  -d '{"available_vram_gb": 8.0, "priority": "balanced"}'
```

### 4. Test Statistics
```bash
curl http://localhost:5100/api/model/statistics
```

## Verification Checklist

- [ ] Model manager initializes correctly
- [ ] Can list available models
- [ ] Can switch between installed models
- [ ] Can download new models
- [ ] Statistics are tracked correctly
- [ ] Recommendations work as expected
- [ ] API endpoints respond correctly
- [ ] GUI integration works
- [ ] Mobile web integration works
- [ ] Configuration is persisted
- [ ] Error handling works properly

## Common Issues and Solutions

### Issue 1: Ollama Not Running
**Solution**: Start Ollama service before using model manager

### Issue 2: No Models Installed
**Solution**: Download recommended model on first run

### Issue 3: Insufficient VRAM
**Solution**: Use compatibility check and recommend smaller model

### Issue 4: Model Switch Fails
**Solution**: Verify model is installed before switching

### Issue 5: Statistics Not Updating
**Solution**: Ensure record_usage is called after each inference

## Performance Considerations

1. **Metadata Persistence**: Saved automatically after each operation
2. **Sync Frequency**: Sync with Ollama on startup and periodically
3. **Statistics Storage**: Lightweight JSON storage
4. **API Response Time**: Fast for list/info, slower for download

## Security Considerations

1. **Metadata File**: Store in secure location with proper permissions
2. **API Access**: Add authentication if exposing publicly
3. **Model Downloads**: Validate model names before downloading
4. **Statistics**: Don't expose sensitive usage patterns

## Next Steps

1. Complete integration with Flask app
2. Add GUI components
3. Test with real Ollama instance
4. Monitor performance in production
5. Gather user feedback
6. Iterate on recommendation algorithm

## References

- [MODEL_MANAGEMENT_IMPLEMENTATION.md](MODEL_MANAGEMENT_IMPLEMENTATION.md)
- [MODEL_MANAGEMENT_QUICK_START.md](MODEL_MANAGEMENT_QUICK_START.md)
- [MODEL_MANAGEMENT_QUICK_REFERENCE.md](MODEL_MANAGEMENT_QUICK_REFERENCE.md)
- [TASK_43_COMPLETION_SUMMARY.md](TASK_43_COMPLETION_SUMMARY.md)
