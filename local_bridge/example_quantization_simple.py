"""
Simple example of model quantization features (no dependencies).

Demonstrates:
- Basic quantization usage
- Model name transformation
- Settings management
- Performance tracking

Requirements: 17.4
"""

import logging
from ollama_client import OllamaClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    """Run simple quantization examples."""
    print("\n" + "=" * 60)
    print("MODEL QUANTIZATION SIMPLE EXAMPLES")
    print("=" * 60)
    
    # Example 1: Basic usage
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Quantization Usage")
    print("=" * 60)
    
    client = OllamaClient()
    print("\n1. Default settings:")
    settings = client.get_quantization_settings()
    print(f"   Enabled: {settings['enabled']}")
    print(f"   Bits: {settings['bits']}")
    print(f"   Memory Reduction: {settings['memory_reduction']}")
    
    client.set_quantization(True, 8)
    print("\n2. After enabling 8-bit quantization:")
    settings = client.get_quantization_settings()
    print(f"   Enabled: {settings['enabled']}")
    print(f"   Bits: {settings['bits']}")
    print(f"   Memory Reduction: {settings['memory_reduction']}")
    
    client.set_quantization(True, 4)
    print("\n3. After switching to 4-bit quantization:")
    settings = client.get_quantization_settings()
    print(f"   Enabled: {settings['enabled']}")
    print(f"   Bits: {settings['bits']}")
    print(f"   Memory Reduction: {settings['memory_reduction']}")
    
    # Example 2: Model name transformation
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Model Name Transformation")
    print("=" * 60)
    
    models = [
        "llama3.1:8b-instruct",
        "llama3.1:11b-instruct",
        "mixtral:8x7b"
    ]
    
    print("\nOriginal → 8-bit → 4-bit:")
    for model in models:
        client.set_quantization(True, 8)
        q8 = client._get_quantized_model_name(model)
        client.set_quantization(True, 4)
        q4 = client._get_quantized_model_name(model)
        print(f"  {model}")
        print(f"    → {q8}")
        print(f"    → {q4}")
    
    # Example 3: Performance tracking
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Performance Tracking")
    print("=" * 60)
    
    client = OllamaClient()
    
    print("\nSimulating model usage...")
    client._record_performance("llama3.1:8b", 2.5, success=True)
    client._record_performance("llama3.1:8b", 2.3, success=True)
    client._record_performance("llama3.1:8b", 2.7, success=True)
    
    client._record_performance("llama3.1:q4_8b", 1.8, success=True)
    client._record_performance("llama3.1:q4_8b", 1.9, success=True)
    client._record_performance("llama3.1:q4_8b", 1.7, success=True)
    
    print("\nPerformance Statistics:")
    
    stats_full = client.get_performance_stats("llama3.1:8b")
    print(f"\nllama3.1:8b (non-quantized):")
    print(f"  Calls: {stats_full['total_calls']}")
    print(f"  Avg Time: {stats_full['avg_time']:.2f}s")
    print(f"  Min/Max: {stats_full['min_time']:.2f}s / {stats_full['max_time']:.2f}s")
    
    stats_quant = client.get_performance_stats("llama3.1:q4_8b")
    print(f"\nllama3.1:q4_8b (4-bit quantized):")
    print(f"  Calls: {stats_quant['total_calls']}")
    print(f"  Avg Time: {stats_quant['avg_time']:.2f}s")
    print(f"  Min/Max: {stats_quant['min_time']:.2f}s / {stats_quant['max_time']:.2f}s")
    
    speedup = stats_full['avg_time'] / stats_quant['avg_time']
    print(f"\nSpeedup with 4-bit quantization: {speedup:.2f}x")
    
    # Example 4: Memory usage comparison
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Memory Usage Comparison")
    print("=" * 60)
    
    base_size = 8.0  # 8B model in GB
    
    print(f"\nBase model size: {base_size:.1f} GB")
    print("\nEstimated memory usage:")
    print(f"  Full precision: {base_size:.1f} GB")
    print(f"  8-bit: {base_size * 0.5:.1f} GB (50% reduction)")
    print(f"  4-bit: {base_size * 0.25:.1f} GB (75% reduction)")
    
    print("\nGPU Recommendations:")
    print("  RTX 4060 (8GB): Use 4-bit quantization")
    print("  RTX 4070 (12GB): Use 8-bit quantization")
    print("  RTX 4080+ (16GB+): Use full precision")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("\n✓ Quantization reduces memory usage by 50-75%")
    print("✓ Can improve inference speed by 1.2-2.0x")
    print("✓ Easy to switch between quantization levels")
    print("✓ Performance tracking helps optimize settings")
    print("\nFor full examples with AI Selector integration:")
    print("  See: QUANTIZATION_QUICK_START.md")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
