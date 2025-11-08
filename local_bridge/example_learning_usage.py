"""
Example usage of the Learning System.
Demonstrates user feedback recording, pattern analysis, and customized preset generation.
"""

from datetime import datetime
from models.database import init_db, get_session, Photo, Preset
from learning_system import LearningSystem


def example_basic_usage():
    """Basic usage example: Recording user feedback"""
    print("=== Basic Learning System Usage ===\n")
    
    # Initialize database and learning system
    init_db('sqlite:///data/junmai.db')
    learning_system = LearningSystem()
    
    # Example 1: Record approval
    print("1. Recording approval...")
    learning_data = learning_system.record_approval(
        photo_id=1,
        original_preset='WhiteLayer_Transparency_v4'
    )
    print(f"   ✓ Recorded approval for photo {learning_data.photo_id}")
    
    # Example 2: Record rejection
    print("\n2. Recording rejection...")
    learning_data = learning_system.record_rejection(
        photo_id=2,
        original_preset='WhiteLayer_Transparency_v4',
        reason='Too bright, lost detail in highlights'
    )
    print(f"   ✓ Recorded rejection for photo {learning_data.photo_id}")
    
    # Example 3: Record modification
    print("\n3. Recording modification...")
    adjustments = {
        'Exposure2012': 0.3,
        'Highlights2012': -15,
        'Shadows2012': 20,
        'Clarity2012': 8
    }
    learning_data = learning_system.record_modification(
        photo_id=3,
        original_preset='WhiteLayer_Transparency_v4',
        final_preset='WhiteLayer_Transparency_v4',
        parameter_adjustments=adjustments
    )
    print(f"   ✓ Recorded modification for photo {learning_data.photo_id}")
    print(f"   Adjustments: {adjustments}")


def example_pattern_analysis():
    """Example: Analyzing parameter patterns"""
    print("\n=== Parameter Pattern Analysis ===\n")
    
    learning_system = LearningSystem()
    
    # Analyze patterns for a specific preset and context
    print("Analyzing patterns for 'WhiteLayer_Transparency_v4' preset...")
    print("Context: backlit_portrait")
    print("Period: Last 90 days\n")
    
    analysis = learning_system.analyze_parameter_patterns(
        context_tag='backlit_portrait',
        preset_name='WhiteLayer_Transparency_v4',
        days=90
    )
    
    if analysis['status'] == 'success':
        print(f"✓ Analysis complete!")
        print(f"  Sample count: {analysis['sample_count']}")
        print(f"  Approval rate: {analysis['approval_rate']:.1%}")
        print(f"  Modifications: {analysis['modification_count']}")
        
        if analysis['avg_adjustments']:
            print("\n  Average adjustments:")
            for param, stats in analysis['avg_adjustments'].items():
                print(f"    {param}:")
                print(f"      Mean: {stats['mean']:.2f}")
                print(f"      Median: {stats['median']:.2f}")
                print(f"      Std Dev: {stats['stdev']:.2f}")
    else:
        print(f"⚠ {analysis['status']}")
        print(f"  Sample count: {analysis.get('sample_count', 0)}")
        print(f"  Minimum required: {analysis.get('min_required', 0)}")


def example_generate_customized_preset():
    """Example: Generating a customized preset"""
    print("\n=== Customized Preset Generation ===\n")
    
    learning_system = LearningSystem()
    
    print("Generating customized preset...")
    print("Base preset: WhiteLayer_Transparency_v4")
    print("Context: backlit_portrait\n")
    
    preset_config = learning_system.generate_customized_preset(
        base_preset_name='WhiteLayer_Transparency_v4',
        context_tag='backlit_portrait',
        analysis_days=90
    )
    
    if preset_config:
        print("✓ Customized preset generated!")
        print(f"  Name: {preset_config['name']}")
        print(f"  Version: {preset_config['version']}")
        print(f"  Base preset: {preset_config['base_preset']}")
        print(f"  Context: {preset_config['context_tag']}")
        
        stats = preset_config['learning_stats']
        print(f"\n  Learning statistics:")
        print(f"    Sample count: {stats['sample_count']}")
        print(f"    Approval rate: {stats['approval_rate']:.1%}")
        print(f"    Analysis period: {stats['analysis_period_days']} days")
        
        # Save the preset
        print("\n  Saving preset to database...")
        saved_preset = learning_system.save_customized_preset(preset_config)
        print(f"  ✓ Saved as preset ID: {saved_preset.id}")
    else:
        print("⚠ Could not generate preset (insufficient data or low approval rate)")


def example_evaluate_preset():
    """Example: Evaluating preset effectiveness"""
    print("\n=== Preset Effectiveness Evaluation ===\n")
    
    learning_system = LearningSystem()
    
    print("Evaluating preset effectiveness...")
    print("Preset: WhiteLayer_Transparency_v4")
    print("Period: Last 30 days\n")
    
    evaluation = learning_system.evaluate_preset_effectiveness(
        preset_name='WhiteLayer_Transparency_v4',
        days=30
    )
    
    if evaluation['status'] == 'success':
        print("✓ Evaluation complete!")
        print(f"  Total uses: {evaluation['total_uses']}")
        print(f"  Approved: {evaluation['approved_count']} ({evaluation['approval_rate']:.1%})")
        print(f"  Modified: {evaluation['modified_count']} ({evaluation['modification_rate']:.1%})")
        print(f"  Rejected: {evaluation['rejected_count']} ({evaluation['rejection_rate']:.1%})")
        
        if evaluation['avg_ai_score']:
            print(f"  Average AI score: {evaluation['avg_ai_score']:.2f}/5.0")
        
        print(f"\n  Effectiveness score: {evaluation['effectiveness_score']:.2f}/1.0")
        
        if evaluation['context_usage']:
            print("\n  Context usage:")
            for context, count in evaluation['context_usage'].items():
                print(f"    {context}: {count} times")
    else:
        print(f"⚠ {evaluation['status']}")


def example_export_import():
    """Example: Exporting and importing learning data"""
    print("\n=== Learning Data Export/Import ===\n")
    
    learning_system = LearningSystem()
    
    # Export
    print("1. Exporting learning data...")
    export_path = 'data/learning_export.json'
    result = learning_system.export_learning_data(
        output_path=export_path,
        days=90  # Last 90 days
    )
    
    if result['status'] == 'success':
        print(f"   ✓ Exported {result['total_records']} records")
        print(f"   File: {result['output_path']}")
    
    # Import (example - typically used for backup restoration)
    print("\n2. Importing learning data...")
    print("   (This would restore data from a backup)")
    # result = learning_system.import_learning_data(export_path)
    # print(f"   ✓ Imported {result['imported_count']} records")
    # print(f"   Skipped {result['skipped_count']} duplicates")


def example_learning_summary():
    """Example: Getting learning system summary"""
    print("\n=== Learning System Summary ===\n")
    
    learning_system = LearningSystem()
    
    print("Getting summary for last 30 days...\n")
    
    summary = learning_system.get_learning_summary(days=30)
    
    print(f"Total records: {summary['total_records']}")
    print(f"Approved: {summary['approved_count']}")
    print(f"Rejected: {summary['rejected_count']}")
    print(f"Modified: {summary['modified_count']}")
    print(f"Overall approval rate: {summary['approval_rate']:.1%}")
    
    if summary['preset_usage']:
        print("\nPreset usage:")
        for preset, count in sorted(
            summary['preset_usage'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {preset}: {count} times")


def example_workflow():
    """Complete workflow example"""
    print("\n=== Complete Learning Workflow ===\n")
    
    learning_system = LearningSystem()
    
    print("Scenario: Photographer reviews 100 photos over 2 weeks")
    print("Preset: WhiteLayer_Transparency_v4")
    print("Context: backlit_portrait\n")
    
    # Step 1: Accumulate feedback
    print("Step 1: Accumulating user feedback...")
    print("  (Recording approvals, rejections, and modifications)")
    print("  ...")
    
    # Step 2: Analyze patterns
    print("\nStep 2: Analyzing parameter patterns...")
    analysis = learning_system.analyze_parameter_patterns(
        context_tag='backlit_portrait',
        preset_name='WhiteLayer_Transparency_v4',
        days=14
    )
    
    if analysis['status'] == 'success':
        print(f"  ✓ Found {analysis['sample_count']} samples")
        print(f"  Approval rate: {analysis['approval_rate']:.1%}")
    
    # Step 3: Generate customized preset
    print("\nStep 3: Generating customized preset...")
    preset_config = learning_system.generate_customized_preset(
        base_preset_name='WhiteLayer_Transparency_v4',
        context_tag='backlit_portrait',
        analysis_days=14
    )
    
    if preset_config:
        print(f"  ✓ Generated: {preset_config['name']}")
        saved = learning_system.save_customized_preset(preset_config)
        print(f"  ✓ Saved to database (ID: {saved.id})")
    
    # Step 4: Evaluate effectiveness
    print("\nStep 4: Evaluating new preset effectiveness...")
    print("  (After using the customized preset for a week)")
    evaluation = learning_system.evaluate_preset_effectiveness(
        preset_name=preset_config['name'] if preset_config else 'WhiteLayer_Transparency_v4',
        days=7
    )
    
    if evaluation['status'] == 'success':
        print(f"  ✓ Effectiveness score: {evaluation['effectiveness_score']:.2f}")
    
    # Step 5: Export for backup
    print("\nStep 5: Backing up learning data...")
    result = learning_system.export_learning_data(
        output_path='data/learning_backup.json'
    )
    print(f"  ✓ Backed up {result['total_records']} records")
    
    print("\n✓ Workflow complete!")


if __name__ == '__main__':
    print("Junmai AutoDev - Learning System Examples")
    print("=" * 50)
    
    # Run examples
    try:
        example_basic_usage()
        example_pattern_analysis()
        example_generate_customized_preset()
        example_evaluate_preset()
        example_export_import()
        example_learning_summary()
        example_workflow()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
