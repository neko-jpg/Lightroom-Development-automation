# Preset Management System - Integration Checklist

This checklist helps you integrate the Preset Management System into your Junmai AutoDev workflow.

## ✅ Pre-Integration Verification

- [x] Database models exist (`models/database.py`)
- [x] Preset table created in database
- [x] PresetManager implementation complete (`preset_manager.py`)
- [x] Tests pass (`validate_preset_manager.py`)
- [x] Documentation available

## 📋 Integration Steps

### Step 1: Database Setup

- [ ] Ensure database is initialized with `init_db()`
- [ ] Verify Preset table exists
- [ ] Run Alembic migrations if needed
- [ ] Create default presets (optional)

**Commands**:
```python
from models.database import init_db
init_db('sqlite:///data/junmai.db')
```

### Step 2: Create Initial Presets

- [ ] Define preset configurations
- [ ] Create presets with context tags
- [ ] Test preset retrieval
- [ ] Export presets for backup

**Example**:
```python
from models.database import get_session
from preset_manager import PresetManager

db = get_session()
manager = PresetManager(db, "config/presets")

# Create your first preset
config = {...}
preset = manager.create_preset(
    name="WhiteLayer_Transparency",
    version="v4",
    config_template=config,
    context_tags=["backlit_portrait"],
    blend_amount=60
)
```

### Step 3: Context Engine Integration

- [ ] Import PresetManager in context_engine.py
- [ ] Add preset selection after context determination
- [ ] Pass selected preset to job creation
- [ ] Test end-to-end flow

**Integration Point** (`context_engine.py`):
```python
from preset_manager import PresetManager

class ContextEngine:
    def __init__(self, db_session):
        self.preset_manager = PresetManager(db_session)
    
    def process_photo(self, photo):
        # Determine context
        context = self.determine_context(exif_data, ai_eval)
        
        # Select preset
        preset = self.preset_manager.select_preset_for_context(context)
        
        # Get config
        config = preset.get_config_template()
        
        return config, preset
```

### Step 4: Job Queue Integration

- [ ] Add preset_id to job creation
- [ ] Store selected preset in photo record
- [ ] Record usage after job completion
- [ ] Update approval rates

**Integration Point** (`job_queue.py` or similar):
```python
def create_job(photo_id, preset):
    # Create job with preset config
    job = Job(
        photo_id=photo_id,
        config_json=json.dumps(preset.get_config_template())
    )
    
    # Store preset reference in photo
    photo = db.query(Photo).get(photo_id)
    photo.selected_preset = preset.name
    
    db.commit()
    return job

def on_job_complete(job, approved):
    # Record preset usage
    photo = job.photo
    preset = preset_manager.get_preset_by_name(photo.selected_preset)
    
    if preset:
        preset_manager.record_preset_usage(
            preset.id,
            photo.id,
            approved
        )
```

### Step 5: API Endpoints

- [ ] Create REST API routes for presets
- [ ] Add authentication/authorization
- [ ] Test API endpoints
- [ ] Document API

**Example Routes** (`app.py`):
```python
from preset_manager import PresetManager

@app.route('/api/presets', methods=['GET'])
def list_presets():
    context = request.args.get('context')
    presets = preset_manager.list_presets(context_tag=context)
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'version': p.version,
        'context_tags': p.get_context_tags(),
        'blend_amount': p.blend_amount,
        'usage_count': p.usage_count,
        'avg_approval_rate': p.avg_approval_rate
    } for p in presets])

@app.route('/api/presets/<int:preset_id>', methods=['GET'])
def get_preset(preset_id):
    preset = preset_manager.get_preset(preset_id)
    if not preset:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': preset.id,
        'name': preset.name,
        'version': preset.version,
        'config_template': preset.get_config_template(),
        'context_tags': preset.get_context_tags(),
        'blend_amount': preset.blend_amount
    })

@app.route('/api/presets/<int:preset_id>/stats', methods=['GET'])
def get_preset_stats(preset_id):
    stats = preset_manager.get_preset_statistics(preset_id)
    return jsonify(stats)

@app.route('/api/presets', methods=['POST'])
def create_preset():
    data = request.json
    preset = preset_manager.create_preset(
        name=data['name'],
        version=data['version'],
        config_template=data['config_template'],
        context_tags=data.get('context_tags', []),
        blend_amount=data.get('blend_amount', 100)
    )
    return jsonify({'id': preset.id}), 201

@app.route('/api/presets/<int:preset_id>', methods=['PUT'])
def update_preset(preset_id):
    data = request.json
    preset = preset_manager.update_preset(preset_id, **data)
    return jsonify({'id': preset.id})

@app.route('/api/presets/<int:preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    success = preset_manager.delete_preset(preset_id)
    if success:
        return '', 204
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/presets/<int:preset_id>/export', methods=['GET'])
def export_preset(preset_id):
    file_path = preset_manager.export_preset(preset_id)
    return send_file(file_path, as_attachment=True)

@app.route('/api/presets/import', methods=['POST'])
def import_preset():
    file = request.files['file']
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    preset = preset_manager.import_preset(
        temp_path,
        overwrite=request.form.get('overwrite', 'false') == 'true'
    )
    
    os.remove(temp_path)
    return jsonify({'id': preset.id}), 201
```

### Step 6: GUI Integration

- [ ] Add preset management panel
- [ ] Create preset selection dropdown
- [ ] Add version comparison view
- [ ] Display statistics dashboard

**GUI Components Needed**:
1. Preset list view
2. Preset editor
3. Version comparison
4. Statistics charts
5. Import/Export dialogs

### Step 7: Testing

- [ ] Test preset creation
- [ ] Test context-based selection
- [ ] Test version management
- [ ] Test import/export
- [ ] Test usage tracking
- [ ] Test API endpoints
- [ ] Test GUI components

**Test Scenarios**:
1. Create preset → Select by context → Apply to photo
2. Create version → Compare versions → Select better version
3. Export presets → Delete → Import → Verify
4. Apply preset → Approve → Check statistics
5. Apply preset → Reject → Check statistics

### Step 8: Documentation

- [ ] Update system documentation
- [ ] Document preset creation process
- [ ] Document API endpoints
- [ ] Create user guide
- [ ] Add troubleshooting section

### Step 9: Deployment

- [ ] Create default presets
- [ ] Export preset backups
- [ ] Update configuration files
- [ ] Deploy to production
- [ ] Monitor usage

## 🔧 Configuration

### config.json Updates

Add preset configuration section:

```json
{
  "presets": {
    "directory": "config/presets",
    "auto_backup": true,
    "backup_interval_hours": 24,
    "default_preset": "default",
    "enable_learning": true
  }
}
```

### Environment Variables

```bash
PRESET_DIR=config/presets
PRESET_BACKUP_DIR=backups/presets
PRESET_AUTO_BACKUP=true
```

## 📊 Monitoring

### Metrics to Track

- [ ] Preset usage counts
- [ ] Approval rates per preset
- [ ] Context-to-preset mapping accuracy
- [ ] Version adoption rates
- [ ] Import/export frequency

### Logging

Add logging for:
- Preset creation/updates
- Context selection decisions
- Usage recording
- Import/export operations
- Errors and warnings

**Example**:
```python
import logging

logger = logging.getLogger('preset_manager')

# Log preset selection
logger.info(f"Selected preset '{preset.name}' for context '{context}'")

# Log usage recording
logger.info(f"Recorded usage: preset={preset.id}, photo={photo.id}, approved={approved}")
```

## 🐛 Troubleshooting

### Common Issues

1. **Preset not found for context**
   - Create preset with that context tag
   - Create default preset as fallback

2. **Import fails**
   - Check JSON format
   - Verify file permissions
   - Check for duplicate names

3. **Statistics not updating**
   - Verify usage recording is called
   - Check database transactions
   - Verify photo-preset linkage

4. **Version comparison fails**
   - Ensure both presets exist
   - Check config template format
   - Verify version strings

## ✅ Post-Integration Verification

- [ ] All tests pass
- [ ] API endpoints work
- [ ] GUI components functional
- [ ] Presets selectable by context
- [ ] Usage tracking works
- [ ] Statistics accurate
- [ ] Import/export works
- [ ] Version management works
- [ ] No performance issues
- [ ] Logging configured
- [ ] Monitoring in place
- [ ] Documentation complete

## 📚 Reference Documentation

- **Implementation**: `PRESET_MANAGEMENT_IMPLEMENTATION.md`
- **Quick Start**: `PRESET_QUICK_START.md`
- **Examples**: `example_preset_usage.py`
- **Tests**: `test_preset_manager.py`
- **Validation**: `validate_preset_manager.py`

## 🎯 Success Criteria

Integration is complete when:

1. ✅ Presets are automatically selected based on photo context
2. ✅ Usage is tracked and approval rates are calculated
3. ✅ Versions can be created and compared
4. ✅ Presets can be imported and exported
5. ✅ API endpoints are functional
6. ✅ GUI components are integrated
7. ✅ Statistics are displayed correctly
8. ✅ System performs well under load
9. ✅ All tests pass
10. ✅ Documentation is complete

## 🚀 Next Steps After Integration

1. **Create Production Presets**
   - Define presets for all common contexts
   - Test with real photos
   - Adjust based on results

2. **Monitor Performance**
   - Track approval rates
   - Identify underperforming presets
   - Create improved versions

3. **User Training**
   - Train users on preset management
   - Document best practices
   - Gather feedback

4. **Continuous Improvement**
   - Analyze usage patterns
   - Create new presets as needed
   - Deprecate unused presets

---

**Last Updated**: 2025-11-08  
**Status**: Ready for Integration
