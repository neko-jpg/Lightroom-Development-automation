"""
Unit tests for EXIF Analyzer Engine.

Tests EXIF metadata extraction, GPS parsing, time of day detection,
and context hint inference.

Requirements: 1.3, 3.1
"""

import pytest
import os
from datetime import datetime, time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from exif_analyzer import EXIFAnalyzer, analyze_photo


class TestEXIFAnalyzer:
    """Test suite for EXIFAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create EXIFAnalyzer instance for testing."""
        return EXIFAnalyzer()
    
    @pytest.fixture
    def mock_exif_tags(self):
        """Create mock EXIF tags for testing."""
        # Create mock tags that return string values when accessed
        make_tag = Mock()
        make_tag.__str__ = Mock(return_value='Canon')
        
        model_tag = Mock()
        model_tag.__str__ = Mock(return_value='Canon EOS R5')
        
        lens_tag = Mock()
        lens_tag.__str__ = Mock(return_value='RF 50mm F1.2 L USM')
        
        iso_tag = Mock()
        iso_tag.__str__ = Mock(return_value='800')
        
        datetime_tag = Mock()
        datetime_tag.__str__ = Mock(return_value='2025:11:08 17:30:00')
        
        exposure_tag = Mock()
        exposure_tag.__str__ = Mock(return_value='1/250')
        
        return {
            'Image Make': make_tag,
            'Image Model': model_tag,
            'EXIF LensModel': lens_tag,
            'EXIF ISOSpeedRatings': iso_tag,
            'EXIF FocalLength': Mock(num=50, den=1),
            'EXIF FNumber': Mock(num=28, den=10),  # f/2.8
            'EXIF ExposureTime': exposure_tag,
            'EXIF DateTimeOriginal': datetime_tag,
            'GPS GPSLatitude': Mock(values=[Mock(num=35, den=1), Mock(num=40, den=1), Mock(num=30, den=1)]),
            'GPS GPSLatitudeRef': Mock(values='N'),
            'GPS GPSLongitude': Mock(values=[Mock(num=139, den=1), Mock(num=45, den=1), Mock(num=15, den=1)]),
            'GPS GPSLongitudeRef': Mock(values='E')
        }
    
    # ========== Initialization Tests ==========
    
    def test_initialization(self, analyzer):
        """Test EXIFAnalyzer initialization."""
        assert analyzer is not None
        assert hasattr(analyzer, 'TIME_OF_DAY_RANGES')
        assert hasattr(analyzer, 'FOCAL_LENGTH_RANGES')
        assert len(analyzer.TIME_OF_DAY_RANGES) > 0
        assert len(analyzer.FOCAL_LENGTH_RANGES) > 0
    
    # ========== Camera Info Extraction Tests ==========
    
    def test_extract_camera_info(self, analyzer, mock_exif_tags):
        """Test camera information extraction."""
        camera_info = analyzer._extract_camera_info(mock_exif_tags)
        
        # The _get_tag_value returns the tag object, which gets converted to string
        assert str(camera_info['make']) == 'Canon'
        assert str(camera_info['model']) == 'Canon EOS R5'
        assert str(camera_info['lens']) == 'RF 50mm F1.2 L USM'
    
    def test_extract_camera_info_missing_fields(self, analyzer):
        """Test camera info extraction with missing fields."""
        tags = {}
        camera_info = analyzer._extract_camera_info(tags)
        
        assert camera_info['make'] is None
        assert camera_info['model'] is None
        assert camera_info['lens'] is None
    
    # ========== Settings Extraction Tests ==========
    
    def test_extract_settings(self, analyzer, mock_exif_tags):
        """Test shooting settings extraction."""
        settings = analyzer._extract_settings(mock_exif_tags)
        
        assert settings['iso'] == 800
        assert settings['focal_length'] == 50.0
        assert settings['aperture'] == 2.8
        assert settings['shutter_speed'] == '1/250'
    
    def test_extract_settings_iso_parsing(self, analyzer):
        """Test ISO value parsing."""
        iso_tag = Mock()
        iso_tag.__str__ = Mock(return_value='1600')
        tags = {'EXIF ISOSpeedRatings': iso_tag}
        settings = analyzer._extract_settings(tags)
        
        assert settings['iso'] == 1600
    
    def test_extract_settings_focal_length_parsing(self, analyzer):
        """Test focal length parsing."""
        # Test rational format
        tags = {'EXIF FocalLength': Mock(num=85, den=1)}
        settings = analyzer._extract_settings(tags)
        assert settings['focal_length'] == 85.0
        
        # Test string format
        tags = {'EXIF FocalLength': '24/1'}
        settings = analyzer._extract_settings(tags)
        assert settings['focal_length'] == 24.0
    
    def test_extract_settings_aperture_parsing(self, analyzer):
        """Test aperture (F-number) parsing."""
        tags = {'EXIF FNumber': Mock(num=18, den=10)}  # f/1.8
        settings = analyzer._extract_settings(tags)
        
        assert settings['aperture'] == 1.8
    
    # ========== GPS Extraction Tests ==========
    
    def test_extract_gps_with_coordinates(self, analyzer, mock_exif_tags):
        """Test GPS extraction with valid coordinates."""
        location = analyzer._extract_gps(mock_exif_tags)
        
        assert location['has_gps'] is True
        assert location['location_type'] == 'outdoor'
        assert location['latitude'] is not None
        assert location['longitude'] is not None
        assert 35.0 < location['latitude'] < 36.0  # Approximate Tokyo latitude
        assert 139.0 < location['longitude'] < 140.0  # Approximate Tokyo longitude
    
    def test_extract_gps_without_coordinates(self, analyzer):
        """Test GPS extraction without coordinates."""
        tags = {}
        location = analyzer._extract_gps(tags)
        
        assert location['has_gps'] is False
        assert location['location_type'] == 'unknown'
        assert location['latitude'] is None
        assert location['longitude'] is None
    
    def test_convert_gps_to_decimal_north_east(self, analyzer):
        """Test GPS coordinate conversion for North/East."""
        # 35°40'30"N = 35.675°
        coord = [Mock(num=35, den=1), Mock(num=40, den=1), Mock(num=30, den=1)]
        ref = 'N'
        
        decimal = analyzer._convert_gps_to_decimal(coord, ref)
        
        assert decimal is not None
        assert abs(decimal - 35.675) < 0.001
    
    def test_convert_gps_to_decimal_south_west(self, analyzer):
        """Test GPS coordinate conversion for South/West."""
        # 35°40'30"S = -35.675°
        coord = [Mock(num=35, den=1), Mock(num=40, den=1), Mock(num=30, den=1)]
        ref = 'S'
        
        decimal = analyzer._convert_gps_to_decimal(coord, ref)
        
        assert decimal is not None
        assert abs(decimal + 35.675) < 0.001
    
    # ========== DateTime Extraction Tests ==========
    
    def test_extract_datetime(self, analyzer, mock_exif_tags):
        """Test datetime extraction and parsing."""
        datetime_info = analyzer._extract_datetime(mock_exif_tags)
        
        assert datetime_info['capture_time'] is not None
        assert isinstance(datetime_info['capture_time'], datetime)
        assert datetime_info['capture_time'].year == 2025
        assert datetime_info['capture_time'].month == 11
        assert datetime_info['capture_time'].day == 8
        assert datetime_info['capture_time'].hour == 17
        assert datetime_info['capture_time'].minute == 30
    
    def test_determine_time_of_day_golden_hour(self, analyzer):
        """Test time of day determination for golden hour."""
        # Evening golden hour: 16:30-18:30
        capture_time = time(17, 30)
        time_of_day = analyzer._determine_time_of_day(capture_time)
        
        assert time_of_day == 'golden_hour_evening'
    
    def test_determine_time_of_day_midday(self, analyzer):
        """Test time of day determination for midday."""
        capture_time = time(12, 30)
        time_of_day = analyzer._determine_time_of_day(capture_time)
        
        assert time_of_day == 'midday'
    
    def test_determine_time_of_day_night(self, analyzer):
        """Test time of day determination for night."""
        capture_time = time(2, 30)
        time_of_day = analyzer._determine_time_of_day(capture_time)
        
        assert time_of_day == 'night'
    
    # ========== Context Hints Inference Tests ==========
    
    def test_infer_context_low_light(self, analyzer):
        """Test context inference for low light conditions."""
        exif_data = {
            'settings': {'iso': 3200, 'focal_length': 50},
            'location': {'location_type': 'unknown', 'has_gps': False},
            'datetime': {'time_of_day': 'night'}
        }
        
        hints = analyzer._infer_context(exif_data)
        
        # ISO 3200 is in the 'low_light' range (1600-3200), not 'very_low_light' (>3200)
        assert hints['lighting'] == 'low_light'
        assert hints.get('likely_indoor') is True
    
    def test_infer_context_portrait(self, analyzer):
        """Test context inference for portrait photography."""
        exif_data = {
            'settings': {'iso': 400, 'focal_length': 85},
            'location': {'location_type': 'outdoor', 'has_gps': True},
            'datetime': {'time_of_day': 'afternoon'}
        }
        
        hints = analyzer._infer_context(exif_data)
        
        assert hints['subject_type'] == 'portrait'
        assert hints['lighting'] == 'good_light'
    
    def test_infer_context_landscape(self, analyzer):
        """Test context inference for landscape photography."""
        exif_data = {
            'settings': {'iso': 200, 'focal_length': 24},
            'location': {'location_type': 'outdoor', 'has_gps': True},
            'datetime': {'time_of_day': 'golden_hour_morning'}
        }
        
        hints = analyzer._infer_context(exif_data)
        
        assert hints['subject_type'] == 'wide'
        assert hints['special_lighting'] == 'golden_hour'
    
    def test_infer_context_backlight_risk(self, analyzer):
        """Test backlight risk detection."""
        exif_data = {
            'settings': {'iso': 800, 'focal_length': 50},
            'location': {'location_type': 'outdoor', 'has_gps': True},
            'datetime': {'time_of_day': 'golden_hour_evening'}
        }
        
        hints = analyzer._infer_context(exif_data)
        
        assert hints.get('backlight_risk') is True
    
    # ========== Rational Value Parsing Tests ==========
    
    def test_parse_rational_with_ratio_object(self, analyzer):
        """Test parsing rational value with ratio object."""
        value = Mock(num=50, den=1)
        result = analyzer._parse_rational(value)
        
        assert result == 50.0
    
    def test_parse_rational_with_string(self, analyzer):
        """Test parsing rational value from string."""
        result = analyzer._parse_rational('24/1')
        assert result == 24.0
        
        result = analyzer._parse_rational('28/10')
        assert result == 2.8
    
    def test_parse_rational_with_zero_denominator(self, analyzer):
        """Test parsing rational value with zero denominator."""
        value = Mock(num=50, den=0)
        result = analyzer._parse_rational(value)
        
        assert result is None
    
    def test_parse_rational_with_invalid_value(self, analyzer):
        """Test parsing invalid rational value."""
        result = analyzer._parse_rational('invalid')
        assert result is None
    
    # ========== Full Analysis Tests ==========
    
    @patch('builtins.open', create=True)
    def test_analyze_success(self, mock_open, analyzer, mock_exif_tags):
        """Test successful photo analysis."""
        with patch('exif_analyzer.exifread') as mock_exifread:
            mock_exifread.process_file.return_value = mock_exif_tags
            mock_open.return_value.__enter__.return_value = MagicMock()
            
            # Create a temporary test file
            test_file = 'test_photo.jpg'
            
            with patch('os.path.exists', return_value=True), \
                 patch('exif_analyzer.EXIFREAD_AVAILABLE', True):
                result = analyzer.analyze(test_file)
            
            assert 'camera' in result
            assert 'settings' in result
            assert 'location' in result
            assert 'datetime' in result
            assert 'context_hints' in result
    
    def test_analyze_file_not_found(self, analyzer):
        """Test analysis with non-existent file."""
        with pytest.raises(FileNotFoundError):
            analyzer.analyze('nonexistent_file.jpg')
    
    @patch('exif_analyzer.EXIFREAD_AVAILABLE', False)
    def test_analyze_without_exifread(self, analyzer):
        """Test analysis when exifread is not available."""
        with patch('os.path.exists', return_value=True):
            result = analyzer.analyze('test_photo.jpg')
        
        # Should return empty result
        assert result['camera'] == {}
        assert result['settings'] == {}
        assert result['location'] == {}
        assert result['datetime'] == {}
    
    # ========== Database Export Tests ==========
    
    @patch('builtins.open', create=True)
    def test_extract_for_database(self, mock_open, analyzer, mock_exif_tags):
        """Test database-ready EXIF extraction."""
        with patch('exif_analyzer.exifread') as mock_exifread:
            mock_exifread.process_file.return_value = mock_exif_tags
            mock_open.return_value.__enter__.return_value = MagicMock()
            
            test_file = 'test_photo.jpg'
            
            with patch('os.path.exists', return_value=True), \
                 patch('exif_analyzer.EXIFREAD_AVAILABLE', True):
                db_data = analyzer.extract_for_database(test_file)
            
            # Check database fields
            assert 'camera_make' in db_data
            assert 'camera_model' in db_data
            assert 'lens' in db_data
            assert 'focal_length' in db_data
            assert 'aperture' in db_data
            assert 'shutter_speed' in db_data
            assert 'iso' in db_data
            assert 'capture_time' in db_data
            assert 'gps_lat' in db_data
            assert 'gps_lon' in db_data
    
    # ========== Convenience Function Tests ==========
    
    @patch('exif_analyzer.EXIFAnalyzer.analyze')
    def test_analyze_photo_convenience_function(self, mock_analyze):
        """Test convenience function for photo analysis."""
        mock_analyze.return_value = {'test': 'data'}
        
        result = analyze_photo('test.jpg')
        
        assert result == {'test': 'data'}
        mock_analyze.assert_called_once_with('test.jpg')


class TestEXIFAnalyzerIntegration:
    """Integration tests for EXIF Analyzer with real-world scenarios."""
    
    @pytest.fixture
    def analyzer(self):
        """Create EXIFAnalyzer instance."""
        return EXIFAnalyzer()
    
    def test_portrait_scenario(self, analyzer):
        """Test portrait photography scenario."""
        exif_data = {
            'camera': {'make': 'Canon', 'model': 'EOS R5'},
            'settings': {
                'iso': 800,  # Need ISO > 400 for backlight risk
                'focal_length': 85.0,
                'aperture': 1.8,
                'shutter_speed': '1/200'
            },
            'location': {
                'latitude': 35.6762,
                'longitude': 139.6503,
                'location_type': 'outdoor',
                'has_gps': True
            },
            'datetime': {
                'capture_time': datetime(2025, 11, 8, 17, 30),
                'time_of_day': 'golden_hour_evening'
            }
        }
        
        hints = analyzer._infer_context(exif_data)
        
        assert hints['subject_type'] == 'portrait'
        assert hints['lighting'] == 'moderate_light'  # ISO 800 is moderate
        assert hints['special_lighting'] == 'golden_hour'
        assert hints.get('backlight_risk') is True
    
    def test_indoor_event_scenario(self, analyzer):
        """Test indoor event photography scenario."""
        exif_data = {
            'settings': {
                'iso': 3200,
                'focal_length': 35.0,
                'aperture': 2.0
            },
            'location': {
                'location_type': 'unknown',
                'has_gps': False
            },
            'datetime': {
                'time_of_day': 'evening'
            }
        }
        
        hints = analyzer._infer_context(exif_data)
        
        # ISO 3200 is in the 'low_light' range (1600-3200), not 'very_low_light' (>3200)
        assert hints['lighting'] == 'low_light'
        assert hints['subject_type'] == 'standard'
        assert hints.get('likely_indoor') is True
    
    def test_landscape_scenario(self, analyzer):
        """Test landscape photography scenario."""
        exif_data = {
            'settings': {
                'iso': 100,
                'focal_length': 16.0,
                'aperture': 11.0
            },
            'location': {
                'location_type': 'outdoor',
                'has_gps': True
            },
            'datetime': {
                'time_of_day': 'golden_hour_morning'
            }
        }
        
        hints = analyzer._infer_context(exif_data)
        
        assert hints['subject_type'] == 'ultra_wide'
        assert hints['lighting'] == 'good_light'
        assert hints['special_lighting'] == 'golden_hour'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
