"""
Integration test for AI Selector with Image Quality Evaluator

This test verifies that the AI Selector correctly integrates
image quality evaluation with EXIF analysis and context recognition.
"""

import unittest
import cv2
import numpy as np
import tempfile
import os
from pathlib import Path

# Import components
try:
    from ai_selector import AISelector
    from image_quality_evaluator import ImageQualityEvaluator
    AI_SELECTOR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import AI Selector: {e}")
    AI_SELECTOR_AVAILABLE = False


@unittest.skipIf(not AI_SELECTOR_AVAILABLE, "AI Selector not available")
class TestAISelectorIntegration(unittest.TestCase):
    """Integration tests for AI Selector."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.selector = AISelector()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_image(self, filename: str, quality: str = 'good') -> str:
        """
        Create a test image with specified quality.
        
        Args:
            filename: Output filename
            quality: 'good', 'poor', or 'excellent'
            
        Returns:
            Path to created image
        """
        if quality == 'excellent':
            # Sharp, well-exposed, good composition
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            # Create checkerboard pattern (sharp)
            square_size = 40
            for i in range(0, 480, square_size):
                for j in range(0, 640, square_size):
                    if (i // square_size + j // square_size) % 2 == 0:
                        img[i:i+square_size, j:j+square_size] = 128
            # Add elements at rule of thirds
            cv2.circle(img, (213, 160), 30, (255, 255, 255), -1)
            cv2.circle(img, (426, 160), 30, (255, 255, 255), -1)
        
        elif quality == 'poor':
            # Blurry, poorly exposed
            img = np.full((480, 640, 3), 30, dtype=np.uint8)  # Dark
            img = cv2.GaussianBlur(img, (21, 21), 0)  # Blurry
        
        else:  # 'good'
            # Decent quality
            img = np.full((480, 640, 3), 128, dtype=np.uint8)
            # Add some detail
            for i in range(0, 480, 80):
                cv2.line(img, (0, i), (640, i), (150, 150, 150), 2)
        
        filepath = os.path.join(self.temp_dir, filename)
        cv2.imwrite(filepath, img)
        return filepath
    
    def test_evaluate_excellent_image(self):
        """Test evaluation of excellent quality image."""
        image_path = self._create_test_image('excellent.jpg', 'excellent')
        
        result = self.selector.evaluate(image_path)
        
        # Check result structure
        self.assertIn('overall_score', result)
        self.assertIn('quality', result)
        self.assertIn('recommendation', result)
        self.assertIn('tags', result)
        
        # Excellent image should score high
        self.assertGreater(result['overall_score'], 3.0)
        
        # Should be approved or at least reviewed
        self.assertIn(result['recommendation'], ['approve', 'review'])
    
    def test_evaluate_poor_image(self):
        """Test evaluation of poor quality image."""
        image_path = self._create_test_image('poor.jpg', 'poor')
        
        result = self.selector.evaluate(image_path)
        
        # Poor image should score low
        self.assertLess(result['overall_score'], 3.5)
        
        # Should be rejected or reviewed
        self.assertIn(result['recommendation'], ['reject', 'review'])
    
    def test_batch_evaluation(self):
        """Test batch evaluation of multiple images."""
        # Create test images
        images = [
            self._create_test_image('img1.jpg', 'excellent'),
            self._create_test_image('img2.jpg', 'good'),
            self._create_test_image('img3.jpg', 'poor')
        ]
        
        results = self.selector.batch_evaluate(images)
        
        # Should have results for all images
        self.assertEqual(len(results), 3)
        
        # All results should have required fields
        for result in results:
            self.assertIn('overall_score', result)
            self.assertIn('recommendation', result)
    
    def test_filter_by_quality(self):
        """Test filtering images by quality threshold."""
        # Create test images with varying quality
        images = [
            self._create_test_image('high1.jpg', 'excellent'),
            self._create_test_image('high2.jpg', 'excellent'),
            self._create_test_image('low1.jpg', 'poor'),
            self._create_test_image('low2.jpg', 'poor')
        ]
        
        # Filter with threshold
        filtered = self.selector.filter_by_quality(images, min_score=3.0)
        
        # Should filter out poor quality images
        self.assertGreater(len(filtered), 0)
        self.assertLess(len(filtered), len(images))
    
    def test_tag_generation(self):
        """Test automatic tag generation."""
        image_path = self._create_test_image('tagged.jpg', 'excellent')
        
        result = self.selector.evaluate(image_path)
        
        # Should have tags
        self.assertIsInstance(result['tags'], list)
        self.assertGreater(len(result['tags']), 0)
    
    def test_quality_metrics_included(self):
        """Test that quality metrics are included in results."""
        image_path = self._create_test_image('metrics.jpg', 'good')
        
        result = self.selector.evaluate(image_path)
        
        # Check quality scores
        self.assertIn('focus_score', result['quality'])
        self.assertIn('exposure_score', result['quality'])
        self.assertIn('composition_score', result['quality'])
        self.assertIn('faces_detected', result['quality'])
        
        # Check metrics details
        self.assertIn('metrics', result)
        self.assertIn('quality_metrics', result['metrics'])


class TestImageQualityEvaluatorStandalone(unittest.TestCase):
    """Standalone tests for Image Quality Evaluator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = ImageQualityEvaluator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_evaluator_initialization(self):
        """Test that evaluator initializes correctly."""
        self.assertIsNotNone(self.evaluator)
        self.assertIsNotNone(self.evaluator.face_detector)
    
    def test_basic_evaluation(self):
        """Test basic image evaluation."""
        # Create simple test image
        img = np.full((480, 640, 3), 128, dtype=np.uint8)
        img_path = os.path.join(self.temp_dir, 'test.jpg')
        cv2.imwrite(img_path, img)
        
        result = self.evaluator.evaluate(img_path)
        
        # Check all required fields
        required_fields = [
            'focus_score', 'exposure_score', 'composition_score',
            'faces_detected', 'face_locations', 'overall_score', 'metrics'
        ]
        for field in required_fields:
            self.assertIn(field, result)
        
        # Check score ranges
        self.assertGreaterEqual(result['focus_score'], 0.0)
        self.assertLessEqual(result['focus_score'], 5.0)
        self.assertGreaterEqual(result['exposure_score'], 0.0)
        self.assertLessEqual(result['exposure_score'], 5.0)
        self.assertGreaterEqual(result['composition_score'], 0.0)
        self.assertLessEqual(result['composition_score'], 5.0)
        self.assertGreaterEqual(result['overall_score'], 0.0)
        self.assertLessEqual(result['overall_score'], 5.0)


def run_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    if AI_SELECTOR_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestAISelectorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestImageQualityEvaluatorStandalone))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
