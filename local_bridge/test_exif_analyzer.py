"""
Unit tests for EXIF Analyzer Engine.

Tests cover:
- Metadata extraction from various image formats
- Camera settings parsing
- GPS location parsing and indoor/outdoor detection
- Time of day detection
- Context hints inference
"""

import unittest
import os
import tempfile
from datetime import datetime, time
from unittest.mock import Mock, patch, MagicMock
from exif_analyzer import EXIFAnalyzer, analyze_photo


class TestEXIFAnalyzer(unittest.TestCase):
    """Test cases for EXIFAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = EXIFAnalyzer()
    
    def test_initialization(self):
        """Test analyzer initialization"""
        self.assertIsNotNone(self.analyzer)
        self.assertIsInstance(self.analyzer.TIME_OF_DAY_RANGES, dict)
        self.assertIsInstance(self.analyzer.FOCAL_LENGTH_RANGES, dict)
    
    def test_empty_result_structure(self):
        """Test empty result structure"""
        result = self.analyzer._empty_result()
        
        self.assertIn('camera', result)
        self.assertIn('settings', result)
        self.assertIn('location', result)
        self.assertIn('datetime', result)
        self.assertIn('context_hints', result)
    
    def test_time_of_day_detection(self):
        """Test time of day detection from capture time"""
        test_cases = [
            (time(3, 0), 'night'),
            (time(6, 0), 'blue_hour_morning'),
            (time(7, 0), 'golden_hour_morning'),
            (time(10, 0), 'morning'),
            (time(12, 0), 'midday'),
            (time(15, 0), 'afternoon'),
            (time(17, 0), 'golden_hour_evening'),
            (time(19, 0), 'blue_hour_evening'),
            (time(22, 0), 'evening')
        ]
        
        for test_time, expected_period in test_cases:
            result = self.analyzer._determine_time_of_day(test_time)
            self.assertEqual(result, expected_period, 
                           f"Time {test_time} should be {expected_period}, got {result}")
    
    def test_parse_rational_with_fraction(self):
        """Test parsing rational values in fraction format"""
        # Mock exifread.Ratio object
        mock_ratio = Mock()
        mock_ratio.num = 50
        mock_ratio.den = 10
        
        result = self.analyzer._parse_rational(mock_ratio)
        self.assertEqual(result, 5.0)
    
    def test_parse_rational_with_string(self):
        """Test parsing rational values as strings"""
        test_cases = [
            ("24/1", 24.0),
            ("50/10", 5.0),
            ("1/100", 0.01),
            ("28", 28.0)
        ]
        
        for input_val, expected in test_cases:
            result = self.analyzer._parse_rational(input_val)
            self.assertAlmostEqual(result, expected, places=5)
    
    def test_parse_rational_with_zero_denominator(self):
        """Test handling of zero denominator"""
        mock_ratio = Mock()
        mock_ratio.num = 50
        mock_ratio.den = 0
        
        result = self.analyzer._parse_rational(mock_ratio)
        self.assertIsNone(result)
    
    def test_gps_conversion_to_decimal(self):
        """Test GPS coordinate conversion from DMS to decimal"""
        # Mock GPS coordinate: 35°41'22" N
        mock_coord = Mock()
        mock_coord.values = [
            Mock(num=35, den=1),  # degrees
            Mock(num=41, den=1),  # minutes
            Mock(num=22, den=1)   # seconds
        ]
        
        result = self.analyzer._convert_gps_to_decimal(mock_coord, 'N')
        expected = 35 + (41/60.0) + (22/3600.0)
        self.assertAlmostEqual(result, expected, places=5)
    
    def test_gps_conversion_south_hemisphere(self):
        """Test GPS conversion for southern hemisphere (negative)"""
        mock_coord = Mock()
        mock_coord.values = [
            Mock(num=33, den=1),
            Mock(num=55, den=1),
            Mock(num=30, den=1)
        ]
        
        result = self.analyzer._convert_gps_to_decimal(mock_coord, 'S')
        self.assertLess(result, 0, "Southern latitude should be negative")
    
    def test_extract_camera_info(self):
        """Test camera information extraction"""
        mock_tags = {
            'Image Make': 'Canon',
            'Image Model': 'Canon EOS R5',
            'EXIF LensModel': 'RF24-105mm F4 L IS USM'
        }
        
        result = self.analyzer._extract_camera_info(mock_tags)
        
        self.assertEqual(result['make'], 'Canon')
        self.assertEqual(result['model'], 'Canon EOS R5')
        self.assertEqual(result['lens'], 'RF24-105mm F4 L IS USM')
    
    def test_extract_settings(self):
        """Test camera settings extraction"""
        mock_tags = {
            'EXIF ISOSpeedRatings': '1600',
            'EXIF FocalLength': Mock(num=50, den=1),
            'EXIF FNumber': Mock(num=28, den=10),  # f/2.8
            'EXIF ExposureTime': '1/250'
        }
        
        result = self.analyzer._extract_settings(mock_tags)
        
        self.assertEqual(result['iso'], 1600)
        self.assertEqual(result['focal_length'], 50.0)
        self.assertAlmostEqual(result['aperture'], 2.8, places=1)
        self.assertEqual(result['shutter_speed'], '1/250')
    
    def test_extract_gps_with_coordinates(self):
        """Test GPS extraction with valid coordinates"""
        mock_lat = Mock()
        mock_lat.values = [Mock(num=35, den=1), Mock(num=41, den=1), Mock(num=0, den=1)]
        
        mock_lon = Mock()
        mock_lon.values = [Mock(num=139, den=1), Mock(num=45, den=1), Mock(num=0, den=1)]
        
        mock_tags = {
            'GPS GPSLatitude': mock_lat,
            'GPS GPSLatitudeRef': 'N',
            'GPS GPSLongitude': mock_lon,
            'GPS GPSLongitudeRef': 'E'
        }
        
        result = self.analyzer._extract_gps(mock_tags)
        
        self.assertIsNotNone(result['latitude'])
        self.assertIsNotNone(result['longitude'])
        self.assertTrue(result['has_gps'])
        self.assertEqual(result['location_type'], 'outdoor')
    
    def test_extract_gps_without_coordinates(self):
        """Test GPS extraction without coordinates (indoor detection)"""
        mock_tags = {}
        
        result = self.analyzer._extract_gps(mock_tags)
        
        self.assertIsNone(result['latitude'])
        self.assertIsNone(result['longitude'])
        self.assertFalse(result['has_gps'])
        self.assertEqual(result['location_type'], 'unknown')
    
    def test_extract_datetime(self):
        """Test datetime extraction and parsing"""
        mock_tags = {
            'EXIF DateTimeOriginal': '2025:11:08 14:30:45'
        }
        
        result = self.analyzer._extract_datetime(mock_tags)
        
        self.assertIsNotNone(result['capture_time'])
        self.assertIsInstance(result['capture_time'], datetime)
        self.assertEqual(result['capture_time'].year, 2025)
        self.assertEqual(result['capture_time'].month, 11)
        self.assertEqual(result['capture_time'].day, 8)
        self.assertEqual(result['time_of_day'], 'afternoon')
    
    def test_infer_context_low_light(self):
        """Test context inference for low light conditions"""
        exif_data = {
            'settings': {'iso': 3200, 'focal_length': 50},
            'location': {'location_type': 'unknown', 'has_gps': False},
            'datetime': {'time_of_day': 'evening'}
        }
        
        hints = self.analyzer._infer_context(exif_data)
        
        self.assertEqual(hints['lighting'], 'low_light')
        self.assertTrue(hints.get('likely_indoor', False))
    
    def test_infer_context_portrait(self):
        """Test context inference for portrait photography"""
        exif_data = {
            'settings': {'iso': 800, 'focal_length': 85},  # Increased ISO to trigger backlight risk
            'location': {'location_type': 'outdoor', 'has_gps': True},
            'datetime': {'time_of_day': 'golden_hour_evening'}
        }
        
        hints = self.analyzer._infer_context(exif_data)
        
        self.assertEqual(hints['subject_type'], 'portrait')
        self.assertEqual(hints['special_lighting'], 'golden_hour')
        self.assertTrue(hints.get('backlight_risk', False))
    
    def test_infer_context_landscape(self):
        """Test context inference for landscape photography"""
        exif_data = {
            'settings': {'iso': 100, 'focal_length': 24},
            'location': {'location_type': 'outdoor', 'has_gps': True},
            'datetime': {'time_of_day': 'morning'}
        }
        
        hints = self.analyzer._infer_context(exif_data)
        
        self.assertEqual(hints['subject_type'], 'wide')
        self.assertEqual(hints['lighting'], 'good_light')
    
    def test_extract_for_database(self):
        """Test extraction formatted for database storage"""
        with patch.object(self.analyzer, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                'camera': {
                    'make': 'Canon',
                    'model': 'EOS R5',
                    'lens': 'RF24-105mm'
                },
                'settings': {
                    'iso': 800,
                    'focal_length': 50.0,
                    'aperture': 2.8,
                    'shutter_speed': '1/250'
                },
                'location': {
                    'latitude': 35.6895,
                    'longitude': 139.6917
                },
                'datetime': {
                    'capture_time': datetime(2025, 11, 8, 14, 30)
                }
            }
            
            result = self.analyzer.extract_for_database('test.jpg')
            
            self.assertEqual(result['camera_make'], 'Canon')
            self.assertEqual(result['camera_model'], 'EOS R5')
            self.assertEqual(result['lens'], 'RF24-105mm')
            self.assertEqual(result['iso'], 800)
            self.assertEqual(result['focal_length'], 50.0)
            self.assertAlmostEqual(result['aperture'], 2.8, places=1)
            self.assertEqual(result['shutter_speed'], '1/250')
            self.assertAlmostEqual(result['gps_lat'], 35.6895, places=4)
            self.assertAlmostEqual(result['gps_lon'], 139.6917, places=4)
    
    def test_analyze_nonexistent_file(self):
        """Test handling of nonexistent file"""
        with self.assertRaises(FileNotFoundError):
            self.analyzer.analyze('nonexistent_file.jpg')
    
    def test_get_tag_value(self):
        """Test safe tag value retrieval"""
        tags = {'TestTag': 'TestValue'}
        
        result = self.analyzer._get_tag_value(tags, 'TestTag')
        self.assertEqual(result, 'TestValue')
        
        result = self.analyzer._get_tag_value(tags, 'NonExistentTag')
        self.assertIsNone(result)
    
    def test_focal_length_ranges(self):
        """Test focal length range definitions"""
        ranges = self.analyzer.FOCAL_LENGTH_RANGES
        
        self.assertIn('ultra_wide', ranges)
        self.assertIn('portrait', ranges)
        self.assertIn('telephoto', ranges)
        
        # Verify ranges don't overlap
        for name, (min_fl, max_fl) in ranges.items():
            self.assertLess(min_fl, max_fl, f"Range {name} has invalid bounds")
    
    def test_time_of_day_ranges_coverage(self):
        """Test that time of day ranges cover full 24 hours"""
        ranges = self.analyzer.TIME_OF_DAY_RANGES
        
        # Test some key times are covered
        test_times = [
            time(0, 0),   # midnight
            time(6, 0),   # dawn
            time(12, 0),  # noon
            time(18, 0),  # dusk
            time(23, 59)  # end of day
        ]
        
        for test_time in test_times:
            result = self.analyzer._determine_time_of_day(test_time)
            self.assertNotEqual(result, 'unknown', 
                              f"Time {test_time} should have a defined period")


class TestConvenienceFunction(unittest.TestCase):
    """Test convenience function"""
    
    @patch('exif_analyzer.EXIFAnalyzer')
    def test_analyze_photo_function(self, mock_analyzer_class):
        """Test the analyze_photo convenience function"""
        mock_instance = Mock()
        mock_instance.analyze.return_value = {'test': 'data'}
        mock_analyzer_class.return_value = mock_instance
        
        result = analyze_photo('test.jpg')
        
        mock_instance.analyze.assert_called_once_with('test.jpg')
        self.assertEqual(result, {'test': 'data'})


class TestEXIFAnalyzerIntegration(unittest.TestCase):
    """Integration tests with mock EXIF data"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = EXIFAnalyzer()
    
    @patch('exif_analyzer.exifread.process_file')
    @patch('builtins.open', create=True)
    def test_full_analysis_workflow(self, mock_open, mock_process_file):
        """Test complete analysis workflow with mocked EXIF data"""
        # Create comprehensive mock EXIF tags
        mock_tags = {
            'Image Make': 'Canon',
            'Image Model': 'EOS R5',
            'EXIF LensModel': 'RF24-105mm F4 L IS USM',
            'EXIF ISOSpeedRatings': '1600',
            'EXIF FocalLength': Mock(num=85, den=1),
            'EXIF FNumber': Mock(num=28, den=10),
            'EXIF ExposureTime': '1/250',
            'EXIF DateTimeOriginal': '2025:11:08 17:30:00',
            'GPS GPSLatitude': Mock(values=[
                Mock(num=35, den=1),
                Mock(num=41, den=1),
                Mock(num=22, den=1)
            ]),
            'GPS GPSLatitudeRef': 'N',
            'GPS GPSLongitude': Mock(values=[
                Mock(num=139, den=1),
                Mock(num=45, den=1),
                Mock(num=30, den=1)
            ]),
            'GPS GPSLongitudeRef': 'E'
        }
        
        mock_process_file.return_value = mock_tags
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp_path = tmp.name
        
        try:
            result = self.analyzer.analyze(tmp_path)
            
            # Verify camera info
            self.assertEqual(result['camera']['make'], 'Canon')
            self.assertEqual(result['camera']['model'], 'EOS R5')
            
            # Verify settings
            self.assertEqual(result['settings']['iso'], 1600)
            self.assertEqual(result['settings']['focal_length'], 85.0)
            
            # Verify location
            self.assertTrue(result['location']['has_gps'])
            self.assertEqual(result['location']['location_type'], 'outdoor')
            
            # Verify datetime
            self.assertEqual(result['datetime']['time_of_day'], 'golden_hour_evening')
            
            # Verify context hints
            hints = result['context_hints']
            self.assertEqual(hints['lighting'], 'moderate_light')  # ISO 1600 is moderate_light range
            self.assertEqual(hints['subject_type'], 'portrait')
            self.assertEqual(hints['special_lighting'], 'golden_hour')
            self.assertTrue(hints.get('backlight_risk', False))
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
