"""
Example usage of LLM-based photo evaluation

Demonstrates how to use the AI Selector with LLM evaluation enabled.
"""

import sys
from pathlib import Path

from ai_selector import AISelector
from ollama_client import OllamaClient


def example_basic_llm_evaluation():
    """Basic example of LLM-enabled photo evaluation."""
    print("=" * 60)
    print("Example 1: Basic LLM Evaluation")
    print("=" * 60)
    
    # Initialize AI Selector with LLM enabled
    selector = AISelector(
        enable_llm=True,
        llm_model="llama3.1:8b-instruct"
    )
    
    # Evaluate a photo
    image_path = "path/to/your/photo.jpg"
    
    try:
        result = selector.evaluate(image_path)
        
        print(f"\n📸 Photo: {Path(image_path).name}")
        print(f"⭐ Overall Score: {result['overall_score']:.2f}/5.0")
        print(f"📋 Recommendation: {result['recommendation'].upper()}")
        
        # Display LLM evaluation if available
        if 'llm_evaluation' in result:
            llm_eval = result['llm_evaluation']
            print(f"\n🤖 LLM Evaluation:")
            print(f"   Score: {llm_eval['llm_score']:.2f}/5.0")
            print(f"   Reasoning: {llm_eval['reasoning']}")
            
            if llm_eval['strengths']:
                print(f"\n✅ Strengths:")
                for strength in llm_eval['strengths']:
                    print(f"   • {strength}")
            
            if llm_eval['weaknesses']:
                print(f"\n⚠️  Weaknesses:")
                for weakness in llm_eval['weaknesses']:
                    print(f"   • {weakness}")
        
        print(f"\n🏷️  Tags: {', '.join(result['tags'])}")
        
    except FileNotFoundError:
        print(f"⚠️  Please provide a valid image path")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_llm_disabled():
    """Example with LLM evaluation disabled."""
    print("\n" + "=" * 60)
    print("Example 2: LLM Disabled (Technical Metrics Only)")
    print("=" * 60)
    
    # Initialize AI Selector with LLM disabled
    selector = AISelector(enable_llm=False)
    
    image_path = "path/to/your/photo.jpg"
    
    try:
        result = selector.evaluate(image_path)
        
        print(f"\n📸 Photo: {Path(image_path).name}")
        print(f"⭐ Overall Score: {result['overall_score']:.2f}/5.0")
        print(f"📋 Recommendation: {result['recommendation'].upper()}")
        
        print(f"\n📊 Technical Scores:")
        print(f"   Focus: {result['quality']['focus_score']:.2f}/5.0")
        print(f"   Exposure: {result['quality']['exposure_score']:.2f}/5.0")
        print(f"   Composition: {result['quality']['composition_score']:.2f}/5.0")
        
        print(f"\n🏷️  Tags: {', '.join(result['tags'])}")
        
        # Note: No LLM evaluation in result
        if 'llm_evaluation' not in result:
            print("\n💡 LLM evaluation was disabled")
        
    except FileNotFoundError:
        print(f"⚠️  Please provide a valid image path")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_batch_with_llm():
    """Example of batch evaluation with LLM."""
    print("\n" + "=" * 60)
    print("Example 3: Batch Evaluation with LLM")
    print("=" * 60)
    
    # Initialize AI Selector
    selector = AISelector(
        enable_llm=True,
        llm_model="llama3.1:8b-instruct"
    )
    
    # List of images to evaluate
    image_paths = [
        "path/to/photo1.jpg",
        "path/to/photo2.jpg",
        "path/to/photo3.jpg"
    ]
    
    try:
        results = selector.batch_evaluate(image_paths)
        
        print(f"\n📊 Evaluated {len(results)} photos\n")
        
        # Sort by score (highest first)
        sorted_results = sorted(
            results,
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )
        
        for i, result in enumerate(sorted_results, 1):
            print(f"{i}. {Path(result['file_path']).name}")
            print(f"   Score: {result['overall_score']:.2f}/5.0")
            print(f"   Recommendation: {result['recommendation']}")
            
            if 'llm_evaluation' in result:
                llm_score = result['llm_evaluation']['llm_score']
                print(f"   LLM Score: {llm_score:.2f}/5.0")
            
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_custom_llm_model():
    """Example using a custom LLM model."""
    print("\n" + "=" * 60)
    print("Example 4: Custom LLM Model")
    print("=" * 60)
    
    # Initialize with custom model
    selector = AISelector(
        enable_llm=True,
        llm_model="llama3.2-vision:11b"  # Use vision model if available
    )
    
    image_path = "path/to/your/photo.jpg"
    
    try:
        result = selector.evaluate(image_path)
        
        print(f"\n📸 Photo: {Path(image_path).name}")
        print(f"🤖 Model: llama3.2-vision:11b")
        print(f"⭐ Overall Score: {result['overall_score']:.2f}/5.0")
        
        if 'llm_evaluation' in result:
            print(f"\n💭 LLM Reasoning:")
            print(f"   {result['llm_evaluation']['reasoning']}")
        
    except FileNotFoundError:
        print(f"⚠️  Please provide a valid image path")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_llm_fallback():
    """Example showing LLM fallback behavior."""
    print("\n" + "=" * 60)
    print("Example 5: LLM Fallback (Ollama Not Running)")
    print("=" * 60)
    
    # Initialize AI Selector
    selector = AISelector(enable_llm=True)
    
    image_path = "path/to/your/photo.jpg"
    
    try:
        result = selector.evaluate(image_path)
        
        print(f"\n📸 Photo: {Path(image_path).name}")
        print(f"⭐ Overall Score: {result['overall_score']:.2f}/5.0")
        
        if 'llm_evaluation' not in result:
            print("\n⚠️  LLM evaluation failed, using technical metrics only")
            print("   (This happens when Ollama is not running)")
        else:
            print("\n✅ LLM evaluation successful")
        
    except FileNotFoundError:
        print(f"⚠️  Please provide a valid image path")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_compare_with_without_llm():
    """Compare evaluation with and without LLM."""
    print("\n" + "=" * 60)
    print("Example 6: Compare With/Without LLM")
    print("=" * 60)
    
    image_path = "path/to/your/photo.jpg"
    
    try:
        # Without LLM
        selector_no_llm = AISelector(enable_llm=False)
        result_no_llm = selector_no_llm.evaluate(image_path)
        
        # With LLM
        selector_with_llm = AISelector(enable_llm=True)
        result_with_llm = selector_with_llm.evaluate(image_path)
        
        print(f"\n📸 Photo: {Path(image_path).name}\n")
        
        print("Without LLM:")
        print(f"  Score: {result_no_llm['overall_score']:.2f}/5.0")
        print(f"  Recommendation: {result_no_llm['recommendation']}")
        print(f"  Tags: {len(result_no_llm['tags'])} tags")
        
        print("\nWith LLM:")
        print(f"  Score: {result_with_llm['overall_score']:.2f}/5.0")
        print(f"  Recommendation: {result_with_llm['recommendation']}")
        print(f"  Tags: {len(result_with_llm['tags'])} tags")
        
        if 'llm_evaluation' in result_with_llm:
            llm_eval = result_with_llm['llm_evaluation']
            print(f"  LLM Score: {llm_eval['llm_score']:.2f}/5.0")
            print(f"  LLM Reasoning: {llm_eval['reasoning'][:50]}...")
        
        # Calculate difference
        score_diff = result_with_llm['overall_score'] - result_no_llm['overall_score']
        print(f"\n📊 Score Difference: {score_diff:+.2f}")
        
    except FileNotFoundError:
        print(f"⚠️  Please provide a valid image path")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples."""
    print("\n🤖 LLM-Based Photo Evaluation Examples\n")
    
    if len(sys.argv) > 1:
        # Use provided image path
        image_path = sys.argv[1]
        
        # Update examples with actual path
        globals()['image_path'] = image_path
        
        print(f"Using image: {image_path}\n")
    else:
        print("💡 Usage: python example_llm_evaluation_usage.py <image_path>")
        print("   Running with placeholder paths...\n")
    
    # Run examples
    example_basic_llm_evaluation()
    example_llm_disabled()
    # example_batch_with_llm()  # Uncomment if you have multiple images
    # example_custom_llm_model()  # Uncomment to try different models
    # example_llm_fallback()
    # example_compare_with_without_llm()
    
    print("\n" + "=" * 60)
    print("✅ Examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
