"""
Example usage of Image Quality Evaluator

This script demonstrates how to use the ImageQualityEvaluator
to evaluate photos for focus, exposure, composition, and face detection.
"""

import sys
import json
from pathlib import Path
from image_quality_evaluator import ImageQualityEvaluator


def evaluate_single_image(image_path: str):
    """
    Evaluate a single image and print detailed results.
    
    Args:
        image_path: Path to the image file
    """
    print(f"\n{'='*60}")
    print(f"Evaluating: {image_path}")
    print(f"{'='*60}\n")
    
    # Initialize evaluator
    evaluator = ImageQualityEvaluator()
    
    # Evaluate image
    try:
        results = evaluator.evaluate(image_path)
        
        # Print overall score
        print(f"📊 OVERALL SCORE: {results['overall_score']:.2f} / 5.0")
        print(f"   {'★' * int(results['overall_score'])}{'☆' * (5 - int(results['overall_score']))}")
        
        # Print focus evaluation
        print(f"\n🔍 FOCUS EVALUATION")
        print(f"   Score: {results['focus_score']:.2f} / 5.0")
        print(f"   Laplacian Variance: {results['metrics']['focus']['laplacian_variance']}")
        print(f"   Category: {results['metrics']['focus']['sharpness_category']}")
        
        # Print exposure evaluation
        print(f"\n💡 EXPOSURE EVALUATION")
        print(f"   Score: {results['exposure_score']:.2f} / 5.0")
        print(f"   Mean Brightness: {results['metrics']['exposure']['mean_brightness']:.2f}")
        print(f"   Highlight Clipping: {results['metrics']['exposure']['highlight_clip_percent']:.2f}%")
        print(f"   Shadow Clipping: {results['metrics']['exposure']['shadow_clip_percent']:.2f}%")
        print(f"   Dynamic Range: {results['metrics']['exposure']['dynamic_range']}")
        print(f"   Category: {results['metrics']['exposure']['exposure_category']}")
        
        # Print composition evaluation
        print(f"\n🎨 COMPOSITION EVALUATION")
        print(f"   Score: {results['composition_score']:.2f} / 5.0")
        print(f"   Power Point Alignment: {results['metrics']['composition']['power_point_alignment']:.4f}")
        print(f"   Line Alignment: {results['metrics']['composition']['line_alignment']:.4f}")
        print(f"   Balance Score: {results['metrics']['composition']['balance_score']:.2f}")
        print(f"   Category: {results['metrics']['composition']['composition_category']}")
        
        # Print face detection
        print(f"\n👤 FACE DETECTION")
        print(f"   Faces Detected: {results['faces_detected']}")
        if results['face_locations']:
            print(f"   Face Locations:")
            for i, (x, y, w, h) in enumerate(results['face_locations'], 1):
                print(f"      Face {i}: x={x}, y={y}, width={w}, height={h}")
        
        # Recommendation
        print(f"\n💭 RECOMMENDATION")
        if results['overall_score'] >= 4.0:
            print(f"   ✅ Excellent quality - Recommended for processing")
        elif results['overall_score'] >= 3.0:
            print(f"   ✓ Good quality - Suitable for processing")
        elif results['overall_score'] >= 2.0:
            print(f"   ⚠ Acceptable quality - May need adjustments")
        else:
            print(f"   ❌ Poor quality - Consider rejecting or manual review")
        
        return results
    
    except Exception as e:
        print(f"❌ Error evaluating image: {e}")
        return None


def evaluate_batch(image_paths: list):
    """
    Evaluate multiple images and generate summary statistics.
    
    Args:
        image_paths: List of image file paths
    """
    print(f"\n{'='*60}")
    print(f"BATCH EVALUATION: {len(image_paths)} images")
    print(f"{'='*60}\n")
    
    evaluator = ImageQualityEvaluator()
    results = []
    
    for i, image_path in enumerate(image_paths, 1):
        print(f"[{i}/{len(image_paths)}] Processing: {Path(image_path).name}")
        
        try:
            result = evaluator.evaluate(image_path)
            result['file_path'] = image_path
            results.append(result)
            
            # Quick summary
            print(f"   Overall: {result['overall_score']:.2f} | "
                  f"Focus: {result['focus_score']:.2f} | "
                  f"Exposure: {result['exposure_score']:.2f} | "
                  f"Composition: {result['composition_score']:.2f} | "
                  f"Faces: {result['faces_detected']}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Generate summary statistics
    if results:
        print(f"\n{'='*60}")
        print(f"SUMMARY STATISTICS")
        print(f"{'='*60}\n")
        
        avg_overall = sum(r['overall_score'] for r in results) / len(results)
        avg_focus = sum(r['focus_score'] for r in results) / len(results)
        avg_exposure = sum(r['exposure_score'] for r in results) / len(results)
        avg_composition = sum(r['composition_score'] for r in results) / len(results)
        total_faces = sum(r['faces_detected'] for r in results)
        
        print(f"Total Images Evaluated: {len(results)}")
        print(f"Average Overall Score: {avg_overall:.2f} / 5.0")
        print(f"Average Focus Score: {avg_focus:.2f} / 5.0")
        print(f"Average Exposure Score: {avg_exposure:.2f} / 5.0")
        print(f"Average Composition Score: {avg_composition:.2f} / 5.0")
        print(f"Total Faces Detected: {total_faces}")
        
        # Quality distribution
        excellent = sum(1 for r in results if r['overall_score'] >= 4.0)
        good = sum(1 for r in results if 3.0 <= r['overall_score'] < 4.0)
        acceptable = sum(1 for r in results if 2.0 <= r['overall_score'] < 3.0)
        poor = sum(1 for r in results if r['overall_score'] < 2.0)
        
        print(f"\nQuality Distribution:")
        print(f"   Excellent (≥4.0): {excellent} ({excellent/len(results)*100:.1f}%)")
        print(f"   Good (3.0-3.9): {good} ({good/len(results)*100:.1f}%)")
        print(f"   Acceptable (2.0-2.9): {acceptable} ({acceptable/len(results)*100:.1f}%)")
        print(f"   Poor (<2.0): {poor} ({poor/len(results)*100:.1f}%)")
        
        # Top 5 images
        print(f"\nTop 5 Images by Overall Score:")
        sorted_results = sorted(results, key=lambda x: x['overall_score'], reverse=True)
        for i, result in enumerate(sorted_results[:5], 1):
            filename = Path(result['file_path']).name
            print(f"   {i}. {filename}: {result['overall_score']:.2f}")
    
    return results


def export_results_json(results: list, output_path: str):
    """
    Export evaluation results to JSON file.
    
    Args:
        results: List of evaluation results
        output_path: Path to output JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results exported to: {output_path}")


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single image: python example_image_quality_usage.py <image_path>")
        print("  Batch: python example_image_quality_usage.py <image1> <image2> ...")
        print("  Export JSON: python example_image_quality_usage.py <images...> --output results.json")
        sys.exit(1)
    
    # Parse arguments
    image_paths = []
    output_path = None
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
            i += 2
        else:
            image_paths.append(sys.argv[i])
            i += 1
    
    # Validate image paths
    valid_paths = []
    for path in image_paths:
        if Path(path).exists():
            valid_paths.append(path)
        else:
            print(f"⚠ Warning: File not found: {path}")
    
    if not valid_paths:
        print("❌ No valid image files found")
        sys.exit(1)
    
    # Evaluate images
    if len(valid_paths) == 1:
        # Single image evaluation
        results = evaluate_single_image(valid_paths[0])
        if results and output_path:
            export_results_json([results], output_path)
    else:
        # Batch evaluation
        results = evaluate_batch(valid_paths)
        if results and output_path:
            export_results_json(results, output_path)


if __name__ == '__main__':
    main()
