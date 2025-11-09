"""
Example: Model Performance Statistics Integration with AI Selector

Demonstrates how model performance statistics automatically track
and optimize model selection during photo evaluation.

Requirements: 18.5
"""

import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_automatic_tracking():
    """Example: Automatic performance tracking during AI evaluation."""
    print("\n" + "="*60)
    print("AUTOMATIC PERFORMANCE TRACKING")
    print("="*60)
    
    from model_performance_integration import get_model_performance_integration
    from model_manager import ModelManager
    from ai_selector import AISelector
    
    # Initialize components
    model_manager = ModelManager()
    integration = get_model_performance_integration(model_manager)
    ai_selector = AISelector(enable_llm=True)
    
    # Simulate photo evaluation with automatic tracking
    test_photo = "path/to/test/photo.jpg"
    model_name = "llama3.1:8b-instruct"
    
    print(f"\nEvaluating photo with {model_name}...")
    print("Performance will be automatically tracked...")
    
    # Use context manager for automatic tracking
    with integration.track_model_performance(
        model_name=model_name,
        operation="photo_evaluation",
        photo_id=123
    ):
        # Simulate evaluation (in real use, this would be actual evaluation)
        time.sleep(0.5)  # Simulate processing
        result = {
            'overall_score': 4.3,
            'quality_score': 4.3,
            'recommendation': 'approve',
            'tags': ['portrait', 'high_quality']
        }
    
    print("✓ Evaluation complete and performance recorded")
    
    # Get statistics
    stats = integration.stats_collector.get_model_statistics(model_name)
    if stats:
        print(f"\nModel Statistics:")
        print(f"  Total Operations: {stats.total_operations}")
        print(f"  Avg Processing Time: {stats.avg_processing_time_ms:.2f}ms")
        print(f"  Success Rate: {stats.success_rate:.1f}%")


def example_intelligent_model_selection():
    """Example: Intelligent model selection based on performance history."""
    print("\n" + "="*60)
    print("INTELLIGENT MODEL SELECTION")
    print("="*60)
    
    from model_performance_integration import get_model_performance_integration
    from model_manager import ModelManager
    
    # Initialize
    model_manager = ModelManager()
    integration = get_model_performance_integration(model_manager)
    
    # Simulate performance history for multiple models
    print("\nSimulating performance history...")
    
    models_performance = {
        "llama3.2:3b-instruct": {
            "avg_time": 600,
            "quality": 3.8,
            "count": 15
        },
        "llama3.1:8b-instruct": {
            "avg_time": 1200,
            "quality": 4.2,
            "count": 20
        },
        "llama3.1:13b-instruct": {
            "avg_time": 2100,
            "quality": 4.7,
            "count": 12
        }
    }
    
    for model_name, perf in models_performance.items():
        for i in range(perf["count"]):
            integration.record_performance(
                model_name=model_name,
                operation="photo_evaluation",
                processing_time_ms=perf["avg_time"] + (i * 10),
                quality_score=perf["quality"],
                success=True
            )
    
    print("✓ Performance history created")
    
    # Get recommendations for different scenarios
    print("\nModel Recommendations:")
    
    scenarios = [
        ("speed", 8.0, "High-volume batch processing"),
        ("quality", 8.0, "Critical photo selection"),
        ("balanced", 8.0, "General use"),
        ("reliable", 8.0, "Production environment")
    ]
    
    for priority, vram, description in scenarios:
        recommended = integration.select_best_model(
            priority=priority,
            available_vram_gb=vram
        )
        
        if recommended:
            stats = integration.stats_collector.get_model_statistics(recommended)
            print(f"\n  {priority.capitalize()} ({description}):")
            print(f"    Model: {recommended}")
            if stats:
                print(f"    Avg Time: {stats.avg_processing_time_ms:.2f}ms")
                if stats.avg_quality_score:
                    print(f"    Avg Quality: {stats.avg_quality_score:.2f}/5.0")


def example_performance_monitoring():
    """Example: Monitoring model performance over time."""
    print("\n" + "="*60)
    print("PERFORMANCE MONITORING")
    print("="*60)
    
    from model_performance_integration import get_model_performance_integration
    from model_manager import ModelManager
    
    # Initialize
    model_manager = ModelManager()
    integration = get_model_performance_integration(model_manager)
    
    # Simulate ongoing operations
    print("\nSimulating ongoing operations...")
    
    model_name = "llama3.1:8b-instruct"
    
    # Simulate performance degradation
    for i in range(20):
        # Gradually increasing processing time (simulating degradation)
        proc_time = 1200 + (i * 50)
        quality = 4.2 - (i * 0.02)  # Slight quality decrease
        success = i < 18  # 2 failures
        
        integration.record_performance(
            model_name=model_name,
            operation="photo_evaluation",
            processing_time_ms=proc_time,
            quality_score=max(quality, 3.0),
            success=success
        )
    
    print("✓ Operations recorded")
    
    # Get performance insights
    insights = integration.get_performance_insights(duration_hours=24)
    
    print(f"\nPerformance Insights:")
    print(f"  Models Analyzed: {insights['models_analyzed']}")
    print(f"  Total Operations: {insights['total_operations']}")
    print(f"  Overall Success Rate: {insights['overall_success_rate']:.1f}%")
    
    if insights['warnings']:
        print("\n  ⚠ Warnings Detected:")
        for warning in insights['warnings']:
            print(f"    - {warning}")
    
    # Get trend data
    trend = integration.stats_collector.get_model_performance_trend(
        model_name=model_name,
        metric="processing_time",
        hours=1,
        bucket_size_minutes=1
    )
    
    if 'buckets' in trend and trend['buckets']:
        print(f"\n  Performance Trend (Processing Time):")
        for bucket in trend['buckets'][:5]:
            print(f"    {bucket['timestamp']}: {bucket['value']:.2f}ms")


def example_model_comparison():
    """Example: Comparing multiple models side-by-side."""
    print("\n" + "="*60)
    print("MODEL COMPARISON")
    print("="*60)
    
    from model_performance_integration import get_model_performance_integration
    from model_manager import ModelManager
    
    # Initialize
    model_manager = ModelManager()
    integration = get_model_performance_integration(model_manager)
    
    # Simulate performance for comparison
    models = ["llama3.2:3b-instruct", "llama3.1:8b-instruct", "llama3.1:13b-instruct"]
    
    print("\nRecording performance for comparison...")
    
    for model in models:
        for i in range(15):
            if "3b" in model:
                proc_time = 600 + i * 10
                quality = 3.8
            elif "8b" in model:
                proc_time = 1200 + i * 20
                quality = 4.2
            else:  # 13b
                proc_time = 2100 + i * 30
                quality = 4.7
            
            integration.record_performance(
                model_name=model,
                operation="photo_evaluation",
                processing_time_ms=proc_time,
                quality_score=quality,
                success=True
            )
    
    print("✓ Performance data recorded")
    
    # Compare models
    comparison = integration.stats_collector.compare_models(models)
    
    print("\nComparison Results:")
    print("\n  Rankings:")
    for category, info in comparison['rankings'].items():
        if info:
            print(f"    {category.replace('_', ' ').title()}: {info['model']}")
    
    print("\n  Detailed Statistics:")
    for model in models:
        stats = comparison['models'].get(model)
        if stats:
            print(f"\n    {model}:")
            print(f"      Operations: {stats['total_operations']}")
            print(f"      Avg Time: {stats['avg_processing_time_ms']:.2f}ms")
            print(f"      Avg Quality: {stats['avg_quality_score']:.2f}/5.0")
            print(f"      Success Rate: {stats['success_rate']:.1f}%")


def example_adaptive_model_switching():
    """Example: Adaptive model switching based on performance."""
    print("\n" + "="*60)
    print("ADAPTIVE MODEL SWITCHING")
    print("="*60)
    
    from model_performance_integration import get_model_performance_integration
    from model_manager import ModelManager
    
    # Initialize
    model_manager = ModelManager()
    integration = get_model_performance_integration(model_manager)
    
    # Simulate batch processing with adaptive model selection
    print("\nProcessing batch of photos with adaptive model selection...")
    
    available_models = ["llama3.2:3b-instruct", "llama3.1:8b-instruct"]
    
    # Build performance history
    for model in available_models:
        for i in range(12):
            if "3b" in model:
                proc_time = 600
                quality = 3.8
            else:
                proc_time = 1200
                quality = 4.2
            
            integration.record_performance(
                model_name=model,
                operation="photo_evaluation",
                processing_time_ms=proc_time,
                quality_score=quality,
                success=True
            )
    
    # Process photos with different priorities
    scenarios = [
        ("speed", "Quick preview generation"),
        ("quality", "Final selection"),
        ("balanced", "General processing")
    ]
    
    for priority, description in scenarios:
        # Select best model for this scenario
        selected_model = integration.select_best_model(
            priority=priority,
            available_vram_gb=8.0
        )
        
        print(f"\n  Scenario: {description}")
        print(f"    Priority: {priority}")
        print(f"    Selected Model: {selected_model}")
        
        # Simulate processing
        with integration.track_model_performance(
            model_name=selected_model,
            operation="photo_evaluation"
        ):
            time.sleep(0.1)  # Simulate processing
            result = {'overall_score': 4.0}
        
        print(f"    ✓ Processing complete")


def main():
    """Run all integration examples."""
    print("\n" + "="*60)
    print("MODEL PERFORMANCE STATISTICS - AI INTEGRATION EXAMPLES")
    print("="*60)
    
    try:
        example_automatic_tracking()
        example_intelligent_model_selection()
        example_performance_monitoring()
        example_model_comparison()
        example_adaptive_model_switching()
        
        print("\n" + "="*60)
        print("ALL INTEGRATION EXAMPLES COMPLETED")
        print("="*60)
        
        print("\nKey Takeaways:")
        print("  ✓ Performance is automatically tracked during AI operations")
        print("  ✓ Model selection is optimized based on historical performance")
        print("  ✓ Performance monitoring detects degradation and issues")
        print("  ✓ Model comparison enables data-driven decisions")
        print("  ✓ Adaptive switching optimizes for different scenarios")
    
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == '__main__':
    main()
