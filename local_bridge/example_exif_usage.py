"""
Example usage of EXIF Analyzer Engine.

This script demonstrates how to use the EXIFAnalyzer to extract
and analyze metadata from photo files.
"""

from exif_analyzer import EXIFAnalyzer, analyze_photo
from models.database import init_db, get_session, Photo
import json


def example_basic_analysis():
    """Example: Basic EXIF analysis"""
    print("=" * 60)
    print("Example 1: Basic EXIF Analysis")
    print("=" * 60)
    
    analyzer = EXIFAnalyzer()
    
    # Analyze a photo file
    # Replace with actual photo path
    photo_path = "path/to/your/photo.jpg"
    
    try:
        result = analyzer.analyze(photo_path)
        
        print("\nCamera Information:")
        print(json.dumps(result['camera'], indent=2))
        
        print("\nCamera Settings:")
        print(json.dumps(result['settings'], indent=2))
        
        print("\nLocation Information:")
        print(json.dumps(result['location'], indent=2))
        
        print("\nDateTime Information:")
        datetime_info = result['datetime'].copy()
        if datetime_info.get('capture_time'):
            datetime_info['capture_time'] = str(datetime_info['capture_time'])
        print(json.dumps(datetime_info, indent=2))
        
        print("\nContext Hints:")
        print(json.dumps(result['context_hints'], indent=2))
        
    except FileNotFoundError:
        print(f"Photo file not found: {photo_path}")
        print("Please update the photo_path variable with a valid image file.")


def example_database_integration():
    """Example: Integrate EXIF data with database"""
    print("\n" + "=" * 60)
    print("Example 2: Database Integration")
    print("=" * 60)
    
    # Initialize database
    init_db('sqlite:///data/junmai_test.db')
    session = get_session()
    
    analyzer = EXIFAnalyzer()
    
    # Analyze photo and extract for database
    photo_path = "path/to/your/photo.jpg"
    
    try:
        # Extract EXIF data formatted for database
        exif_data = analyzer.extract_for_database(photo_path)
        
        # Create Photo record
        photo = Photo(
            file_path=photo_path,
            file_name="example_photo.jpg",
            file_size=1024000,
            **exif_data
        )
        
        session.add(photo)
        session.commit()
        
        print(f"\nPhoto record created with ID: {photo.id}")
        print(f"Camera: {photo.camera_make} {photo.camera_model}")
        print(f"Settings: ISO {photo.iso}, f/{photo.aperture}, {photo.shutter_speed}")
        print(f"Focal Length: {photo.focal_length}mm")
        
        if photo.gps_lat and photo.gps_lon:
            print(f"Location: {photo.gps_lat:.4f}, {photo.gps_lon:.4f}")
        
        session.close()
        
    except FileNotFoundError:
        print(f"Photo file not found: {photo_path}")
        print("Please update the photo_path variable with a valid image file.")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        session.close()


def example_context_inference():
    """Example: Context inference for preset selection"""
    print("\n" + "=" * 60)
    print("Example 3: Context Inference for Preset Selection")
    print("=" * 60)
    
    analyzer = EXIFAnalyzer()
    
    # Simulate different shooting scenarios
    scenarios = [
        {
            'name': 'Portrait in Golden Hour',
            'settings': {'iso': 800, 'focal_length': 85},
            'location': {'location_type': 'outdoor', 'has_gps': True},
            'datetime': {'time_of_day': 'golden_hour_evening'}
        },
        {
            'name': 'Indoor Low Light',
            'settings': {'iso': 3200, 'focal_length': 50},
            'location': {'location_type': 'unknown', 'has_gps': False},
            'datetime': {'time_of_day': 'evening'}
        },
        {
            'name': 'Landscape in Morning',
            'settings': {'iso': 100, 'focal_length': 24},
            'location': {'location_type': 'outdoor', 'has_gps': True},
            'datetime': {'time_of_day': 'morning'}
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        hints = analyzer._infer_context(scenario)
        
        print(f"  Lighting: {hints.get('lighting', 'N/A')}")
        print(f"  Subject Type: {hints.get('subject_type', 'N/A')}")
        print(f"  Location: {hints.get('location_type', 'N/A')}")
        print(f"  Time of Day: {hints.get('time_of_day', 'N/A')}")
        
        if hints.get('special_lighting'):
            print(f"  Special Lighting: {hints['special_lighting']}")
        if hints.get('backlight_risk'):
            print(f"  ⚠️  Backlight Risk Detected")
        if hints.get('likely_indoor'):
            print(f"  🏠 Likely Indoor")


def example_batch_processing():
    """Example: Batch process multiple photos"""
    print("\n" + "=" * 60)
    print("Example 4: Batch Processing")
    print("=" * 60)
    
    analyzer = EXIFAnalyzer()
    
    # List of photo paths (replace with actual paths)
    photo_paths = [
        "path/to/photo1.jpg",
        "path/to/photo2.jpg",
        "path/to/photo3.jpg"
    ]
    
    results = []
    
    for photo_path in photo_paths:
        try:
            result = analyzer.analyze(photo_path)
            results.append({
                'path': photo_path,
                'success': True,
                'data': result
            })
            print(f"✓ Analyzed: {photo_path}")
        except Exception as e:
            results.append({
                'path': photo_path,
                'success': False,
                'error': str(e)
            })
            print(f"✗ Failed: {photo_path} - {e}")
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\nProcessed {len(results)} photos: {successful} successful, {len(results) - successful} failed")


def example_time_of_day_detection():
    """Example: Time of day detection"""
    print("\n" + "=" * 60)
    print("Example 5: Time of Day Detection")
    print("=" * 60)
    
    analyzer = EXIFAnalyzer()
    
    from datetime import time
    
    test_times = [
        time(6, 30),   # Golden hour morning
        time(12, 0),   # Midday
        time(17, 30),  # Golden hour evening
        time(22, 0)    # Evening
    ]
    
    print("\nTime of Day Detection:")
    for test_time in test_times:
        period = analyzer._determine_time_of_day(test_time)
        print(f"  {test_time.strftime('%H:%M')} → {period}")


if __name__ == '__main__':
    print("EXIF Analyzer - Usage Examples")
    print("=" * 60)
    
    # Run examples
    # Note: Update photo paths before running
    
    # example_basic_analysis()
    # example_database_integration()
    example_context_inference()
    example_time_of_day_detection()
    # example_batch_processing()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
