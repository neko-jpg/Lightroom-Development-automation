"""
Quick verification script to test configuration manager integration
"""

import sys
import pathlib

# Add local_bridge to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from config_manager import ConfigManager

def verify_integration():
    """Verify configuration manager is working correctly"""
    print("=" * 60)
    print("Configuration Manager Integration Verification")
    print("=" * 60)
    
    # Test 1: Initialize
    print("\n1. Initializing ConfigManager...")
    config_mgr = ConfigManager(pathlib.Path("config/test_verify.json"))
    print("   ✓ ConfigManager initialized")
    
    # Test 2: Generate default
    print("\n2. Generating default configuration...")
    config = config_mgr.generate_default()
    print(f"   ✓ Default config generated (version: {config['version']})")
    
    # Test 3: Validate
    print("\n3. Validating configuration...")
    is_valid, error = config_mgr.validate(config)
    if is_valid:
        print("   ✓ Configuration is valid")
    else:
        print(f"   ✗ Validation failed: {error}")
        return False
    
    # Test 4: Check all sections
    print("\n4. Verifying configuration sections...")
    sections = ['system', 'ai', 'processing', 'export', 'notifications', 'ui']
    for section in sections:
        if section in config:
            print(f"   ✓ Section '{section}' present")
        else:
            print(f"   ✗ Section '{section}' missing")
            return False
    
    # Test 5: Check key settings
    print("\n5. Verifying key settings...")
    checks = [
        ('ai.llm_model', 'llama3.1:8b-instruct'),
        ('ai.gpu_memory_limit_mb', 6144),
        ('processing.max_concurrent_jobs', 3),
        ('processing.cpu_limit_percent', 80),
        ('ui.theme', 'dark'),
        ('ui.language', 'ja')
    ]
    
    for key_path, expected in checks:
        value = config_mgr.get(key_path)
        if value == expected:
            print(f"   ✓ {key_path} = {value}")
        else:
            print(f"   ✗ {key_path} = {value} (expected {expected})")
            return False
    
    # Test 6: Save and load
    print("\n6. Testing save and load...")
    config_mgr.save()
    print("   ✓ Configuration saved")
    
    loaded = config_mgr.load()
    print("   ✓ Configuration loaded")
    
    if loaded == config:
        print("   ✓ Loaded config matches saved config")
    else:
        print("   ✗ Loaded config differs from saved config")
        return False
    
    # Test 7: Update operation
    print("\n7. Testing update operation...")
    config_mgr.update({
        'processing': {
            'max_concurrent_jobs': 5
        }
    })
    
    if config_mgr.get('processing.max_concurrent_jobs') == 5:
        print("   ✓ Update operation successful")
    else:
        print("   ✗ Update operation failed")
        return False
    
    # Test 8: Export presets
    print("\n8. Verifying export presets...")
    presets = config_mgr.get('export.presets')
    preset_names = [p['name'] for p in presets]
    expected_presets = ['SNS', 'Print', 'Archive']
    
    for name in expected_presets:
        if name in preset_names:
            print(f"   ✓ Export preset '{name}' present")
        else:
            print(f"   ✗ Export preset '{name}' missing")
            return False
    
    # Cleanup
    import os
    if os.path.exists("config/test_verify.json"):
        os.remove("config/test_verify.json")
        print("\n9. Cleanup completed")
    
    print("\n" + "=" * 60)
    print("✅ All verification checks passed!")
    print("=" * 60)
    print("\nConfiguration Manager is ready for use.")
    print("\nKey Features:")
    print("  • Load/Save configuration with validation")
    print("  • Default configuration generation")
    print("  • Dot-notation key access (e.g., 'ai.llm_model')")
    print("  • Partial configuration updates")
    print("  • Import/Export functionality")
    print("  • Flask API integration")
    print("\nNext Steps:")
    print("  • Use ConfigManager in hot folder service")
    print("  • Use ConfigManager in AI selection engine")
    print("  • Use ConfigManager in job queue system")
    print("  • Use ConfigManager in GUI components")
    
    return True


if __name__ == '__main__':
    try:
        success = verify_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
