"""
Tests for Model Performance Statistics System

Requirements: 18.5
"""

import pytest
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

from model_performance_stats import (
    ModelPerformanceStatsCollector,
    ModelPerformanceRecord,
    ModelStatistics,
    get_model_performance_stats
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage file."""
    storage_file = tmp_path / "test_model_stats.json"
    return str(storage_file)


@pytest.fixture
def collector(temp_storage):
    """Create test collector instance."""
    return ModelPerformanceStatsCollector(storage_file=temp_storage)


def test_record_model_performance(collector):
    """Test recording model performance."""
    collector.record_model_performance(
        model_name="llama3.1:8b-instruct",
        operation="photo_evaluation",
        processing_time_ms=1234.56,
        quality_score=4.2,
        success=True,
        memory_used_mb=512.0,
        tokens_generated=150,
        photo_id=123,
        job_id="job_abc"
    )
    
    # Verify record was added
    assert "llama3.1:8b-instruct" in collector.records
    assert len(collector.records["llama3.1:8b-instruct"]) == 1
    
    record = collector.records["llama3.1:8b-instruct"][0]
    assert record.model_name == "llama3.1:8b-instruct"
    assert record.operation == "photo_evaluation"
    assert record.processing_time_ms == 1234.56
    assert record.quality_score == 4.2
    assert record.success is True
    assert record.memory_used_mb == 512.0
    assert record.tokens_generated == 150


def test_get_model_statistics(collector):
    """Test getting model statistics."""
    # Record multiple operations
    for i in range(10):
        collector.record_model_performance(
            model_name="llama3.1:8b-instruct",
            operation="photo_evaluation",
            processing_time_ms=1000 + i * 100,
            quality_score=3.5 + i * 0.1,
            success=i < 9  # One failure
        )
    
    stats = collector.get_model_statistics("llama3.1:8b-instruct")
    
    assert stats is not None
    assert stats.model_name == "llama3.1:8b-instruct"
    assert stats.total_operations == 10
    assert stats.successful_operations == 9
    assert stats.failed_operations == 1
    assert stats.success_rate == 90.0
    assert stats.avg_processing_time_ms == pytest.approx(1450.0, rel=0.01)
    assert stats.min_processing_time_ms == 1000.0
    assert stats.max_processing_time_ms == 1900.0
    assert stats.avg_quality_score == pytest.approx(3.95, rel=0.01)


def test_get_all_model_statistics(collector):
    """Test getting statistics for all models."""
    # Record for multiple models
    models = ["llama3.1:8b-instruct", "llama3.1:13b-instruct", "llama3.2:3b-instruct"]
    
    for model in models:
        for i in range(5):
            collector.record_model_performance(
                model_name=model,
                operation="photo_evaluation",
                processing_time_ms=1000 + i * 100,
                quality_score=4.0,
                success=True
            )
    
    all_stats = collector.get_all_model_statistics()
    
    assert len(all_stats) == 3
    for model in models:
        assert model in all_stats
        assert all_stats[model].total_operations == 5


def test_compare_models(collector):
    """Test comparing models."""
    # Record different performance for different models
    collector.record_model_performance(
        model_name="fast_model",
        operation="test",
        processing_time_ms=500,
        quality_score=3.5,
        success=True
    )
    
    collector.record_model_performance(
        model_name="quality_model",
        operation="test",
        processing_time_ms=2000,
        quality_score=4.8,
        success=True
    )
    
    collector.record_model_performance(
        model_name="unreliable_model",
        operation="test",
        processing_time_ms=1000,
        quality_score=4.0,
        success=False
    )
    
    comparison = collector.compare_models(["fast_model", "quality_model", "unreliable_model"])
    
    assert "models" in comparison
    assert "rankings" in comparison
    
    # Check rankings
    assert comparison['rankings']['fastest']['model'] == "fast_model"
    assert comparison['rankings']['highest_quality']['model'] == "quality_model"
    assert comparison['rankings']['most_reliable']['model'] in ["fast_model", "quality_model"]


def test_recommend_model_speed_priority(collector):
    """Test model recommendation with speed priority."""
    # Record performance for multiple models
    collector.record_model_performance(
        model_name="fast_model",
        operation="test",
        processing_time_ms=500,
        quality_score=3.5,
        success=True
    )
    
    for _ in range(10):  # Need min_operations
        collector.record_model_performance(
            model_name="slow_model",
            operation="test",
            processing_time_ms=2000,
            quality_score=4.5,
            success=True
        )
    
    for _ in range(10):
        collector.record_model_performance(
            model_name="fast_model",
            operation="test",
            processing_time_ms=500,
            quality_score=3.5,
            success=True
        )
    
    recommended = collector.recommend_model(priority="speed", min_operations=10)
    assert recommended == "fast_model"


def test_recommend_model_quality_priority(collector):
    """Test model recommendation with quality priority."""
    for _ in range(10):
        collector.record_model_performance(
            model_name="fast_model",
            operation="test",
            processing_time_ms=500,
            quality_score=3.5,
            success=True
        )
    
    for _ in range(10):
        collector.record_model_performance(
            model_name="quality_model",
            operation="test",
            processing_time_ms=2000,
            quality_score=4.8,
            success=True
        )
    
    recommended = collector.recommend_model(priority="quality", min_operations=10)
    assert recommended == "quality_model"


def test_recommend_model_reliable_priority(collector):
    """Test model recommendation with reliable priority."""
    for _ in range(10):
        collector.record_model_performance(
            model_name="reliable_model",
            operation="test",
            processing_time_ms=1000,
            quality_score=4.0,
            success=True
        )
    
    for i in range(10):
        collector.record_model_performance(
            model_name="unreliable_model",
            operation="test",
            processing_time_ms=800,
            quality_score=4.2,
            success=i < 5  # 50% success rate
        )
    
    recommended = collector.recommend_model(priority="reliable", min_operations=10)
    assert recommended == "reliable_model"


def test_get_performance_trend(collector):
    """Test getting performance trend."""
    model_name = "test_model"
    
    # Record performance over time
    for i in range(10):
        collector.record_model_performance(
            model_name=model_name,
            operation="test",
            processing_time_ms=1000 + i * 100,
            quality_score=3.0 + i * 0.1,
            success=True
        )
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    trend = collector.get_model_performance_trend(
        model_name=model_name,
        metric="processing_time",
        hours=1,
        bucket_size_minutes=1
    )
    
    assert 'buckets' in trend
    assert len(trend['buckets']) > 0
    assert trend['model_name'] == model_name
    assert trend['metric'] == "processing_time"


def test_filter_by_duration(collector):
    """Test filtering statistics by duration."""
    model_name = "test_model"
    
    # Record old data
    old_record = ModelPerformanceRecord(
        timestamp=datetime.now() - timedelta(hours=48),
        model_name=model_name,
        operation="test",
        processing_time_ms=1000,
        success=True
    )
    collector.records[model_name].append(old_record)
    
    # Record recent data
    for i in range(5):
        collector.record_model_performance(
            model_name=model_name,
            operation="test",
            processing_time_ms=2000,
            success=True
        )
    
    # Get stats for last 24 hours
    stats = collector.get_model_statistics(model_name, duration_hours=24)
    
    assert stats.total_operations == 5  # Should not include old record


def test_filter_by_operation(collector):
    """Test filtering statistics by operation."""
    model_name = "test_model"
    
    # Record different operations
    for i in range(3):
        collector.record_model_performance(
            model_name=model_name,
            operation="photo_evaluation",
            processing_time_ms=1000,
            success=True
        )
    
    for i in range(2):
        collector.record_model_performance(
            model_name=model_name,
            operation="tag_generation",
            processing_time_ms=500,
            success=True
        )
    
    # Get stats for specific operation
    stats = collector.get_model_statistics(model_name, operation="photo_evaluation")
    
    assert stats.total_operations == 3
    assert stats.avg_processing_time_ms == 1000.0


def test_persistence(temp_storage):
    """Test data persistence."""
    # Create collector and record data
    collector1 = ModelPerformanceStatsCollector(storage_file=temp_storage)
    collector1.record_model_performance(
        model_name="test_model",
        operation="test",
        processing_time_ms=1234.56,
        quality_score=4.2,
        success=True
    )
    
    # Create new collector with same storage
    collector2 = ModelPerformanceStatsCollector(storage_file=temp_storage)
    
    # Verify data was loaded
    assert "test_model" in collector2.records
    assert len(collector2.records["test_model"]) == 1
    assert collector2.records["test_model"][0].processing_time_ms == 1234.56


def test_max_records_limit(collector):
    """Test maximum records limit."""
    collector.max_records_per_model = 10
    model_name = "test_model"
    
    # Record more than max
    for i in range(15):
        collector.record_model_performance(
            model_name=model_name,
            operation="test",
            processing_time_ms=1000,
            success=True
        )
    
    # Should only keep last 10
    assert len(collector.records[model_name]) == 10


def test_export_statistics(collector, tmp_path):
    """Test exporting statistics."""
    # Record some data
    for i in range(5):
        collector.record_model_performance(
            model_name="test_model",
            operation="test",
            processing_time_ms=1000 + i * 100,
            quality_score=4.0,
            success=True
        )
    
    # Export
    export_file = tmp_path / "export.json"
    collector.export_statistics(str(export_file))
    
    # Verify export file exists and contains data
    assert export_file.exists()
    
    with open(export_file, 'r') as f:
        data = json.load(f)
    
    assert 'export_timestamp' in data
    assert 'models' in data
    assert 'test_model' in data['models']


def test_clear_model_data(collector):
    """Test clearing model data."""
    model_name = "test_model"
    
    # Record data
    for i in range(5):
        collector.record_model_performance(
            model_name=model_name,
            operation="test",
            processing_time_ms=1000,
            success=True
        )
    
    assert model_name in collector.records
    
    # Clear data
    collector.clear_model_data(model_name)
    
    assert model_name not in collector.records


def test_clear_old_data(collector):
    """Test clearing old data."""
    model_name = "test_model"
    
    # Record old data
    old_record = ModelPerformanceRecord(
        timestamp=datetime.now() - timedelta(days=60),
        model_name=model_name,
        operation="test",
        processing_time_ms=1000,
        success=True
    )
    collector.records[model_name].append(old_record)
    
    # Record recent data
    for i in range(3):
        collector.record_model_performance(
            model_name=model_name,
            operation="test",
            processing_time_ms=1000,
            success=True
        )
    
    # Clear data older than 30 days
    collector.clear_old_data(days=30)
    
    # Should only have recent data
    assert len(collector.records[model_name]) == 3


def test_token_throughput_calculation(collector):
    """Test token throughput calculation."""
    model_name = "test_model"
    
    # Record with token information
    collector.record_model_performance(
        model_name=model_name,
        operation="test",
        processing_time_ms=1000,  # 1 second
        tokens_generated=100,
        success=True
    )
    
    stats = collector.get_model_statistics(model_name)
    
    assert stats.avg_tokens_per_second == pytest.approx(100.0, rel=0.01)


def test_composite_score_calculation(collector):
    """Test composite score calculation for best overall."""
    # Record balanced model
    for _ in range(10):
        collector.record_model_performance(
            model_name="balanced_model",
            operation="test",
            processing_time_ms=1000,
            quality_score=4.0,
            success=True
        )
    
    # Record fast but lower quality
    for _ in range(10):
        collector.record_model_performance(
            model_name="fast_model",
            operation="test",
            processing_time_ms=500,
            quality_score=3.0,
            success=True
        )
    
    # Record slow but high quality
    for _ in range(10):
        collector.record_model_performance(
            model_name="quality_model",
            operation="test",
            processing_time_ms=2000,
            quality_score=4.8,
            success=True
        )
    
    comparison = collector.compare_models(["balanced_model", "fast_model", "quality_model"])
    
    assert 'best_overall' in comparison['rankings']
    assert comparison['rankings']['best_overall'] is not None
    assert 'composite_score' in comparison['rankings']['best_overall']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
