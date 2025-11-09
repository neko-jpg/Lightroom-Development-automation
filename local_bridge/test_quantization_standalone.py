"""
Standalone test suite for model quantization functionality.
Does not require cv2 or other heavy dependencies.

Tests:
- Quantization settings management
- Model name transformation
- Performance tracking

Requirements: 17.4
"""

import sys
import logging
from unittest.mock import Mock, patch

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ollama_client_quantization():
    """Test OllamaClient quantization features."""
    from ollama_client import OllamaClient
    
    print("\n" + "=" * 60)
    print("TEST: OllamaClient Quantization")
    print("=" * 60)
    
    # Test 1: Default initialization
    print("\n1. Testing default initialization...")
    client = OllamaClient()
    assert client.enable_quantization == False
    assert client.quantization_bits == 8
    print("   ✓ Default settings correct")
    
    # Test 2: Initialization with quantization
    print("\n2. Testing initialization with quantization...")
    client = OllamaClient(enable_quantization=True, quantization_bits=4)
    assert client.enable_quantization == True
    assert client.quantization_bits == 4
    print("   ✓ Quantization settings correct")
    
    # Test 3: Model name transformation (disabled)
    print("\n3. Testing model name transformation (disabled)...")
    client = OllamaClient(enable_quantization=False)
    model = "llama3.1:8b-instruct"
    result = client._get_quantized_model_name(model)
    assert result == model
    print(f"   ✓ {model} → {result}")
    
    # Test 4: Model name transformation (8-bit)
    print("\n4. Testing model name transformation (8-bit)...")
    client = OllamaClient(enable_quantization=True, quantization_bits=8)
    model = "llama3.1:8b-instruct"
    result = client._get_quantized_model_name(model)
    assert result == "llama3.1:q8_8b-instruct"
    print(f"   ✓ {model} → {result}")
    
    # Test 5: Model name transformation (4-bit)
    print("\n5. Testing model name transformation (4-bit)...")
    client = OllamaClient(enable_quantization=True, quantization_bits=4)
    model = "llama3.1:8b-instruct"
    result = client._get_quantized_model_name(model)
    assert result == "llama3.1:q4_8b-instruct"
    print(f"   ✓ {model} → {result}")
    
    # Test 6: Model name without tag
    print("\n6. Testing model name without tag...")
    client = OllamaClient(enable_quantization=True, quantization_bits=8)
    model = "llama3.1"
    result = client._get_quantized_model_name(model)
    assert result == "llama3.1:q8"
    print(f"   ✓ {model} → {result}")
    
    # Test 7: Already quantized model
    print("\n7. Testing already quantized model...")
    client = OllamaClient(enable_quantization=True, quantization_bits=8)
    model = "llama3.1:q4_8b-instruct"
    result = client._get_quantized_model_name(model)
    assert result == model
    print(f"   ✓ {model} → {result} (unchanged)")
    
    # Test 8: Set quantization
    print("\n8. Testing set_quantization...")
    client = OllamaClient()
    client.set_quantization(True, 4)
    assert client.enable_quantization == True
    assert client.quantization_bits == 4
    print("   ✓ Quantization enabled (4-bit)")
    
    # Test 9: Invalid quantization bits
    print("\n9. Testing invalid quantization bits...")
    client = OllamaClient()
    try:
        client.set_quantization(True, 16)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be 4 or 8" in str(e)
        print("   ✓ ValueError raised correctly")
    
    # Test 10: Get quantization settings (disabled)
    print("\n10. Testing get_quantization_settings (disabled)...")
    client = OllamaClient(enable_quantization=False)
    settings = client.get_quantization_settings()
    assert settings['enabled'] == False
    assert settings['bits'] is None
    assert settings['memory_reduction'] is None
    print("   ✓ Settings correct for disabled quantization")
    
    # Test 11: Get quantization settings (8-bit)
    print("\n11. Testing get_quantization_settings (8-bit)...")
    client = OllamaClient(enable_quantization=True, quantization_bits=8)
    settings = client.get_quantization_settings()
    assert settings['enabled'] == True
    assert settings['bits'] == 8
    assert settings['memory_reduction'] == "~50% (8-bit quantization)"
    print("   ✓ Settings correct for 8-bit quantization")
    
    # Test 12: Get quantization settings (4-bit)
    print("\n12. Testing get_quantization_settings (4-bit)...")
    client = OllamaClient(enable_quantization=True, quantization_bits=4)
    settings = client.get_quantization_settings()
    assert settings['enabled'] == True
    assert settings['bits'] == 4
    assert settings['memory_reduction'] == "~75% (4-bit quantization)"
    print("   ✓ Settings correct for 4-bit quantization")
    
    # Test 13: Performance tracking
    print("\n13. Testing performance tracking...")
    client = OllamaClient()
    client._record_performance("test_model", 2.5, success=True)
    client._record_performance("test_model", 2.3, success=True)
    client._record_performance("test_model", 0.0, success=False)
    
    stats = client.get_performance_stats("test_model")
    assert stats['total_calls'] == 3
    assert stats['successful_calls'] == 2
    assert stats['failed_calls'] == 1
    assert abs(stats['avg_time'] - 2.4) < 0.01
    assert stats['min_time'] == 2.3
    assert stats['max_time'] == 2.5
    print("   ✓ Performance tracking working correctly")
    
    print("\n" + "=" * 60)
    print("All OllamaClient tests passed! ✓")
    print("=" * 60)


def test_memory_reduction():
    """Test memory reduction estimation."""
    from ollama_client import OllamaClient
    
    print("\n" + "=" * 60)
    print("TEST: Memory Reduction Estimation")
    print("=" * 60)
    
    # Test 4-bit
    print("\n1. Testing 4-bit memory reduction...")
    client = OllamaClient(enable_quantization=True, quantization_bits=4)
    reduction = client._estimate_memory_reduction()
    assert reduction == "~75% (4-bit quantization)"
    print(f"   ✓ {reduction}")
    
    # Test 8-bit
    print("\n2. Testing 8-bit memory reduction...")
    client.set_quantization(True, 8)
    reduction = client._estimate_memory_reduction()
    assert reduction == "~50% (8-bit quantization)"
    print(f"   ✓ {reduction}")
    
    # Test disabled
    print("\n3. Testing disabled quantization...")
    client.set_quantization(False)
    reduction = client._estimate_memory_reduction()
    assert reduction is None
    print("   ✓ None (quantization disabled)")
    
    print("\n" + "=" * 60)
    print("Memory reduction tests passed! ✓")
    print("=" * 60)


def test_integration_workflow():
    """Test complete quantization workflow."""
    from ollama_client import OllamaClient
    
    print("\n" + "=" * 60)
    print("TEST: Integration Workflow")
    print("=" * 60)
    
    # Create client with quantization
    print("\n1. Creating client with 8-bit quantization...")
    client = OllamaClient(enable_quantization=True, quantization_bits=8)
    settings = client.get_quantization_settings()
    assert settings['enabled'] == True
    assert settings['bits'] == 8
    print("   ✓ Client created with 8-bit quantization")
    
    # Test model name transformation
    print("\n2. Testing model name transformation...")
    model = "llama3.1:8b-instruct"
    quantized = client._get_quantized_model_name(model)
    assert 'q8' in quantized
    print(f"   ✓ {model} → {quantized}")
    
    # Switch to 4-bit
    print("\n3. Switching to 4-bit quantization...")
    client.set_quantization(True, 4)
    quantized = client._get_quantized_model_name(model)
    assert 'q4' in quantized
    print(f"   ✓ {model} → {quantized}")
    
    # Disable quantization
    print("\n4. Disabling quantization...")
    client.set_quantization(False)
    quantized = client._get_quantized_model_name(model)
    assert quantized == model
    print(f"   ✓ {model} → {quantized}")
    
    print("\n" + "=" * 60)
    print("Integration workflow tests passed! ✓")
    print("=" * 60)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MODEL QUANTIZATION STANDALONE TESTS")
    print("=" * 60)
    
    try:
        test_ollama_client_quantization()
        test_memory_reduction()
        test_integration_workflow()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓✓✓")
        print("=" * 60)
        print("\nSummary:")
        print("  - OllamaClient quantization: 13 tests passed")
        print("  - Memory reduction: 3 tests passed")
        print("  - Integration workflow: 4 tests passed")
        print("  - Total: 20 tests passed")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
