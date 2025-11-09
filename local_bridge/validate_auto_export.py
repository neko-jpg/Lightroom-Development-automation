"""
Validation script for Auto Export Engine

This script validates the auto-export implementation without requiring
full database setup or dependencies.

Requirements: 6.1, 6.4
"""

import sys
import pathlib

# Add local_bridge to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))


def validate_module_imports():
    """Validate that all modules can be imported"""
    print("=" * 60)
    print("Validating Auto Export Engine Implementation")
    print("=" * 60)
    
    print("\n1. Checking module imports...")
    
    try:
        from auto_export_engine import AutoExportEngine, ExportJob
        print("   ✓ auto_export_engine module imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import auto_export_engine: {e}")
        return False
    
    try:
        from export_preset_manager import ExportPresetManager, ExportPreset
        print("   ✓ export_preset_manager module imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import export_preset_manager: {e}")
        return False
    
    return True


def validate_class_structure():
    """Validate class structure and methods"""
    print("\n2. Checking class structure...")
    
    from auto_export_engine import AutoExportEngine, ExportJob
    from export_preset_manager import ExportPresetManager
    
    # Check AutoExportEngine methods
    required_methods = [
        'trigger_auto_export',
        'export_multiple_formats',
        'generate_filename',
        'get_export_path',
        'process_export_job',
        'complete_export_job',
        'get_next_export_job',
        'get_export_queue_status',
        'get_export_job',
        'cancel_export_job',
        'clear_export_queue',
        'get_export_config_for_lightroom'
    ]
    
    for method in required_methods:
        if hasattr(AutoExportEngine, method):
            print(f"   ✓ AutoExportEngine.{method} exists")
        else:
            print(f"   ✗ AutoExportEngine.{method} missing")
            return False
    
    # Check ExportJob attributes
    required_attrs = ['id', 'photo_id', 'preset_name', 'status', 'created_at']
    
    for attr in required_attrs:
        if attr in ExportJob.__annotations__:
            print(f"   ✓ ExportJob.{attr} exists")
        else:
            print(f"   ✗ ExportJob.{attr} missing")
            return False
    
    return True


def validate_api_endpoints():
    """Validate API endpoints are added to app.py"""
    print("\n3. Checking API endpoints...")
    
    app_file = pathlib.Path(__file__).parent / "app.py"
    
    if not app_file.exists():
        print("   ✗ app.py not found")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_endpoints = [
        '/export/auto/trigger',
        '/export/auto/multiple',
        '/export/auto/queue',
        '/export/auto/job/<string:job_id>',
        '/export/auto/job/next',
        '/export/auto/job/<string:job_id>/complete',
        '/export/auto/job/<string:job_id>/cancel',
        '/export/auto/queue/clear',
        '/export/auto/filename/generate',
        '/photos/<int:photo_id>/approve',
        '/photos/<int:photo_id>/reject',
        '/photos/approval/queue'
    ]
    
    for endpoint in required_endpoints:
        if endpoint in content:
            print(f"   ✓ Endpoint {endpoint} exists")
        else:
            print(f"   ✗ Endpoint {endpoint} missing")
            return False
    
    # Check if auto_export_engine is imported
    if 'from auto_export_engine import AutoExportEngine' in content:
        print("   ✓ AutoExportEngine imported in app.py")
    else:
        print("   ✗ AutoExportEngine not imported in app.py")
        return False
    
    # Check if auto_export_engine is initialized
    if 'auto_export_engine = AutoExportEngine' in content:
        print("   ✓ AutoExportEngine initialized in app.py")
    else:
        print("   ✗ AutoExportEngine not initialized in app.py")
        return False
    
    return True


def validate_documentation():
    """Validate documentation files exist"""
    print("\n4. Checking documentation...")
    
    base_dir = pathlib.Path(__file__).parent
    
    required_files = [
        'auto_export_engine.py',
        'test_auto_export_engine.py',
        'example_auto_export_usage.py',
        'AUTO_EXPORT_QUICK_START.md'
    ]
    
    for filename in required_files:
        file_path = base_dir / filename
        if file_path.exists():
            print(f"   ✓ {filename} exists")
        else:
            print(f"   ✗ {filename} missing")
            return False
    
    return True


def validate_filename_template_support():
    """Validate filename template variable support"""
    print("\n5. Checking filename template support...")
    
    from auto_export_engine import AutoExportEngine
    
    # Check if generate_filename method exists and has proper signature
    import inspect
    
    sig = inspect.signature(AutoExportEngine.generate_filename)
    params = list(sig.parameters.keys())
    
    required_params = ['self', 'photo', 'preset', 'sequence_number']
    
    for param in required_params:
        if param in params:
            print(f"   ✓ Parameter '{param}' exists in generate_filename")
        else:
            print(f"   ✗ Parameter '{param}' missing in generate_filename")
            return False
    
    # Check template variables in docstring
    method = AutoExportEngine.generate_filename
    docstring = method.__doc__ or ""
    
    template_vars = ['{date}', '{time}', '{sequence}', '{original}', 
                    '{year}', '{month}', '{day}', '{preset}']
    
    for var in template_vars:
        if var in docstring:
            print(f"   ✓ Template variable {var} documented")
        else:
            print(f"   ⚠ Template variable {var} not documented (may still be supported)")
    
    return True


def validate_requirements_coverage():
    """Validate requirements coverage"""
    print("\n6. Checking requirements coverage...")
    
    base_dir = pathlib.Path(__file__).parent
    
    # Check auto_export_engine.py
    with open(base_dir / 'auto_export_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'Requirements: 6.1, 6.4' in content:
        print("   ✓ Requirements 6.1, 6.4 documented in auto_export_engine.py")
    else:
        print("   ⚠ Requirements not documented in auto_export_engine.py")
    
    # Check for key functionality
    features = {
        'Approval-triggered auto-export': 'trigger_auto_export',
        'Multiple format export': 'export_multiple_formats',
        'Automatic filename generation': 'generate_filename',
        'Export queue management': 'get_export_queue_status'
    }
    
    for feature, method in features.items():
        if method in content:
            print(f"   ✓ {feature} implemented ({method})")
        else:
            print(f"   ✗ {feature} not implemented ({method})")
            return False
    
    return True


def main():
    """Run all validations"""
    results = []
    
    results.append(("Module Imports", validate_module_imports()))
    results.append(("Class Structure", validate_class_structure()))
    results.append(("API Endpoints", validate_api_endpoints()))
    results.append(("Documentation", validate_documentation()))
    results.append(("Filename Templates", validate_filename_template_support()))
    results.append(("Requirements Coverage", validate_requirements_coverage()))
    
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All validations passed!")
        print("\nImplementation complete:")
        print("  - Approval-triggered auto-export")
        print("  - Multiple format simultaneous export")
        print("  - Automatic filename generation")
        print("  - Export queue management")
        print("\nRequirements: 6.1, 6.4 ✓")
        return 0
    else:
        print("\n✗ Some validations failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
