"""
Model Performance Integration

Integrates model performance statistics with:
- AI Selector (automatic performance recording)
- Model Manager (performance-based model selection)
- Performance Metrics (unified metrics collection)

Requirements: 18.5
"""

import logging
import time
from typing import Dict, Optional
from contextlib import contextmanager

from model_performance_stats import get_model_performance_stats
from model_manager import ModelManager
from performance_metrics import get_performance_metrics_collector

logger = logging.getLogger(__name__)


class ModelPerformanceIntegration:
    """
    Integration layer for model performance tracking.
    
    Automatically records performance metrics when models are used
    and provides intelligent model selection based on performance history.
    """
    
    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        auto_record: bool = True
    ):
        """
        Initialize model performance integration.
        
        Args:
            model_manager: Model manager instance
            auto_record: Automatically record performance metrics
        """
        self.model_manager = model_manager
        self.auto_record = auto_record
        self.stats_collector = get_model_performance_stats()
        self.metrics_collector = get_performance_metrics_collector()
        
        logger.info(f"Model performance integration initialized (auto_record={auto_record})")
    
    @contextmanager
    def track_model_performance(
        self,
        model_name: str,
        operation: str,
        photo_id: Optional[int] = None,
        job_id: Optional[str] = None
    ):
        """
        Context manager for tracking model performance.
        
        Usage:
            with integration.track_model_performance("llama3.1:8b", "photo_eval"):
                result = model.evaluate(photo)
                yield result
        
        Args:
            model_name: Name of the model
            operation: Operation being performed
            photo_id: Associated photo ID
            job_id: Associated job ID
        """
        start_time = time.time()
        success = True
        error_message = None
        quality_score = None
        memory_used_mb = None
        tokens_generated = None
        
        try:
            # Record memory before operation
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024 * 1024)
            
            # Yield control to caller
            result = yield
            
            # Extract quality score if available
            if isinstance(result, dict):
                quality_score = result.get('overall_score') or result.get('quality_score')
                tokens_generated = result.get('tokens_generated')
            
            # Record memory after operation
            memory_after = process.memory_info().rss / (1024 * 1024)
            memory_used_mb = memory_after - memory_before
        
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Error during model operation: {e}")
            raise
        
        finally:
            # Calculate processing time
            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000
            
            # Record performance if auto-record is enabled
            if self.auto_record:
                self.record_performance(
                    model_name=model_name,
                    operation=operation,
                    processing_time_ms=processing_time_ms,
                    quality_score=quality_score,
                    success=success,
                    error_message=error_message,
                    memory_used_mb=memory_used_mb if memory_used_mb and memory_used_mb > 0 else None,
                    tokens_generated=tokens_generated,
                    photo_id=photo_id,
                    job_id=job_id
                )
    
    def record_performance(
        self,
        model_name: str,
        operation: str,
        processing_time_ms: float,
        quality_score: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        memory_used_mb: Optional[float] = None,
        tokens_generated: Optional[int] = None,
        photo_id: Optional[int] = None,
        job_id: Optional[str] = None
    ):
        """
        Record model performance metrics.
        
        Records to both model-specific stats and general performance metrics.
        
        Args:
            model_name: Name of the model
            operation: Operation performed
            processing_time_ms: Processing time in milliseconds
            quality_score: Quality score (1-5) if applicable
            success: Whether operation succeeded
            error_message: Error message if failed
            memory_used_mb: Memory used in MB
            tokens_generated: Number of tokens generated
            photo_id: Associated photo ID
            job_id: Associated job ID
        """
        # Record to model-specific stats
        self.stats_collector.record_model_performance(
            model_name=model_name,
            operation=operation,
            processing_time_ms=processing_time_ms,
            quality_score=quality_score,
            success=success,
            error_message=error_message,
            memory_used_mb=memory_used_mb,
            tokens_generated=tokens_generated,
            photo_id=photo_id,
            job_id=job_id
        )
        
        # Also record to general performance metrics
        self.metrics_collector.record_processing_time(
            operation=f"{model_name}:{operation}",
            duration_ms=processing_time_ms,
            photo_id=photo_id,
            job_id=job_id,
            success=success,
            error_message=error_message
        )
        
        # Update model manager usage stats if available
        if self.model_manager:
            self.model_manager.record_usage(
                model_name=model_name,
                inference_time=processing_time_ms / 1000,  # Convert to seconds
                success=success
            )
        
        logger.debug(
            f"Recorded performance: {model_name} - {operation} - "
            f"{processing_time_ms:.2f}ms - success={success}"
        )
    
    def select_best_model(
        self,
        priority: str = "balanced",
        available_vram_gb: Optional[float] = None,
        min_operations: int = 10
    ) -> Optional[str]:
        """
        Select best model based on performance history and resources.
        
        Combines model manager's compatibility checks with performance stats.
        
        Args:
            priority: Priority ("speed", "quality", "balanced", "reliable")
            available_vram_gb: Available VRAM in GB
            min_operations: Minimum operations required for recommendation
            
        Returns:
            Recommended model name or None
        """
        # Get available models from model manager
        available_models = None
        if self.model_manager:
            if available_vram_gb:
                # Filter by VRAM compatibility
                all_models = self.model_manager.list_available_models(
                    max_vram_gb=available_vram_gb,
                    installed_only=True
                )
                available_models = [m.name for m in all_models]
            else:
                # All installed models
                all_models = self.model_manager.list_available_models(installed_only=True)
                available_models = [m.name for m in all_models]
        
        # Get recommendation from performance stats
        recommended = self.stats_collector.recommend_model(
            priority=priority,
            available_models=available_models,
            min_operations=min_operations
        )
        
        if recommended:
            logger.info(f"Selected model: {recommended} (priority={priority})")
        else:
            logger.warning("No suitable model found based on performance history")
            
            # Fallback to model manager recommendation
            if self.model_manager and available_vram_gb:
                recommended = self.model_manager.recommend_model(
                    available_vram_gb=available_vram_gb,
                    priority=priority
                )
                if recommended:
                    logger.info(f"Fallback to model manager recommendation: {recommended}")
        
        return recommended
    
    def get_model_performance_summary(
        self,
        model_name: str,
        duration_hours: int = 24
    ) -> Dict:
        """
        Get comprehensive performance summary for a model.
        
        Combines data from model-specific stats and model manager.
        
        Args:
            model_name: Name of the model
            duration_hours: Hours of history to include
            
        Returns:
            Performance summary dictionary
        """
        summary = {
            'model_name': model_name,
            'duration_hours': duration_hours
        }
        
        # Get model-specific statistics
        stats = self.stats_collector.get_model_statistics(model_name, duration_hours)
        if stats:
            summary['statistics'] = stats.to_dict()
        
        # Get model metadata from model manager
        if self.model_manager:
            model_info = self.model_manager.get_model_info(model_name)
            if model_info:
                summary['model_info'] = {
                    'size': model_info.size,
                    'purpose': model_info.purpose.value,
                    'description': model_info.description,
                    'min_vram_gb': model_info.min_vram_gb,
                    'installed': model_info.installed
                }
            
            # Get model manager stats
            manager_stats = self.model_manager.get_model_statistics(model_name)
            if manager_stats:
                summary['manager_statistics'] = manager_stats
        
        return summary
    
    def compare_models_comprehensive(
        self,
        model_names: list,
        duration_hours: int = 24
    ) -> Dict:
        """
        Comprehensive comparison of multiple models.
        
        Args:
            model_names: List of model names to compare
            duration_hours: Hours of history to include
            
        Returns:
            Comprehensive comparison dictionary
        """
        comparison = {
            'models': {},
            'performance_comparison': None,
            'recommendations': {}
        }
        
        # Get performance comparison
        comparison['performance_comparison'] = self.stats_collector.compare_models(
            model_names=model_names,
            duration_hours=duration_hours
        )
        
        # Get detailed info for each model
        for model_name in model_names:
            comparison['models'][model_name] = self.get_model_performance_summary(
                model_name=model_name,
                duration_hours=duration_hours
            )
        
        # Get recommendations for different priorities
        for priority in ['speed', 'quality', 'balanced', 'reliable']:
            recommended = self.select_best_model(priority=priority)
            if recommended:
                comparison['recommendations'][priority] = recommended
        
        return comparison
    
    def get_performance_insights(self, duration_hours: int = 24) -> Dict:
        """
        Get performance insights across all models.
        
        Args:
            duration_hours: Hours of history to analyze
            
        Returns:
            Insights dictionary with recommendations and trends
        """
        insights = {
            'duration_hours': duration_hours,
            'models_analyzed': 0,
            'total_operations': 0,
            'overall_success_rate': 0.0,
            'fastest_model': None,
            'highest_quality_model': None,
            'most_reliable_model': None,
            'recommendations': {},
            'warnings': []
        }
        
        # Get all model statistics
        all_stats = self.stats_collector.get_all_model_statistics(duration_hours)
        
        if not all_stats:
            insights['warnings'].append("No performance data available")
            return insights
        
        insights['models_analyzed'] = len(all_stats)
        
        # Calculate overall metrics
        total_ops = sum(s.total_operations for s in all_stats.values())
        total_successful = sum(s.successful_operations for s in all_stats.values())
        
        insights['total_operations'] = total_ops
        insights['overall_success_rate'] = (total_successful / total_ops * 100) if total_ops > 0 else 0
        
        # Find best models
        fastest = min(all_stats.items(), key=lambda x: x[1].avg_processing_time_ms)
        insights['fastest_model'] = {
            'name': fastest[0],
            'avg_time_ms': fastest[1].avg_processing_time_ms
        }
        
        models_with_quality = {
            name: stats for name, stats in all_stats.items()
            if stats.avg_quality_score is not None
        }
        if models_with_quality:
            highest_quality = max(models_with_quality.items(), key=lambda x: x[1].avg_quality_score)
            insights['highest_quality_model'] = {
                'name': highest_quality[0],
                'avg_quality': highest_quality[1].avg_quality_score
            }
        
        most_reliable = max(all_stats.items(), key=lambda x: x[1].success_rate)
        insights['most_reliable_model'] = {
            'name': most_reliable[0],
            'success_rate': most_reliable[1].success_rate
        }
        
        # Get recommendations
        for priority in ['speed', 'quality', 'balanced', 'reliable']:
            recommended = self.select_best_model(priority=priority)
            if recommended:
                insights['recommendations'][priority] = recommended
        
        # Generate warnings
        for name, stats in all_stats.items():
            if stats.success_rate < 90:
                insights['warnings'].append(
                    f"{name}: Low success rate ({stats.success_rate:.1f}%)"
                )
            if stats.avg_processing_time_ms > 5000:
                insights['warnings'].append(
                    f"{name}: Slow processing ({stats.avg_processing_time_ms:.0f}ms avg)"
                )
        
        return insights


# Global instance
_model_performance_integration = None


def get_model_performance_integration(
    model_manager: Optional[ModelManager] = None
) -> ModelPerformanceIntegration:
    """Get global model performance integration instance."""
    global _model_performance_integration
    if _model_performance_integration is None:
        _model_performance_integration = ModelPerformanceIntegration(model_manager)
    return _model_performance_integration


def main():
    """Example usage of Model Performance Integration."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize with model manager
    from model_manager import ModelManager
    model_manager = ModelManager()
    
    integration = get_model_performance_integration(model_manager)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "select":
            priority = sys.argv[2] if len(sys.argv) > 2 else "balanced"
            vram = float(sys.argv[3]) if len(sys.argv) > 3 else None
            
            recommended = integration.select_best_model(
                priority=priority,
                available_vram_gb=vram
            )
            print(f"\nRecommended model ({priority} priority): {recommended}")
        
        elif command == "summary":
            model_name = sys.argv[2] if len(sys.argv) > 2 else None
            if not model_name:
                print("Usage: python model_performance_integration.py summary <model_name>")
                return
            
            summary = integration.get_model_performance_summary(model_name)
            print(f"\n{'='*60}")
            print(f"PERFORMANCE SUMMARY: {model_name}")
            print('='*60)
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        
        elif command == "insights":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            insights = integration.get_performance_insights(hours)
            
            print(f"\n{'='*60}")
            print(f"PERFORMANCE INSIGHTS (Last {hours} hours)")
            print('='*60)
            print(f"\nModels Analyzed: {insights['models_analyzed']}")
            print(f"Total Operations: {insights['total_operations']}")
            print(f"Overall Success Rate: {insights['overall_success_rate']:.1f}%")
            
            if insights['fastest_model']:
                print(f"\nFastest Model: {insights['fastest_model']['name']} "
                      f"({insights['fastest_model']['avg_time_ms']:.2f}ms)")
            
            if insights['highest_quality_model']:
                print(f"Highest Quality: {insights['highest_quality_model']['name']} "
                      f"({insights['highest_quality_model']['avg_quality']:.2f}/5.0)")
            
            if insights['most_reliable_model']:
                print(f"Most Reliable: {insights['most_reliable_model']['name']} "
                      f"({insights['most_reliable_model']['success_rate']:.1f}%)")
            
            print("\nRecommendations:")
            for priority, model in insights['recommendations'].items():
                print(f"  {priority.capitalize()}: {model}")
            
            if insights['warnings']:
                print("\nWarnings:")
                for warning in insights['warnings']:
                    print(f"  ⚠ {warning}")
    
    else:
        print("Usage:")
        print("  python model_performance_integration.py select [priority] [vram]")
        print("  python model_performance_integration.py summary <model_name>")
        print("  python model_performance_integration.py insights [hours]")


if __name__ == '__main__':
    import json
    main()
