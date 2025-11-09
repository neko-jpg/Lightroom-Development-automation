"""
Example usage of Multi-Model Management System.

Demonstrates:
- Listing available models
- Switching models
- Downloading models
- Getting model recommendations
- Tracking model statistics

Requirements: 18.1, 18.2, 18.3, 18.4
"""

import logging
from model_manager import ModelManager, ModelPurpose

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_list_models():
    """Example: List available models."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: List Available Models")
    print("=" * 60)
    
    manager = ModelManager()
    
    # List all models
    print("\nAll models:")
    models = manager.list_available_models()
    for model in models:
        status = "✓" if model.installed else "✗"
        print(f"  {status} {model.name} ({model.size}) - {model.purpose.value}")
    
    # List only installed models
    print("\nInstalled models:")
    installed = manager.list_available_models(installed_only=True)
    for model in installed:
        print(f"  ✓ {model.name}")
    
    # List models by purpose
    print("\nSpeed-focused models:")
    speed_models = manager.list_available_models(purpose=ModelPurpose.SPEED)
    for model in speed_models:
        print(f"  {model.name} - {model.description}")
    
    # List models that fit in 8GB VRAM
    print("\nModels for 8GB VRAM:")
    vram_models = manager.list_available_models(max_vram_gb=8.0)
    for model in vram_models:
        print(f"  {model.name} - Min VRAM: {model.min_vram_gb}GB")


def example_model_info():
    """Example: Get model information."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Get Model Information")
    print("=" * 60)
    
    manager = ModelManager()
    
    model_name = "llama3.1:8b-instruct"
    info = manager.get_model_info(model_name)
    
    if info:
        print(f"\nModel: {info.name}")
        print(f"  Size: {info.size}")
        print(f"  Purpose: {info.purpose.value}")
        print(f"  Description: {info.description}")
        print(f"  Recommended Use: {info.recommended_use}")
        print(f"  Min VRAM: {info.min_vram_gb}GB")
        print(f"  Quantization Support: {', '.join(info.quantization_support)}")
        print(f"  Download Size: {info.download_size_mb}MB")
        print(f"  Installed: {info.installed}")
        
        if info.usage_count > 0:
            print(f"  Usage Count: {info.usage_count}")
            if info.avg_inference_time:
                print(f"  Avg Inference Time: {info.avg_inference_time:.2f}s")
            if info.success_rate:
                print(f"  Success Rate: {info.success_rate*100:.1f}%")


def example_switch_model():
    """Example: Switch models."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Switch Models")
    print("=" * 60)
    
    manager = ModelManager()
    
    # Get current model
    current = manager.get_current_model()
    print(f"\nCurrent model: {current}")
    
    # Switch to a different model (if installed)
    installed = manager.list_installed_models()
    if len(installed) > 1:
        new_model = installed[1] if installed[0] == current else installed[0]
        
        print(f"\nSwitching to: {new_model}")
        success = manager.switch_model(new_model)
        
        if success:
            print(f"✓ Successfully switched to: {new_model}")
            print(f"  Current model is now: {manager.get_current_model()}")
        else:
            print(f"✗ Failed to switch to: {new_model}")
    else:
        print("\nOnly one model installed, cannot demonstrate switching")


def example_download_model():
    """Example: Download a model."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Download Model")
    print("=" * 60)
    
    manager = ModelManager()
    
    # Check which models are not installed
    all_models = manager.list_available_models()
    not_installed = [m for m in all_models if not m.installed]
    
    if not_installed:
        model_to_download = not_installed[0].name
        
        print(f"\nModel to download: {model_to_download}")
        print("Note: This is a demonstration. Actual download would take time.")
        print("In production, use progress callback for status updates.")
        
        # Uncomment to actually download:
        # def progress_callback(data):
        #     status = data.get('status', '')
        #     if 'completed' in data and 'total' in data:
        #         percent = (data['completed'] / data['total'] * 100)
        #         print(f"  Progress: {percent:.1f}%")
        #     else:
        #         print(f"  Status: {status}")
        #
        # success, message = manager.download_model(
        #     model_to_download,
        #     progress_callback=progress_callback
        # )
        #
        # if success:
        #     print(f"✓ {message}")
        # else:
        #     print(f"✗ {message}")
    else:
        print("\nAll models are already installed")


def example_recommend_model():
    """Example: Get model recommendations."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Model Recommendations")
    print("=" * 60)
    
    manager = ModelManager()
    
    # Recommend for different scenarios
    scenarios = [
        (8.0, "speed", "Fast processing on RTX 4060"),
        (8.0, "balanced", "Balanced performance on RTX 4060"),
        (8.0, "quality", "Best quality on RTX 4060"),
        (4.0, "balanced", "Limited VRAM (4GB)"),
        (16.0, "quality", "High-end GPU (16GB)"),
    ]
    
    for vram, priority, description in scenarios:
        recommended = manager.recommend_model(vram, priority)
        print(f"\n{description}:")
        print(f"  VRAM: {vram}GB, Priority: {priority}")
        print(f"  Recommended: {recommended}")


def example_check_compatibility():
    """Example: Check model compatibility."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Check Model Compatibility")
    print("=" * 60)
    
    manager = ModelManager()
    
    # Check compatibility for different models
    models_to_check = [
        "llama3.2:1b-instruct",
        "llama3.1:8b-instruct",
        "llama3.1:70b-instruct"
    ]
    
    available_vram = 8.0
    
    print(f"\nAvailable VRAM: {available_vram}GB\n")
    
    for model_name in models_to_check:
        compatible, message = manager.check_model_compatibility(model_name, available_vram)
        status = "✓" if compatible else "✗"
        print(f"{status} {model_name}")
        print(f"  {message}")


def example_track_usage():
    """Example: Track model usage."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Track Model Usage")
    print("=" * 60)
    
    manager = ModelManager()
    
    # Simulate some usage
    model_name = "llama3.1:8b-instruct"
    
    print(f"\nSimulating usage for: {model_name}")
    
    # Record some successful inferences
    for i in range(5):
        inference_time = 2.5 + (i * 0.1)  # Simulated times
        manager.record_usage(model_name, inference_time, success=True)
        print(f"  Inference {i+1}: {inference_time:.2f}s - Success")
    
    # Record a failure
    manager.record_usage(model_name, 0.0, success=False)
    print(f"  Inference 6: Failed")
    
    # Get statistics
    stats = manager.get_model_statistics(model_name)
    
    print(f"\nStatistics for {model_name}:")
    print(f"  Usage Count: {stats['usage_count']}")
    print(f"  Avg Inference Time: {stats['avg_inference_time']:.2f}s")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"  Last Used: {stats['last_used']}")


def example_all_statistics():
    """Example: Get all model statistics."""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: All Model Statistics")
    print("=" * 60)
    
    manager = ModelManager()
    
    stats = manager.get_all_statistics()
    
    print("\nModel Statistics:")
    for model_name, stat in stats.items():
        if stat['usage_count'] > 0:
            print(f"\n{model_name}:")
            print(f"  Usage Count: {stat['usage_count']}")
            if stat['avg_inference_time']:
                print(f"  Avg Time: {stat['avg_inference_time']:.2f}s")
            if stat['success_rate']:
                print(f"  Success Rate: {stat['success_rate']*100:.1f}%")
            print(f"  Last Used: {stat['last_used']}")


def example_export_import():
    """Example: Export and import metadata."""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Export/Import Metadata")
    print("=" * 60)
    
    manager = ModelManager()
    
    # Export metadata
    export_file = "data/model_metadata_backup.json"
    print(f"\nExporting metadata to: {export_file}")
    manager.export_metadata(export_file)
    print("✓ Metadata exported")
    
    # Import metadata (in practice, this would be from a different file)
    print(f"\nImporting metadata from: {export_file}")
    manager.import_metadata(export_file)
    print("✓ Metadata imported")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MULTI-MODEL MANAGEMENT SYSTEM - EXAMPLE USAGE")
    print("=" * 70)
    
    try:
        example_list_models()
        example_model_info()
        example_switch_model()
        # example_download_model()  # Commented out to avoid actual download
        example_recommend_model()
        example_check_compatibility()
        example_track_usage()
        example_all_statistics()
        example_export_import()
        
        print("\n" + "=" * 70)
        print("ALL EXAMPLES COMPLETED")
        print("=" * 70)
    
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == '__main__':
    main()
