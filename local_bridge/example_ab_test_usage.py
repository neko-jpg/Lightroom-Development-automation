"""
Example usage of the A/B Testing System.

This script demonstrates how to:
1. Create an A/B test comparing two presets
2. Assign photos to test variants
3. Record results
4. Measure effectiveness
5. Test statistical significance
6. Generate reports
"""

from models.database import init_db, get_session, Preset, Photo
from ab_test_manager import ABTestManager
from preset_manager import PresetManager
import random


def main():
    # Initialize database
    print("Initializing database...")
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    
    # Initialize managers
    ab_manager = ABTestManager(db)
    preset_manager = PresetManager(db)
    
    print("\n" + "="*60)
    print("A/B Testing System - Example Usage")
    print("="*60)
    
    # ========== Step 1: Create or get presets ==========
    print("\n1. Setting up presets...")
    
    # Check if presets exist
    preset_a = preset_manager.get_preset_by_name('WhiteLayer_v4')
    preset_b = preset_manager.get_preset_by_name('WhiteLayer_v5')
    
    if not preset_a:
        print("   Creating Preset A (WhiteLayer_v4)...")
        preset_a = preset_manager.create_preset(
            name='WhiteLayer_v4',
            version='v4',
            config_template={
                'version': '1.0',
                'pipeline': [
                    {
                        'stage': 'base',
                        'settings': {
                            'exposure': 0.0,
                            'contrast': 0,
                            'highlights': -15,
                            'shadows': 10
                        }
                    },
                    {
                        'stage': 'HSL',
                        'settings': {
                            'orange_hue': -4,
                            'orange_sat': -6,
                            'orange_lum': 4
                        }
                    }
                ]
            },
            context_tags=['backlit_portrait'],
            blend_amount=60
        )
    
    if not preset_b:
        print("   Creating Preset B (WhiteLayer_v5)...")
        preset_b = preset_manager.create_preset(
            name='WhiteLayer_v5',
            version='v5',
            config_template={
                'version': '1.0',
                'pipeline': [
                    {
                        'stage': 'base',
                        'settings': {
                            'exposure': 0.1,
                            'contrast': 5,
                            'highlights': -18,
                            'shadows': 12
                        }
                    },
                    {
                        'stage': 'HSL',
                        'settings': {
                            'orange_hue': -5,
                            'orange_sat': -8,
                            'orange_lum': 6
                        }
                    }
                ]
            },
            context_tags=['backlit_portrait'],
            blend_amount=70
        )
    
    print(f"   ✓ Preset A: {preset_a.name} (ID: {preset_a.id})")
    print(f"   ✓ Preset B: {preset_b.name} (ID: {preset_b.id})")
    
    # ========== Step 2: Create A/B test ==========
    print("\n2. Creating A/B test...")
    
    ab_test = ab_manager.create_ab_test(
        name='WhiteLayer v4 vs v5 - Backlit Portraits',
        description='Testing improved version of WhiteLayer preset for backlit portrait scenarios',
        preset_a_id=preset_a.id,
        preset_b_id=preset_b.id,
        context_tag='backlit_portrait',
        target_sample_size=100,
        duration_days=30
    )
    
    print(f"   ✓ Created A/B test: {ab_test.name}")
    print(f"   ✓ Test ID: {ab_test.id}")
    print(f"   ✓ Status: {ab_test.status}")
    print(f"   ✓ Target sample size: {ab_test.target_sample_size}")
    
    # ========== Step 3: Simulate photo assignments and results ==========
    print("\n3. Simulating photo assignments and results...")
    
    # Get or create sample photos
    photos = db.query(Photo).filter(Photo.context_tag == 'backlit_portrait').limit(80).all()
    
    if len(photos) < 80:
        print(f"   Creating {80 - len(photos)} sample photos...")
        for i in range(80 - len(photos)):
            photo = Photo(
                file_path=f'/test/backlit_portrait_{i}.cr3',
                file_name=f'backlit_portrait_{i}.cr3',
                file_size=10000000,
                context_tag='backlit_portrait',
                status='imported',
                ai_score=random.uniform(3.5, 5.0)
            )
            db.add(photo)
        db.commit()
        photos = db.query(Photo).filter(Photo.context_tag == 'backlit_portrait').limit(80).all()
    
    print(f"   Assigning {len(photos)} photos to test variants...")
    
    # Assign photos and simulate results
    # Variant B (v5) will have slightly better approval rate
    for i, photo in enumerate(photos):
        assignment = ab_manager.assign_photo_to_variant(
            test_id=ab_test.id,
            photo_id=photo.id
        )
        
        # Simulate approval based on variant
        # Variant A: 70% approval rate
        # Variant B: 85% approval rate
        if assignment.variant == 'A':
            approved = random.random() < 0.70
        else:
            approved = random.random() < 0.85
        
        # Simulate processing time
        processing_time = random.uniform(4.5, 6.5)
        
        ab_manager.record_result(
            test_id=ab_test.id,
            photo_id=photo.id,
            approved=approved,
            processing_time=processing_time
        )
    
    print(f"   ✓ Assigned and recorded results for {len(photos)} photos")
    
    # ========== Step 4: Check progress ==========
    print("\n4. Checking test progress...")
    
    progress = ab_manager.get_test_progress(ab_test.id)
    
    print(f"   Total assignments: {progress['total_assignments']}")
    print(f"   Completed assignments: {progress['completed_assignments']}")
    print(f"   Progress: {progress['progress_percent']:.1f}%")
    print(f"   Ready for analysis: {progress['ready_for_analysis']}")
    
    # ========== Step 5: Measure effectiveness ==========
    print("\n5. Measuring effectiveness...")
    
    effectiveness = ab_manager.measure_effectiveness(ab_test.id)
    
    if effectiveness['status'] == 'success':
        print(f"   Variant A (Control):")
        print(f"     - Samples: {effectiveness['variant_a']['samples']}")
        print(f"     - Approval rate: {effectiveness['variant_a']['approval_rate']:.1%}")
        print(f"     - Avg processing time: {effectiveness['variant_a']['avg_processing_time']:.2f}s")
        
        print(f"   Variant B (Treatment):")
        print(f"     - Samples: {effectiveness['variant_b']['samples']}")
        print(f"     - Approval rate: {effectiveness['variant_b']['approval_rate']:.1%}")
        print(f"     - Avg processing time: {effectiveness['variant_b']['avg_processing_time']:.2f}s")
        
        print(f"   Improvements:")
        print(f"     - Approval rate: {effectiveness['improvements']['approval_rate']:+.1f}%")
        if effectiveness['improvements']['processing_time']:
            print(f"     - Processing time: {effectiveness['improvements']['processing_time']:+.1f}%")
    else:
        print(f"   Status: {effectiveness['status']}")
    
    # ========== Step 6: Test statistical significance ==========
    print("\n6. Testing statistical significance...")
    
    significance = ab_manager.test_statistical_significance(ab_test.id)
    
    if significance['status'] == 'success':
        print(f"   Approval rate test:")
        print(f"     - Chi-squared statistic: {significance['approval_rate_test']['chi2_statistic']:.4f}")
        print(f"     - P-value: {significance['approval_rate_test']['p_value']:.4f}")
        print(f"     - Significant: {significance['approval_rate_test']['significant']}")
        print(f"     - {significance['approval_rate_test']['interpretation']}")
        
        if significance['processing_time_test']:
            print(f"   Processing time test:")
            print(f"     - T-statistic: {significance['processing_time_test']['t_statistic']:.4f}")
            print(f"     - P-value: {significance['processing_time_test']['p_value']:.4f}")
            print(f"     - Significant: {significance['processing_time_test']['significant']}")
        
        print(f"\n   Winner: {significance['winner'] if significance['winner'] else 'No clear winner'}")
        print(f"   Recommendation: {significance['recommendation']}")
    
    # ========== Step 7: Generate report ==========
    print("\n7. Generating report...")
    
    report_path = 'data/ab_test_report.json'
    report = ab_manager.generate_report(ab_test.id, output_path=report_path)
    
    print(f"   ✓ Report generated: {report_path}")
    print(f"\n   Summary:")
    print(f"     - Conclusion: {report['summary']['conclusion']}")
    print(f"     - Action: {report['summary']['action']}")
    
    # ========== Step 8: List all tests ==========
    print("\n8. Listing all A/B tests...")
    
    all_tests = ab_manager.list_ab_tests()
    
    print(f"   Total tests: {len(all_tests)}")
    for test in all_tests:
        print(f"     - {test.name} (Status: {test.status})")
    
    print("\n" + "="*60)
    print("Example completed successfully!")
    print("="*60)
    
    db.close()


if __name__ == '__main__':
    main()
