"""
EXIF Analyzer Engine for Junmai AutoDev system.
Extracts and analyzes EXIF metadata from RAW and JPEG images.

Features:
- Metadata extraction using exifread and piexif
- Camera settings analysis (ISO, shutter speed, aperture, focal length)
- GPS location parsing with indoor/outdoor detection
- Time of day detection from capture timestamp
- Context hints inference for preset selection

Requirements: 1.3, 3.1
"""

import os
from datetime import datetime, time
from typing import Dict, Optional, Tuple, Any
import logging
from pathlib import Path

try:
    import exifread
    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False
    logging.warning("exifread not available. Install with: pip install exifread")

try:
    import piexif
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False
    logging.warning("piexif not available. Install with: pip install piexif")


logger = logging.getLogger(__name__)


class EXIFAnalyzer:
    """
    EXIF解析エンジン
    
    写真ファイルからEXIFメタデータを抽出し、撮影コンテキストを推定します。
    """
    
    # Time of day definitions (24-hour format)
    TIME_OF_DAY_RANGES = {
        'night': (time(0, 0), time(5, 0)),
        'blue_hour_morning': (time(5, 0), time(6, 30)),
        'golden_hour_morning': (time(6, 30), time(8, 0)),
        'morning': (time(8, 0), time(11, 0)),
        'midday': (time(11, 0), time(14, 0)),
        'afternoon': (time(14, 0), time(16, 30)),
        'golden_hour_evening': (time(16, 30), time(18, 30)),
        'blue_hour_evening': (time(18, 30), time(20, 0)),
        'evening': (time(20, 0), time(23, 59))
    }
    
    # Focal length ranges for subject type inference
    FOCAL_LENGTH_RANGES = {
        'ultra_wide': (0, 24),
        'wide': (24, 35),
        'standard': (35, 70),
        'portrait': (70, 135),
        'telephoto': (135, 300),
        'super_telephoto': (300, 9999)
    }
    
    def __init__(self):
        """Initialize EXIF analyzer"""
        if not EXIFREAD_AVAILABLE:
            logger.error("exifread library is not installed")
        if not PIEXIF_AVAILABLE:
            logger.warning("piexif library is not installed (optional)")
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        写真ファイルのEXIFデータを解析
        
        Args:
            file_path: 写真ファイルのパス
            
        Returns:
            解析結果の辞書:
            {
                'camera': {...},      # カメラ情報
                'settings': {...},    # 撮影設定
                'location': {...},    # GPS位置情報
                'datetime': {...},    # 撮影日時情報
                'context_hints': {...} # コンテキストヒント
            }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not EXIFREAD_AVAILABLE:
            logger.error("Cannot analyze EXIF: exifread not installed")
            return self._empty_result()
        
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            
            result = {
                'camera': self._extract_camera_info(tags),
                'settings': self._extract_settings(tags),
                'location': self._extract_gps(tags),
                'datetime': self._extract_datetime(tags),
                'context_hints': {}
            }
            
            # Infer context hints from extracted data
            result['context_hints'] = self._infer_context(result)
            
            logger.info(f"Successfully analyzed EXIF for: {Path(file_path).name}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing EXIF for {file_path}: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'camera': {},
            'settings': {},
            'location': {},
            'datetime': {},
            'context_hints': {}
        }
    
    def _extract_camera_info(self, tags: Dict) -> Dict[str, Optional[str]]:
        """
        カメラ情報を抽出
        
        Args:
            tags: EXIF tags dictionary
            
        Returns:
            カメラ情報の辞書
        """
        return {
            'make': self._get_tag_value(tags, 'Image Make'),
            'model': self._get_tag_value(tags, 'Image Model'),
            'lens': self._get_tag_value(tags, 'EXIF LensModel') or 
                   self._get_tag_value(tags, 'EXIF LensMake'),
            'serial_number': self._get_tag_value(tags, 'EXIF BodySerialNumber')
        }
    
    def _extract_settings(self, tags: Dict) -> Dict[str, Any]:
        """
        撮影設定を抽出
        
        Args:
            tags: EXIF tags dictionary
            
        Returns:
            撮影設定の辞書
        """
        # Extract ISO
        iso = self._get_tag_value(tags, 'EXIF ISOSpeedRatings')
        if iso:
            try:
                iso = int(str(iso))
            except (ValueError, TypeError):
                iso = None
        
        # Extract focal length
        focal_length = self._get_tag_value(tags, 'EXIF FocalLength')
        if focal_length:
            focal_length = self._parse_rational(focal_length)
        
        # Extract aperture (F-number)
        aperture = self._get_tag_value(tags, 'EXIF FNumber')
        if aperture:
            aperture = self._parse_rational(aperture)
        
        # Extract shutter speed
        shutter_speed = self._get_tag_value(tags, 'EXIF ExposureTime')
        
        # Extract exposure compensation
        exposure_comp = self._get_tag_value(tags, 'EXIF ExposureBiasValue')
        if exposure_comp:
            exposure_comp = self._parse_rational(exposure_comp)
        
        # Extract white balance
        white_balance = self._get_tag_value(tags, 'EXIF WhiteBalance')
        
        # Extract metering mode
        metering_mode = self._get_tag_value(tags, 'EXIF MeteringMode')
        
        return {
            'iso': iso,
            'focal_length': focal_length,
            'aperture': aperture,
            'shutter_speed': str(shutter_speed) if shutter_speed else None,
            'exposure_compensation': exposure_comp,
            'white_balance': str(white_balance) if white_balance else None,
            'metering_mode': str(metering_mode) if metering_mode else None
        }
    
    def _extract_gps(self, tags: Dict) -> Dict[str, Any]:
        """
        GPS位置情報を抽出し、屋外/室内を判定
        
        Args:
            tags: EXIF tags dictionary
            
        Returns:
            GPS情報と屋外/室内判定の辞書
        """
        gps_lat = self._get_tag_value(tags, 'GPS GPSLatitude')
        gps_lat_ref = self._get_tag_value(tags, 'GPS GPSLatitudeRef')
        gps_lon = self._get_tag_value(tags, 'GPS GPSLongitude')
        gps_lon_ref = self._get_tag_value(tags, 'GPS GPSLongitudeRef')
        
        latitude = None
        longitude = None
        
        if gps_lat and gps_lon:
            try:
                latitude = self._convert_gps_to_decimal(gps_lat, gps_lat_ref)
                longitude = self._convert_gps_to_decimal(gps_lon, gps_lon_ref)
            except Exception as e:
                logger.warning(f"Failed to parse GPS coordinates: {e}")
        
        # Determine indoor/outdoor based on GPS availability
        # If GPS is present and valid, likely outdoor
        location_type = None
        if latitude is not None and longitude is not None:
            location_type = 'outdoor'
        else:
            # No GPS data - could be indoor or GPS disabled
            location_type = 'unknown'
        
        return {
            'latitude': latitude,
            'longitude': longitude,
            'location_type': location_type,
            'has_gps': latitude is not None and longitude is not None
        }
    
    def _extract_datetime(self, tags: Dict) -> Dict[str, Any]:
        """
        撮影日時を抽出し、時間帯を判定
        
        Args:
            tags: EXIF tags dictionary
            
        Returns:
            日時情報と時間帯の辞書
        """
        # Try different datetime tags
        datetime_str = (
            self._get_tag_value(tags, 'EXIF DateTimeOriginal') or
            self._get_tag_value(tags, 'EXIF DateTimeDigitized') or
            self._get_tag_value(tags, 'Image DateTime')
        )
        
        capture_time = None
        time_of_day = None
        
        if datetime_str:
            try:
                # Parse EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                capture_time = datetime.strptime(str(datetime_str), '%Y:%m:%d %H:%M:%S')
                time_of_day = self._determine_time_of_day(capture_time.time())
            except ValueError as e:
                logger.warning(f"Failed to parse datetime: {datetime_str}, error: {e}")
        
        return {
            'capture_time': capture_time,
            'time_of_day': time_of_day,
            'datetime_string': str(datetime_str) if datetime_str else None
        }
    
    def _infer_context(self, exif_data: Dict) -> Dict[str, Any]:
        """
        EXIFデータからコンテキストヒントを推定
        
        Args:
            exif_data: 抽出されたEXIFデータ
            
        Returns:
            コンテキストヒントの辞書
        """
        hints = {}
        
        settings = exif_data.get('settings', {})
        location = exif_data.get('location', {})
        datetime_info = exif_data.get('datetime', {})
        
        # Lighting condition inference
        iso = settings.get('iso')
        time_of_day = datetime_info.get('time_of_day')
        
        if iso:
            if iso > 3200:
                hints['lighting'] = 'very_low_light'
            elif iso > 1600:
                hints['lighting'] = 'low_light'
            elif iso > 800:
                hints['lighting'] = 'moderate_light'
            else:
                hints['lighting'] = 'good_light'
        
        # Subject type inference from focal length
        focal_length = settings.get('focal_length')
        if focal_length:
            for subject_type, (min_fl, max_fl) in self.FOCAL_LENGTH_RANGES.items():
                if min_fl <= focal_length < max_fl:
                    hints['subject_type'] = subject_type
                    break
        
        # Location type
        if location.get('location_type'):
            hints['location_type'] = location['location_type']
        
        # Time of day
        if time_of_day:
            hints['time_of_day'] = time_of_day
            
            # Special lighting conditions based on time
            if 'golden_hour' in time_of_day:
                hints['special_lighting'] = 'golden_hour'
            elif 'blue_hour' in time_of_day:
                hints['special_lighting'] = 'blue_hour'
        
        # Backlight detection (high ISO + golden hour + outdoor)
        if (iso and iso > 400 and 
            time_of_day and 'golden_hour' in time_of_day and
            location.get('location_type') == 'outdoor'):
            hints['backlight_risk'] = True
        
        # Indoor detection (no GPS + high ISO)
        if (not location.get('has_gps') and iso and iso > 1600):
            hints['likely_indoor'] = True
        
        return hints
    
    def _determine_time_of_day(self, capture_time: time) -> str:
        """
        撮影時刻から時間帯を判定
        
        Args:
            capture_time: 撮影時刻
            
        Returns:
            時間帯の文字列
        """
        for period, (start, end) in self.TIME_OF_DAY_RANGES.items():
            if start <= capture_time <= end:
                return period
        
        return 'unknown'
    
    def _get_tag_value(self, tags: Dict, tag_name: str) -> Optional[Any]:
        """
        タグ値を安全に取得
        
        Args:
            tags: EXIF tags dictionary
            tag_name: タグ名
            
        Returns:
            タグ値またはNone
        """
        tag = tags.get(tag_name)
        return tag if tag else None
    
    def _parse_rational(self, value: Any) -> Optional[float]:
        """
        EXIF rational値をfloatに変換
        
        Args:
            value: EXIF rational値
            
        Returns:
            float値またはNone
        """
        try:
            # Handle exifread.Ratio objects
            if hasattr(value, 'num') and hasattr(value, 'den'):
                if value.den == 0:
                    return None
                return float(value.num) / float(value.den)
            
            # Handle string representation like "24/1"
            value_str = str(value)
            if '/' in value_str:
                num, den = value_str.split('/')
                den_val = float(den)
                if den_val == 0:
                    return None
                return float(num) / den_val
            
            # Try direct conversion
            return float(value_str)
            
        except (ValueError, AttributeError, ZeroDivisionError) as e:
            logger.debug(f"Failed to parse rational value {value}: {e}")
            return None
    
    def _convert_gps_to_decimal(
        self, 
        gps_coord: Any, 
        gps_ref: Optional[Any]
    ) -> Optional[float]:
        """
        GPS座標をDMS形式から10進数形式に変換
        
        Args:
            gps_coord: GPS座標 (度, 分, 秒)
            gps_ref: 方向参照 (N/S/E/W)
            
        Returns:
            10進数形式の座標またはNone
        """
        try:
            # Parse coordinate values
            if hasattr(gps_coord, 'values'):
                values = gps_coord.values
            else:
                # Try to parse as list
                values = list(gps_coord)
            
            if len(values) < 3:
                return None
            
            # Extract degrees, minutes, seconds
            degrees = self._parse_rational(values[0])
            minutes = self._parse_rational(values[1])
            seconds = self._parse_rational(values[2])
            
            if degrees is None or minutes is None or seconds is None:
                return None
            
            # Convert to decimal
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            # Apply direction
            if gps_ref:
                ref_str = str(gps_ref).upper()
                if ref_str in ['S', 'W']:
                    decimal = -decimal
            
            return decimal
            
        except Exception as e:
            logger.debug(f"Failed to convert GPS coordinate: {e}")
            return None
    
    def extract_for_database(self, file_path: str) -> Dict[str, Any]:
        """
        データベース保存用にEXIFデータを抽出
        
        Args:
            file_path: 写真ファイルのパス
            
        Returns:
            データベースのPhotoモデルに対応する辞書
        """
        exif_data = self.analyze(file_path)
        
        camera = exif_data.get('camera', {})
        settings = exif_data.get('settings', {})
        location = exif_data.get('location', {})
        datetime_info = exif_data.get('datetime', {})
        
        return {
            'camera_make': camera.get('make'),
            'camera_model': camera.get('model'),
            'lens': camera.get('lens'),
            'focal_length': settings.get('focal_length'),
            'aperture': settings.get('aperture'),
            'shutter_speed': settings.get('shutter_speed'),
            'iso': settings.get('iso'),
            'capture_time': datetime_info.get('capture_time'),
            'gps_lat': location.get('latitude'),
            'gps_lon': location.get('longitude')
        }


# Convenience function for quick analysis
def analyze_photo(file_path: str) -> Dict[str, Any]:
    """
    写真ファイルのEXIFデータを解析（便利関数）
    
    Args:
        file_path: 写真ファイルのパス
        
    Returns:
        解析結果の辞書
    """
    analyzer = EXIFAnalyzer()
    return analyzer.analyze(file_path)
