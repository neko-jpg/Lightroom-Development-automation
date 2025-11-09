"""
Example usage of model quantization features.

Demonstrates:
- Enabling/disabling quantization
- Switching between 4-bit and 8-bit quantization
- Performance comparison
- Integration with AI Selector

Requirements: 17.4
"""

import logging
from pathlib import Path
from ollama_client import OllamaClient
from ai_selector import AISelector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_quantization():
    """Example: Basic quantization usage."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Quantization Usage")
    print("=" * 60)
    
    # Create client without quantization
    client = OllamaClient()
    print(f"\n1. Default settings:")
    settings = client.get_quantization_settings()
    print(f"   Enabled: {settings['enabled']}")
    print(f"   Bits: {settings['bits']}")
    print(f"   Memory Reduction: {settings['memory_reduction']}")
    
    # Enable 8-bit quantization
    client.set_quantization(True, 8)
    print(f"\n2. After enabling 8-bit quantization:")
    settings = client.get_quantization_settings()
    print(f"   Enabled: {settings['enabled']}")
    print(f"   Bits: {settings['bits']}")
    print(f"   Memory Reduction: {settings['memory_reduction']}")
    
    # Switch to 4-bit quantization
    client.set_quantization(True, 4)
    print(f"\n3. After switching to 4-bit quantization:")
    settings = client.get_quantization_settings()
    print(f"   Enabled: {settings['enabled']}")
    print(f"   Bits: {settings['bits']}")
    print(f"   Memory Reduction: {settings['memory_reduction']}")
    
    # Disable quantization
    client.set_quantization(False)
    print(f"\n4. After disabling quantization:")
    settings = client.get_quantization_settings()
    print(f"   Enabled: {settings['enabled']}")
    print(f"   Bits: {settings['bits']}")
    print(f"   Memory Reduction: {settings['memory_reduction']}")


def example_model_name_transformation():
    """Example: Model name transformation with quantization."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Model Name Transformation")
    print("=" * 60)
    
    models = [
        "llama3.1:8b-instruct",
        "llama3.1:11b-instruct",
        "mixtral:8x7b",
        "llama3.1"
    ]
    
    client = OllamaClient()
    
    print("\nOriginal model names:")
    for model in models:
        print(f"  - {model}")
    
    # 8-bit quantization
    client.set_quantization(True, 8)
    print("\n8-bit quantized names:")
    for model in models:
        quantized = client._get_quantized_model_name(model)
        print(f"  - {model} → {quantized}")
    
    # 4-bit quantization
    client.set_quantization(True, 4)
    print("\n4-bit quantized names:")
    for model in models:
        quantized = client._get_quantized_model_name(model)
        print(f"  - {model} → {quantized}")


def example_performance_tracking():
    """Example: Performance tracking."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Performance Tracking")
    print("=" * 60)
    
    client = OllamaClient()
    
    # Simulate some performance data
    print("\nSimulating model usage...")
    client._record_performance("llama3.1:8b", 2.5, success=True)
    client._record_performance("llama3.1:8b", 2.3, success=True)
    client._record_performance("llama3.1:8b", 2.7, success=True)
    client._record_performance("llama3.1:8b", 0.0, success=False)
    
    client._record_performance("llama3.1:q4_8b", 1.8, success=True)
    client._record_performance("llama3.1:q4_8b", 1.9, success=True)
    client._record_performance("llama3.1:q4_8b", 1.7, success=True)
    
    # Get statistics
    print("\nPerformance Statistics:")
    
    stats_full = client.get_performance_stats("llama3.1:8b")
    print(f"\nllama3.1:8b (non-quantized):")
    print(f"  Total Calls: {stats_full['total_calls']}")
    print(f"  Successful: {stats_full['successful_calls']}")
    print(f"  Failed: {stats_full['failed_calls']}")
    print(f"  Avg Time: {stats_full['avg_time']:.2f}s")
    print(f"  Min Time: {stats_full['min_time']:.2f}s")
    print(f"  Max Time: {stats_full['max_time']:.2f}s")
    
    stats_quant = client.get_performance_stats("llama3.1:q4_8b")
    print(f"\nllama3.1:q4_8b (4-bit quantized):")
    print(f"  Total Calls: {stats_quant['total_calls']}")
    print(f"  Successful: {stats_quant['successful_calls']}")
    print(f"  Failed: {stats_quant['failed_calls']}")
    print(f"  Avg Time: {stats_quant['avg_time']:.2f}s")
    print(f"  Min Time: {stats_quant['min_time']:.2f}s")
    print(f"  Max Time: {stats_quant['max_time']:.2f}s")
    
    # Calculate speedup
    if stats_full['avg_time'] > 0:
        speedup = stats_full['avg_time'] / stats_quant['avg_time']
        print(f"\nSpeedup with 4-bit quantization: {speedup:.2f}x")


def example_ai_selector_integration():
    """Example: AI Selector with quantization."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: AI Selector Integration")
    print("=" * 60)
    
    # Create AI Selector with quantization enabled
    print("\n1. Creating AI Selector with 8-bit quantization...")
    selector = AISelector(
        enable_llm=True,
        enable_quantization=True,
        quantization_bits=8
    )
    
    settings = selector.get_quantization_settings()
    print(f"   Quantization enabled: {settings['enabled']}")
    print(f"   Quantization bits: {settings['bits']}")
    print(f"   Memory reduction: {settings['memory_reduction']}")
    
    # Switch to 4-bit quantization
    print("\n2. Switching to 4-bit quantization...")
    selector.set_quantization(True, 4)
    
    settings = selector.get_quantization_settings()
    print(f"   Quantization enabled: {settings['enabled']}")
    print(f"   Quantization bits: {settings['bits']}")
    print(f"   Memory reduction: {settings['memory_reduction']}")
    
    # Disable quantization
    print("\n3. Disabling quantization...")
    selector.set_quantization(False)
    
    settings = selector.get_quantization_settings()
    print(f"   Quantization enabled: {settings['enabled']}")
    print(f"   Quantization bits: {settings['bits']}")
    print(f"   Memory reduction: {settings['memory_reduction']}")


def example_list_models():
    """Example: List available models."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: List Available Models")
    print("=" * 60)
    
    client = OllamaClient()
    
    print("\nFetching available models from Ollama...")
    models = client.list_available_models()
    
    if models:
        print(f"\nFound {len(models)} models:")
        for model in models:
            name = model.get('name', 'Unknown')
            size = model.get('size', 0)
            size_gb = size / (1024**3) if size > 0 else 0
            print(f"  - {name} ({size_gb:.2f} GB)")
    else:
        print("\nNo models found or Ollama is not running.")
        print("Make sure Ollama is installed and running:")
        print("  1. Install Ollama from https://ollama.ai")
        print("  2. Run: ollama serve")
        print("  3. Pull a model: ollama pull llama3.1:8b-instruct")


def example_check_model():
    """Example: Check if specific models exist."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Check Model Availability")
    print("=" * 60)
    
    client = OllamaClient()
    
    models_to_check = [
        "llama3.1:8b-instruct",
        "llama3.1:q4_8b-instruct",
        "llama3.1:q8_8b-instruct",
        "mixtral:8x7b"
    ]
    
    print("\nChecking model availability:")
    for model in models_to_check:
        exists = client.check_model_exists(model)
        status = "✓ Available" if exists else "✗ Not found"
        print(f"  {model}: {status}")


def example_memory_usage_comparison():
    """Example: Compare memory usage between quantization levels."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Memory Usage Comparison")
    print("=" * 60)
    
    # Typical model sizes (approximate)
    base_model_size_gb = 8.0  # 8B model in full precision
    
    print(f"\nBase model size: {base_model_size_gb:.1f} GB")
    print("\nEstimated memory usage:")
    
    # Full precision (16-bit)
    print(f"  Full precision (16-bit): {base_model_size_gb:.1f} GB")
    
    # 8-bit quantization
    size_8bit = base_model_size_gb * 0.5
    print(f"  8-bit quantization: {size_8bit:.1f} GB (50% reduction)")
    
    # 4-bit quantization
    size_4bit = base_model_size_gb * 0.25
    print(f"  4-bit quantization: {size_4bit:.1f} GB (75% reduction)")
    
    print("\nRecommendations:")
    print("  - RTX 4060 (8GB VRAM): Use 4-bit or 8-bit quantization")
    print("  - RTX 4070 (12GB VRAM): Use 8-bit quantization or full precision")
    print("  - RTX 4090 (24GB VRAM): Use full precision for best quality")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("MODEL QUANTIZATION EXAMPLES")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_quantization()
        example_model_name_transformation()
        example_performance_tracking()
        example_ai_selector_integration()
        example_list_models()
        example_check_model()
        example_memory_usage_comparison()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("\nNote: Some examples require Ollama to be running.")
        print("Install and start Ollama: https://ollama.ai")


if __name__ == '__main__':
    main()
