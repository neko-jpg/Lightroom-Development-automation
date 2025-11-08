"""
Example usage of Context Recognition Engine.

Demonstrates how to use the context engine with EXIF data to determine
shooting context and get preset recommendations.
"""

from pathlib import Path
from exif_analyzer import EXIFAnalyzer
from context_engine import ContextEngine, determine_photo_context


def example_basic_usage():
    """Basic usage example"""
    print("=" * 60)
    print("Example 1: Basic Context Determination")
    print("=" * 60)
    
    # Sample EXIF data (normally from EXIFAnalyzer)
    exif_data = {
        'camera': {
            'make': 'Canon',
            'model': 'EOS R5',
            'lens': 'RF 50mm F1.8'
        },
        'settings': {
            'iso': 500,
            'focal_length': 50.0,
            'aperture': 2.8,
            'shutter_speed': '1/250',
            'exposure_compensation': -0.3
        },
        'location': {
            'latitude': 35.6762,
            'longitude': 139.6503,
            'location_type': 'outdoor',
            'has_gps': True
        },
        'datetime': {
            'capture_time': None,
            'time_of_day': 'golden_hour_evening'
        },
        'context_hints': {
            'lighting': 'moderate_light',
            'subject_type': 'standard',
            'time_of_day': 'golden_hour_evening',
            'backlight_risk': True
        }
    }
    
    # Initialize engine
    engine = ContextEngine()
    
    # Determine context
    result = engine.determine_context(exif_data)
    
    print(f"\nDetected Context: {result['context']}")
    print(f"Confidence Score: {result['score']:.2f}")
    print(f"Description: {result['description']}")
    print(f"Recommended Preset: {result['recommended_preset']}")
    print(f"Preset Blend: {result['preset_blend']}%")
    
    print("\nAll Context Scores:")
    for context, score in sorted(result['all_scores'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {context}: {score:.3f}")


def example_with_real_photo():
    """Example with real photo file"""
    print("\n" + "=" * 60)
    print("Example 2: Context Determination from Real Photo")
    print("=" * 60)
    
    # Path to a sample photo (adjust as needed)
    photo_path = "path/to/your/photo.CR3"
    
    if not Path(photo_path).exists():
        print(f"\nPhoto not found: {photo_path}")
        print("Please update the path to a real photo file.")
        return
    
    # Analyze EXIF
    print(f"\nAnalyzing: {Path(photo_path).name}")
    analyzer = EXIFAnalyzer()
    exif_data = analyzer.analyze(photo_path)
    
    # Determine context
    engine = ContextEngine()
    result = engine.determine_context(exif_data)
    
    print(f"\nCamera: {exif_data['camera'].get('make')} {exif_data['camera'].get('model')}")
    print(f"Settings: ISO {exif_data['settings'].get('iso')}, "
          f"f/{exif_data['settings'].get('aperture')}, "
          f"{exif_data['settings'].get('shutter_speed')}")
    print(f"Focal Length: {exif_data['settings'].get('focal_length')}mm")
    print(f"Time of Day: {exif_data['datetime'].get('time_of_day')}")
    
    print(f"\nDetected Context: {result['context']}")
    print(f"Confidence: {result['score']:.2%}")
    print(f"Recommended Preset: {result['recommended_preset']} ({result['preset_blend']}%)")


def example_multiple_scenarios():
    """Example showing different shooting scenarios"""
    print("\n" + "=" * 60)
    print("Example 3: Multiple Shooting Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            'name': 'Backlit Portrait',
            'exif': {
                'settings': {'iso': 500, 'focal_length': 50.0, 'aperture': 2.8},
                'location': {'has_gps': True, 'location_type': 'outdoor'},
                'context_hints': {'time_of_day': 'golden_hour_evening', 'backlight_risk': True}
            }
        },
        {
            'name': 'Low Light Indoor',
            'exif': {
                'settings': {'iso': 3200, 'focal_length': 35.0, 'aperture': 1.8},
                'location': {'has_gps': False, 'location_type': 'unknown'},
                'context_hints': {'lighting': 'low_light', 'time_of_day': 'evening'}
            }
        },
        {
            'name': 'Landscape',
            'exif': {
                'settings': {'iso': 200, 'focal_length': 24.0, 'aperture': 8.0},
                'location': {'has_gps': True, 'location_type': 'outdoor'},
                'context_hints': {'time_of_day': 'morning', 'lighting': 'good_light'}
            }
        },
        {
            'name': 'Night Cityscape',
            'exif': {
                'settings': {'iso': 1600, 'focal_length': 35.0, 'aperture': 4.0},
                'location': {'has_gps': True, 'location_type': 'outdoor'},
                'context_hints': {'time_of_day': 'night', 'lighting': 'low_light'}
            }
        },
        {
            'name': 'Sports Action',
            'exif': {
                'settings': {'iso': 800, 'focal_length': 200.0, 'aperture': 2.8, 'shutter_speed': '1/1000'},
                'location': {'has_gps': True, 'location_type': 'outdoor'},
                'context_hints': {'time_of_day': 'afternoon', 'subject_type': 'telephoto'}
            }
        }
    ]
    
    engine = ContextEngine()
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 40)
        
        # Add required structure
        exif_data = {
            'camera': {},
            'settings': {},
            'location': {},
            'datetime': {},
            'context_hints': {}
        }
        
        # Merge scenario data
        for key, value in scenario['exif'].items():
            exif_data[key].update(value)
        
        result = engine.determine_context(exif_data)
        
        print(f"  Context: {result['context']}")
        print(f"  Score: {result['score']:.2f}")
        print(f"  Preset: {result['recommended_preset']} ({result['preset_blend']}%)")


def example_list_contexts():
    """Example listing all available contexts"""
    print("\n" + "=" * 60)
    print("Example 4: List All Available Contexts")
    print("=" * 60)
    
    engine = ContextEngine()
    contexts = engine.get_context_list()
    
    print(f"\nTotal contexts: {len(contexts)}\n")
    
    for context in contexts:
        print(f"{context['name']}")
        print(f"  Description: {context['description']}")
        print(f"  Preset: {context['recommended_preset']} ({context['preset_blend']}%)")
        print(f"  Conditions: {context['condition_count']}")
        print()


def example_validate_rules():
    """Example validating rules file"""
    print("\n" + "=" * 60)
    print("Example 5: Validate Context Rules")
    print("=" * 60)
    
    engine = ContextEngine()
    is_valid, errors = engine.validate_rules()
    
    if is_valid:
        print("\n✓ Rules file is valid!")
        print(f"  Loaded {len(engine.rules)} contexts successfully")
    else:
        print("\n✗ Rules file has errors:")
        for error in errors:
            print(f"  - {error}")


def example_convenience_function():
    """Example using convenience function"""
    print("\n" + "=" * 60)
    print("Example 6: Using Convenience Function")
    print("=" * 60)
    
    exif_data = {
        'camera': {},
        'settings': {
            'iso': 1600,
            'focal_length': 85.0,
            'aperture': 1.8
        },
        'location': {
            'has_gps': False,
            'location_type': 'unknown'
        },
        'datetime': {},
        'context_hints': {
            'lighting': 'low_light',
            'time_of_day': 'evening'
        }
    }
    
    # Use convenience function (creates engine internally)
    result = determine_photo_context(exif_data)
    
    print(f"\nQuick determination:")
    print(f"  Context: {result['context']}")
    print(f"  Preset: {result['recommended_preset']}")


def example_with_ai_evaluation():
    """Example with AI evaluation data"""
    print("\n" + "=" * 60)
    print("Example 7: Context with AI Evaluation")
    print("=" * 60)
    
    exif_data = {
        'camera': {},
        'settings': {
            'iso': 800,
            'focal_length': 50.0,
            'aperture': 2.8
        },
        'location': {
            'has_gps': True,
            'location_type': 'outdoor'
        },
        'datetime': {},
        'context_hints': {
            'time_of_day': 'golden_hour_evening'
        }
    }
    
    # AI evaluation results (from AI Selection Engine)
    ai_eval = {
        'overall_score': 4.5,
        'focus_score': 4.8,
        'exposure_score': 4.2,
        'composition_score': 4.6,
        'faces_detected': 1,
        'recommendation': 'Excellent portrait with good focus'
    }
    
    engine = ContextEngine()
    result = engine.determine_context(exif_data, ai_eval)
    
    print(f"\nWith AI evaluation:")
    print(f"  AI Score: {ai_eval['overall_score']}/5.0")
    print(f"  Context: {result['context']}")
    print(f"  Preset: {result['recommended_preset']}")


if __name__ == '__main__':
    # Run all examples
    example_basic_usage()
    example_multiple_scenarios()
    example_list_contexts()
    example_validate_rules()
    example_convenience_function()
    example_with_ai_evaluation()
    
    # Uncomment to test with real photo
    # example_with_real_photo()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
