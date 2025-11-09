"""
Model-Specific Performance Statistics System

Tracks and analyzes performance metrics for individual LLM models including:
- Model-specific processing time recording
- Model-specific quality score tracking
- Recommended model selection logic based on performance
- Comparative analysis between models

Requirements: 18.5
"""

import logging
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """Types of performance metrics tracked per model."""
    PROCESSING_TIME = "processing_time"
    QUALITY_SCORE = "quality_score"
    SUCCESS_RATE = "success_rate"
    MEMORY_USAGE = "memory_usage"
    TOKEN_THROUGHPUT = "token_throughput"


@dataclass
class ModelPerformanceRecord:
    """Individual performance record for a model."""
    timestamp: datetime
    model_name: str
    operation: str
    processing_time_ms: float
    quality_score: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    memory_used_mb: Optional[float] = None
    tokens_generated: Optional[int] = None
    photo_id: Optional[int] = None
    job_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'model_name': self.model_name,
            'operation': self.operation,
            'processing_time_ms': self.processing_time_ms,
            'quality_score': self.quality_score,
            'success': self.success,
            'error_message': self.error_message,
            'memory_used_mb': self.memory_used_mb,
            'tokens_generated': self.tokens_generated,
            'photo_id': self.photo_id,
            'job_id': self.job_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelPerformanceRecord':
        """Create from dictionary."""
        data = data.copy()
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ModelStatistics:
    """Aggregated statistics for a model."""
    model_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    success_rate: float
    avg_processing_time_ms: float
    min_processing_time_ms: float
    max_processing_time_ms: float
    median_processing_time_ms: float
    avg_quality_score: Optional[float] = None
    min_quality_score: Optional[float] = None
    max_quality_score: Optional[float] = None
    avg_memory_used_mb: Optional[float] = None
    avg_tokens_per_second: Optional[float] = None
    last_used: Optional[datetime] = None
    first_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        if self.last_used:
            data['last_used'] = self.last_used.isoformat()
        if self.first_used:
            data['first_used'] = self.first_used.isoformat()
        return data


class ModelPerformanceStatsCollector:
    """
    Model-specific performance statistics collector.
    
    Features:
    - Track processing time per model
    - Track quality scores per model
    - Calculate model-specific statistics
    - Recommend best model based on performance
    - Compare models side-by-side
    
    Requirements: 18.5
    """
    
    def __init__(
        self,
        storage_file: str = "data/model_performance_stats.json",
        max_records_per_model: int = 1000
    ):
        """
        Initialize model performance stats collector.
        
        Args:
            storage_file: Path to storage file
            max_records_per_model: Maximum records to keep per model
        """
        self.storage_file = Path(storage_file)
        self.max_records_per_model = max_records_per_model
        
        # Performance records by model
        self.records: Dict[str, List[ModelPerformanceRecord]] = defaultdict(list)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Load existing data
        self._load_data()
        
        logger.info(f"Model performance stats collector initialized (storage={storage_file})")
    
    def _load_data(self):
        """Load performance data from storage file."""
        if not self.storage_file.exists():
            logger.info("No existing performance data found")
            return
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load records
            for model_name, records_data in data.get('records', {}).items():
                self.records[model_name] = [
                    ModelPerformanceRecord.from_dict(r) for r in records_data
                ]
            
            total_records = sum(len(records) for records in self.records.values())
            logger.info(f"Loaded {total_records} performance records for {len(self.records)} models")
        
        except Exception as e:
            logger.error(f"Error loading performance data: {e}")
    
    def _save_data(self):
        """Save performance data to storage file."""
        try:
            # Ensure directory exists
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'records': {
                    model_name: [r.to_dict() for r in records]
                    for model_name, records in self.records.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Performance data saved")
        
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
    
    def record_model_performance(
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
        Record performance metrics for a model.
        
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
            
        Requirements: 18.5
        """
        record = ModelPerformanceRecord(
            timestamp=datetime.now(),
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
        
        with self.lock:
            self.records[model_name].append(record)
            
            # Trim if exceeds max
            if len(self.records[model_name]) > self.max_records_per_model:
                self.records[model_name] = self.records[model_name][-self.max_records_per_model:]
            
            self._save_data()
        
        logger.debug(
            f"Recorded performance for {model_name}: "
            f"{processing_time_ms:.2f}ms, success={success}"
        )
    
    def get_model_statistics(
        self,
        model_name: str,
        duration_hours: Optional[int] = None,
        operation: Optional[str] = None
    ) -> Optional[ModelStatistics]:
        """
        Get aggregated statistics for a model.
        
        Args:
            model_name: Name of the model
            duration_hours: Only include records from last N hours
            operation: Filter by operation type
            
        Returns:
            Model statistics or None if no data
            
        Requirements: 18.5
        """
        with self.lock:
            if model_name not in self.records:
                return None
            
            records = self.records[model_name].copy()
        
        # Filter by duration
        if duration_hours:
            cutoff = datetime.now() - timedelta(hours=duration_hours)
            records = [r for r in records if r.timestamp >= cutoff]
        
        # Filter by operation
        if operation:
            records = [r for r in records if r.operation == operation]
        
        if not records:
            return None
        
        # Calculate statistics
        successful = [r for r in records if r.success]
        failed = [r for r in records if not r.success]
        
        processing_times = [r.processing_time_ms for r in records]
        processing_times_sorted = sorted(processing_times)
        
        quality_scores = [r.quality_score for r in records if r.quality_score is not None]
        memory_usages = [r.memory_used_mb for r in records if r.memory_used_mb is not None]
        
        # Calculate token throughput
        token_throughputs = []
        for r in records:
            if r.tokens_generated and r.processing_time_ms > 0:
                tokens_per_second = (r.tokens_generated / r.processing_time_ms) * 1000
                token_throughputs.append(tokens_per_second)
        
        stats = ModelStatistics(
            model_name=model_name,
            total_operations=len(records),
            successful_operations=len(successful),
            failed_operations=len(failed),
            success_rate=(len(successful) / len(records) * 100) if records else 0,
            avg_processing_time_ms=sum(processing_times) / len(processing_times),
            min_processing_time_ms=min(processing_times),
            max_processing_time_ms=max(processing_times),
            median_processing_time_ms=processing_times_sorted[len(processing_times_sorted) // 2],
            avg_quality_score=sum(quality_scores) / len(quality_scores) if quality_scores else None,
            min_quality_score=min(quality_scores) if quality_scores else None,
            max_quality_score=max(quality_scores) if quality_scores else None,
            avg_memory_used_mb=sum(memory_usages) / len(memory_usages) if memory_usages else None,
            avg_tokens_per_second=sum(token_throughputs) / len(token_throughputs) if token_throughputs else None,
            last_used=records[-1].timestamp,
            first_used=records[0].timestamp
        )
        
        return stats
    
    def get_all_model_statistics(
        self,
        duration_hours: Optional[int] = None,
        operation: Optional[str] = None
    ) -> Dict[str, ModelStatistics]:
        """
        Get statistics for all models.
        
        Args:
            duration_hours: Only include records from last N hours
            operation: Filter by operation type
            
        Returns:
            Dictionary mapping model names to statistics
            
        Requirements: 18.5
        """
        with self.lock:
            model_names = list(self.records.keys())
        
        stats = {}
        for model_name in model_names:
            model_stats = self.get_model_statistics(model_name, duration_hours, operation)
            if model_stats:
                stats[model_name] = model_stats
        
        return stats
    
    def compare_models(
        self,
        model_names: List[str],
        duration_hours: Optional[int] = None,
        operation: Optional[str] = None
    ) -> Dict:
        """
        Compare performance between multiple models.
        
        Args:
            model_names: List of model names to compare
            duration_hours: Only include records from last N hours
            operation: Filter by operation type
            
        Returns:
            Comparison dictionary with rankings
            
        Requirements: 18.5
        """
        comparison = {
            'models': {},
            'rankings': {
                'fastest': None,
                'highest_quality': None,
                'most_reliable': None,
                'best_overall': None
            }
        }
        
        # Get statistics for each model
        for model_name in model_names:
            stats = self.get_model_statistics(model_name, duration_hours, operation)
            if stats:
                comparison['models'][model_name] = stats.to_dict()
        
        if not comparison['models']:
            return comparison
        
        # Determine rankings
        models_with_stats = list(comparison['models'].items())
        
        # Fastest (lowest avg processing time)
        fastest = min(
            models_with_stats,
            key=lambda x: x[1]['avg_processing_time_ms']
        )
        comparison['rankings']['fastest'] = {
            'model': fastest[0],
            'avg_time_ms': fastest[1]['avg_processing_time_ms']
        }
        
        # Highest quality (highest avg quality score)
        models_with_quality = [
            (name, stats) for name, stats in models_with_stats
            if stats['avg_quality_score'] is not None
        ]
        if models_with_quality:
            highest_quality = max(
                models_with_quality,
                key=lambda x: x[1]['avg_quality_score']
            )
            comparison['rankings']['highest_quality'] = {
                'model': highest_quality[0],
                'avg_quality': highest_quality[1]['avg_quality_score']
            }
        
        # Most reliable (highest success rate)
        most_reliable = max(
            models_with_stats,
            key=lambda x: x[1]['success_rate']
        )
        comparison['rankings']['most_reliable'] = {
            'model': most_reliable[0],
            'success_rate': most_reliable[1]['success_rate']
        }
        
        # Best overall (composite score)
        best_overall = self._calculate_best_overall(models_with_stats)
        if best_overall:
            comparison['rankings']['best_overall'] = best_overall
        
        return comparison
    
    def _calculate_best_overall(
        self,
        models_with_stats: List[Tuple[str, Dict]]
    ) -> Optional[Dict]:
        """
        Calculate best overall model based on composite score.
        
        Args:
            models_with_stats: List of (model_name, stats_dict) tuples
            
        Returns:
            Best overall model info or None
        """
        if not models_with_stats:
            return None
        
        scores = []
        
        for model_name, stats in models_with_stats:
            # Normalize metrics to 0-1 scale
            
            # Speed score (inverse of processing time, normalized)
            all_times = [s[1]['avg_processing_time_ms'] for s in models_with_stats]
            min_time = min(all_times)
            max_time = max(all_times)
            if max_time > min_time:
                speed_score = 1 - ((stats['avg_processing_time_ms'] - min_time) / (max_time - min_time))
            else:
                speed_score = 1.0
            
            # Quality score (normalized to 0-1)
            quality_score = 0.0
            if stats['avg_quality_score'] is not None:
                quality_score = (stats['avg_quality_score'] - 1.0) / 4.0  # 1-5 scale to 0-1
            
            # Reliability score (success rate as 0-1)
            reliability_score = stats['success_rate'] / 100.0
            
            # Composite score (weighted average)
            # Weights: speed=30%, quality=40%, reliability=30%
            composite = (
                speed_score * 0.3 +
                quality_score * 0.4 +
                reliability_score * 0.3
            )
            
            scores.append((model_name, composite, {
                'speed_score': speed_score,
                'quality_score': quality_score,
                'reliability_score': reliability_score
            }))
        
        # Get best
        best = max(scores, key=lambda x: x[1])
        
        return {
            'model': best[0],
            'composite_score': best[1],
            'component_scores': best[2]
        }
    
    def recommend_model(
        self,
        priority: str = "balanced",
        available_models: Optional[List[str]] = None,
        duration_hours: Optional[int] = 24,
        min_operations: int = 10
    ) -> Optional[str]:
        """
        Recommend best model based on performance history and priority.
        
        Args:
            priority: Priority ("speed", "quality", "balanced", "reliable")
            available_models: List of available models (None = all)
            duration_hours: Consider performance from last N hours
            min_operations: Minimum operations required for recommendation
            
        Returns:
            Recommended model name or None
            
        Requirements: 18.5
        """
        # Get statistics for all models
        all_stats = self.get_all_model_statistics(duration_hours)
        
        # Filter by available models
        if available_models:
            all_stats = {
                name: stats for name, stats in all_stats.items()
                if name in available_models
            }
        
        # Filter by minimum operations
        all_stats = {
            name: stats for name, stats in all_stats.items()
            if stats.total_operations >= min_operations
        }
        
        if not all_stats:
            logger.warning("No models with sufficient performance history")
            return None
        
        # Select based on priority
        if priority == "speed":
            # Fastest model
            best = min(
                all_stats.items(),
                key=lambda x: x[1].avg_processing_time_ms
            )
            logger.info(f"Recommended model (speed): {best[0]} ({best[1].avg_processing_time_ms:.2f}ms avg)")
            return best[0]
        
        elif priority == "quality":
            # Highest quality model
            models_with_quality = {
                name: stats for name, stats in all_stats.items()
                if stats.avg_quality_score is not None
            }
            if not models_with_quality:
                logger.warning("No models with quality scores")
                return None
            
            best = max(
                models_with_quality.items(),
                key=lambda x: x[1].avg_quality_score
            )
            logger.info(f"Recommended model (quality): {best[0]} ({best[1].avg_quality_score:.2f} avg)")
            return best[0]
        
        elif priority == "reliable":
            # Most reliable model
            best = max(
                all_stats.items(),
                key=lambda x: x[1].success_rate
            )
            logger.info(f"Recommended model (reliable): {best[0]} ({best[1].success_rate:.1f}% success)")
            return best[0]
        
        else:  # balanced
            # Best overall composite score
            models_list = list(all_stats.items())
            models_with_dicts = [(name, stats.to_dict()) for name, stats in models_list]
            best_overall = self._calculate_best_overall(models_with_dicts)
            
            if best_overall:
                logger.info(
                    f"Recommended model (balanced): {best_overall['model']} "
                    f"(composite={best_overall['composite_score']:.3f})"
                )
                return best_overall['model']
            
            return None
    
    def get_model_performance_trend(
        self,
        model_name: str,
        metric: str = "processing_time",
        hours: int = 24,
        bucket_size_minutes: int = 60
    ) -> Dict:
        """
        Get performance trend over time for a model.
        
        Args:
            model_name: Name of the model
            metric: Metric to track ("processing_time", "quality_score", "success_rate")
            hours: Number of hours to analyze
            bucket_size_minutes: Size of time buckets in minutes
            
        Returns:
            Trend data with time buckets
        """
        with self.lock:
            if model_name not in self.records:
                return {'error': 'Model not found'}
            
            records = self.records[model_name].copy()
        
        # Filter by time range
        cutoff = datetime.now() - timedelta(hours=hours)
        records = [r for r in records if r.timestamp >= cutoff]
        
        if not records:
            return {'error': 'No data in time range'}
        
        # Create time buckets
        bucket_size = timedelta(minutes=bucket_size_minutes)
        start_time = records[0].timestamp
        end_time = records[-1].timestamp
        
        buckets = []
        current_time = start_time
        
        while current_time <= end_time:
            bucket_end = current_time + bucket_size
            bucket_records = [
                r for r in records
                if current_time <= r.timestamp < bucket_end
            ]
            
            if bucket_records:
                if metric == "processing_time":
                    value = sum(r.processing_time_ms for r in bucket_records) / len(bucket_records)
                elif metric == "quality_score":
                    quality_records = [r for r in bucket_records if r.quality_score is not None]
                    value = sum(r.quality_score for r in quality_records) / len(quality_records) if quality_records else None
                elif metric == "success_rate":
                    successful = sum(1 for r in bucket_records if r.success)
                    value = (successful / len(bucket_records)) * 100
                else:
                    value = None
                
                buckets.append({
                    'timestamp': current_time.isoformat(),
                    'value': value,
                    'count': len(bucket_records)
                })
            
            current_time = bucket_end
        
        return {
            'model_name': model_name,
            'metric': metric,
            'hours': hours,
            'bucket_size_minutes': bucket_size_minutes,
            'buckets': buckets
        }
    
    def export_statistics(self, output_file: str):
        """
        Export all model statistics to a file.
        
        Args:
            output_file: Output file path
        """
        try:
            all_stats = self.get_all_model_statistics()
            
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'models': {
                    name: stats.to_dict()
                    for name, stats in all_stats.items()
                },
                'comparison': self.compare_models(list(all_stats.keys()))
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Statistics exported to: {output_file}")
        
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}")
    
    def clear_model_data(self, model_name: str):
        """
        Clear performance data for a specific model.
        
        Args:
            model_name: Name of the model
        """
        with self.lock:
            if model_name in self.records:
                count = len(self.records[model_name])
                del self.records[model_name]
                self._save_data()
                logger.info(f"Cleared {count} records for model: {model_name}")
    
    def clear_old_data(self, days: int = 30):
        """
        Clear performance data older than specified days.
        
        Args:
            days: Number of days to keep
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            total_removed = 0
            
            for model_name in list(self.records.keys()):
                original_count = len(self.records[model_name])
                self.records[model_name] = [
                    r for r in self.records[model_name]
                    if r.timestamp >= cutoff
                ]
                removed = original_count - len(self.records[model_name])
                total_removed += removed
                
                # Remove model if no records left
                if not self.records[model_name]:
                    del self.records[model_name]
            
            self._save_data()
            logger.info(f"Cleared {total_removed} old records (older than {days} days)")


# Global instance
_model_performance_stats = None


def get_model_performance_stats() -> ModelPerformanceStatsCollector:
    """Get global model performance stats collector instance."""
    global _model_performance_stats
    if _model_performance_stats is None:
        _model_performance_stats = ModelPerformanceStatsCollector()
    return _model_performance_stats


def main():
    """Example usage of Model Performance Stats."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = get_model_performance_stats()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            model_name = sys.argv[2] if len(sys.argv) > 2 else None
            
            if model_name:
                # Show stats for specific model
                stats = collector.get_model_statistics(model_name)
                if stats:
                    print(f"\n{'='*60}")
                    print(f"STATISTICS FOR {model_name}")
                    print('='*60)
                    print(f"Total Operations: {stats.total_operations}")
                    print(f"Success Rate: {stats.success_rate:.1f}%")
                    print(f"Avg Processing Time: {stats.avg_processing_time_ms:.2f}ms")
                    print(f"Min/Max Time: {stats.min_processing_time_ms:.2f}ms / {stats.max_processing_time_ms:.2f}ms")
                    if stats.avg_quality_score:
                        print(f"Avg Quality Score: {stats.avg_quality_score:.2f}/5.0")
                    if stats.avg_memory_used_mb:
                        print(f"Avg Memory Used: {stats.avg_memory_used_mb:.2f}MB")
                    if stats.avg_tokens_per_second:
                        print(f"Avg Tokens/Second: {stats.avg_tokens_per_second:.2f}")
                else:
                    print(f"No statistics found for model: {model_name}")
            else:
                # Show stats for all models
                all_stats = collector.get_all_model_statistics()
                print(f"\n{'='*60}")
                print("ALL MODEL STATISTICS")
                print('='*60)
                for name, stats in all_stats.items():
                    print(f"\n{name}:")
                    print(f"  Operations: {stats.total_operations}")
                    print(f"  Success Rate: {stats.success_rate:.1f}%")
                    print(f"  Avg Time: {stats.avg_processing_time_ms:.2f}ms")
                    if stats.avg_quality_score:
                        print(f"  Avg Quality: {stats.avg_quality_score:.2f}/5.0")
        
        elif command == "compare":
            models = sys.argv[2:] if len(sys.argv) > 2 else []
            if not models:
                print("Usage: python model_performance_stats.py compare <model1> <model2> ...")
                return
            
            comparison = collector.compare_models(models)
            print(f"\n{'='*60}")
            print("MODEL COMPARISON")
            print('='*60)
            
            print("\nRankings:")
            for category, info in comparison['rankings'].items():
                if info:
                    print(f"  {category.replace('_', ' ').title()}: {info['model']}")
        
        elif command == "recommend":
            priority = sys.argv[2] if len(sys.argv) > 2 else "balanced"
            recommended = collector.recommend_model(priority=priority)
            print(f"\nRecommended model ({priority} priority): {recommended}")
        
        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else "model_stats_export.json"
            collector.export_statistics(output_file)
            print(f"Statistics exported to: {output_file}")
    
    else:
        print("Usage:")
        print("  python model_performance_stats.py stats [model_name]  - Show statistics")
        print("  python model_performance_stats.py compare <models...> - Compare models")
        print("  python model_performance_stats.py recommend [priority] - Recommend model")
        print("  python model_performance_stats.py export [file]        - Export statistics")


if __name__ == '__main__':
    main()
