"""
Example usage of Model Performance Statistics System

Demonstrates:
- Recording model performance
- Getting statistics
- Comparing models
- Model recommendations
- Performance trends
- Integration with AI Selector

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


def example_basic_recording():
    """Example: Basic performance recording."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Performance Recording")
    print("="*60)
    
    from model_performance_stats import get_model_performance_stats
    
    collector = get_model_performance_stats()
    
    # Record performance for a model
    collector.record_model_performance(
        model_name="llama3.1:8b-instruct",
        operation="photo_evaluation",
        processing_time_ms=1234.56,
        quality_score=4.2,
        success=True,
        memory_used_mb=512.0,
        tokens_generated=150,
        photo_id=123,
        job_id="job_abc123"
    )
    
    print("✓ Performance recorded for llama3.1:8b-instruct")
    
    # Get statistics
    stats = collector.get_model_statistics("llama3.1:8b-instruct")
    if stats:
        print(f"\nStatistics:")
        print(f"  Total Operations: {stats.total_operations}")
        print(f"  Success Rate: {stats.success_rate:.1f}%")
        print(f"  Avg Processing Time: {stats.avg_processing_time_ms:.2f}ms")
        if stats.avg_quality_score:
            print(f"  Avg Quality Score: {stats.avg_quality_score:.2f}/5.0")


def example_multiple_models():
    """Example: Recording and comparing multiple models."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multiple Models Comparison")
    print("="*60)
    
    from model_performance_stats import get_model_performance_stats
    
    collector = get_model_performance_stats()
    
    # Simulate performance for different models
    models_data = {
        "llama3.1:8b-instruct": {
            "processing_times": [1200, 1300, 1100, 1250, 1150],
            "quality_scores": [4.2, 4.3, 4.1, 4.4, 4.2]
        },
        "llama3.1:13b-instruct": {
            "processing_times": [2100, 2200, 2000, 2150, 2050],
            "quality_scores": [4.7, 4.8, 4.6, 4.9, 4.7]
        },
        "llama3.2:3b-instruct": {
            "processing_times": [600, 650, 580, 620, 590],
            "quality_scores": [3.8, 3.9, 3.7, 4.0, 3.8]
        }
    }
    
    # Record performance for each model
    for model_name, data in models_data.items():
        for i, (proc_time, quality) in enumerate(zip(data["processing_times"], data["quality_scores"])):
            collector.record_model_performance(
                model_name=model_name,
                operation="photo_evaluation",
                processing_time_ms=proc_time,
                quality_score=quality,
                success=True,
                photo_id=100 + i
            )
        print(f"✓ Recorded {len(data['processing_times'])} operations for {model_name}")
    
    # Compare models
    print("\nComparing models...")
    comparison = collector.compare_models(list(models_data.keys()))
    
    print("\nRankings:")
    for category, info in comparison['rankings'].items():
        if info:
            print(f"  {category.replace('_', ' ').title()}: {info['model']}")


def example_model_recommendation():
    """Example: Getting model recommendations."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Model Recommendations")
    print("="*60)
    
    from model_performance_stats import get_model_performance_stats
    
    collector = get_model_performance_stats()
    
    # Ensure we have enough data (min_operations=10)
    models = ["llama3.1:8b-instruct", "llama3.1:13b-instruct", "llama3.2:3b-instruct"]
    
    for model in models:
        for i in range(12):
            # Simulate different characteristics
            if "3b" in model:
                proc_time = 600 + i * 10
                quality = 3.8 + i * 0.02
            elif "8b" in model:
                proc_time = 1200 + i * 20
                quality = 4.2 + i * 0.02
            else:  # 13b
                proc_time = 2100 + i * 30
                quality = 4.7 + i * 0.02
            
            collector.record_model_performance(
                model_name=model,
                operation="photo_evaluation",
                processing_time_ms=proc_time,
                quality_score=min(quality, 5.0),
                success=True
            )
    
    # Get recommendations for different priorities
    priorities = ["speed", "quality", "balanced", "reliable"]
    
    print("\nRecommendations:")
    for priority in priorities:
        recommended = collector.recommend_model(priority=priority, min_operations=10)
        if recommended:
            stats = collector.get_model_statistics(recommended)
            print(f"\n  {priority.capitalize()} Priority: {recommended}")
            if stats:
                print(f"    Avg Time: {stats.avg_processing_time_ms:.2f}ms")
                if stats.avg_quality_score:
                    print(f"    Avg Quality: {stats.avg_quality_score:.2f}/5.0")
                print(f"    Success Rate: {stats.success_rate:.1f}%")


def example_performance_trend():
    """Example: Analyzing performance trends."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Performance Trends")
    print("="*60)
    
    from model_performance_stats import get_model_performance_stats
    
    collector = get_model_performance_stats()
    model_name = "llama3.1:8b-instruct"
    
    # Record performance over time with gradual improvement
    print(f"\nRecording performance data for {model_name}...")
    for i in range(20):
        # Simulate performance improvement over time
        proc_time = 1500 - i * 20  # Getting faster
        quality = 3.5 + i * 0.05  # Getting better quality
        
        collector.record_model_performance(
            model_name=model_name,
            operation="photo_evaluation",
            processing_time_ms=proc_time,
            quality_score=min(quality, 5.0),
            success=True
        )
        time.sleep(0.01)  # Small delay for different timestamps
    
    # Get trend data
    trend = collector.get_model_performance_trend(
        model_name=model_name,
        metric="processing_time",
        hours=1,
        bucket_size_minutes=1
    )
    
    if 'buckets' in trend and trend['buckets']:
        print(f"\nPerformance Trend ({trend['metric']}):")
        for bucket in trend['buckets'][:5]:  # Show first 5 buckets
            print(f"  {bucket['timestamp']}: {bucket['value']:.2f}ms ({bucket['count']} ops)")


def example_integration_with_ai_selector():
    """Example: Integration with AI Selector."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Integration with AI Selector")
    print("="*60)
    
    from model_performance_integration import get_model_performance_integration
    from model_manager import ModelManager
    
    # Initialize integration
    model_manager = ModelManager()
    integration = get_model_performance_integration(model_manager)
    
    # Simulate photo evaluation with performance tracking
    model_name = "llama3.1:8b-instruct"
    
    print(f"\nEvaluating photo with {model_name}...")
    
    # Use context manager for automatic performance tracking
    with integration.track_model_performance(
        model_name=model_name,
        operation="photo_evaluation",
        photo_id=456
    ):
        # Simulate photo evaluation
        time.sleep(0.1)  # Simulate processing
        result = {
            'overall_score': 4.3,
            'quality_score': 4.3,
            'recommendation': 'approve'
        }
    
    print("✓ Photo evaluated and performance recorded")
    
    # Get performance summary
    summary = integration.get_model_performance_summary(model_name, duration_hours=24)
    
    print(f"\nPerformance Summary for {model_name}:")
    if 'statistics' in summary:
        stats = summary['statistics']
        print(f"  Total Operations: {stats['total_operations']}")
        print(f"  Success Rate: {stats['success_rate']:.1f}%")
        print(f"  Avg Time: {stats['avg_processing_time_ms']:.2f}ms")


def example_performance_insights():
    """Example: Getting performance insights."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Performance Insights")
    print("="*60)
    
    from model_performance_integration import get_model_performance_integration
    from model_manager import ModelManager
    
    model_manager = ModelManager()
    integration = get_model_performance_integration(model_manager)
    
    # Record some test data
    models = ["llama3.1:8b-instruct", "llama3.1:13b-instruct", "llama3.2:3b-instruct"]
    
    for model in models:
        for i in range(15):
            if "3b" in model:
                proc_time = 600 + i * 10
                quality = 3.8
                success = True
            elif "8b" in model:
                proc_time = 1200 + i * 20
                quality = 4.2
                success = i < 14  # One failure
            else:  # 13b
                proc_time = 2100 + i * 30
                quality = 4.7
                success = True
            
            integration.record_performance(
                model_name=model,
                operation="photo_evaluation",
                processing_time_ms=proc_time,
                quality_score=quality,
                success=success
            )
    
    # Get insights
    insights = integration.get_performance_insights(duration_hours=24)
    
    print(f"\nPerformance Insights:")
    print(f"  Models Analyzed: {insights['models_analyzed']}")
    print(f"  Total Operations: {insights['total_operations']}")
    print(f"  Overall Success Rate: {insights['overall_success_rate']:.1f}%")
    
    if insights['fastest_model']:
        print(f"\n  Fastest Model: {insights['fastest_model']['name']}")
        print(f"    Avg Time: {insights['fastest_model']['avg_time_ms']:.2f}ms")
    
    if insights['highest_quality_model']:
        print(f"\n  Highest Quality: {insights['highest_quality_model']['name']}")
        print(f"    Avg Quality: {insights['highest_quality_model']['avg_quality']:.2f}/5.0")
    
    if insights['most_reliable_model']:
        print(f"\n  Most Reliable: {insights['most_reliable_model']['name']}")
        print(f"    Success Rate: {insights['most_reliable_model']['success_rate']:.1f}%")
    
    print("\n  Recommendations:")
    for priority, model in insights['recommendations'].items():
        print(f"    {priority.capitalize()}: {model}")
    
    if insights['warnings']:
        print("\n  Warnings:")
        for warning in insights['warnings']:
            print(f"    ⚠ {warning}")


def example_export_statistics():
    """Example: Exporting statistics."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Exporting Statistics")
    print("="*60)
    
    from model_performance_stats import get_model_performance_stats
    
    collector = get_model_performance_stats()
    
    # Export to file
    export_file = "data/model_performance_export.json"
    collector.export_statistics(export_file)
    
    print(f"✓ Statistics exported to: {export_file}")
    
    # Verify export
    if Path(export_file).exists():
        import json
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        print(f"\nExport contains:")
        print(f"  Models: {len(data.get('models', {}))}")
        print(f"  Timestamp: {data.get('export_timestamp', 'N/A')}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("MODEL PERFORMANCE STATISTICS - USAGE EXAMPLES")
    print("="*60)
    
    try:
        example_basic_recording()
        example_multiple_models()
        example_model_recommendation()
        example_performance_trend()
        example_integration_with_ai_selector()
        example_performance_insights()
        example_export_statistics()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60)
    
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == '__main__':
    main()
