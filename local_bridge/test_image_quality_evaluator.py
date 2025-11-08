"""
Test suite for Image Quality Evaluator

Tests focus evaluation, exposure evaluation, composition evaluation,
and face detection functionality.
"""

import unittest
import cv2
import numpy as np
import tempfile
import os
from pathlib import Path
from image_quality_evaluator import ImageQualityEvaluator


class TestImageQualityEvaluator(unittest.TestCase):
    """Test cases for ImageQualityEvaluator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = ImageQualityEvaluator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_image(
        self,
        width: int = 640,
        height: int = 480,
        brightness: int = 128,
        blur: int = 0,
        pattern: str = 'gradient'
    ) -> str:
        """
        Create a synthetic test image.
        
        Args:
            width: Image width
            height: Image height
            brightness: Average brightness (0-255)
            blur: Blur kernel size (0 for no blur)
            pattern: Pattern type ('gradient', 'checkerboard', 'solid', 'thirds')
            
        Returns:
            Path to created image file
        """
        # Create base image
        if pattern == 'gradient':
            img = np.zeros((height, width, 3), dtype=np.uint8)
            for i in range(height):
                img[i, :] = int(brightness * i / height)
        
        elif pattern == 'checkerboard':
            img = np.zeros((height, width, 3), dtype=np.uint8)
            square_size = 50
            for i in range(0, height, square_size):
                for j in range(0, width, square_size):
                    if (i // square_size + j // square_size) % 2 == 0:
                        img[i:i+square_size, j:j+square_size] = brightness
        
        elif pattern == 'solid':
            img = np.full((height, width, 3), brightness, dtype=np.uint8)
        
        elif pattern == 'thirds':
            # Create image with elements at rule of thirds intersections
            img = np.full((height, width, 3), brightness, dtype=np.uint8)
            third_h = height // 3
            third_w = width // 3
            
            # Add circles at power points
            for y in [third_h, 2 * third_h]:
                for x in [third_w, 2 * third_w]:
                    cv2.circle(img, (x, y), 30, (255, 255, 255), -1)
        
        else:
            img = np.full((height, width, 3), brightness, dtype=np.uint8)
        
        # Apply blur if requested
        if blur > 0:
            img = cv2.GaussianBlur(img, (blur, blur), 0)
        
        # Save image
        filename = os.path.join(self.temp_dir, f'test_{pattern}_{brightness}_{blur}.jpg')
        cv2.imwrite(filename, img)
        
        return filename
    
    def test_focus_evaluation_sharp_image(self):
        """Test focus evaluation on a sharp image."""
        # Create sharp checkerboard pattern (high frequency content)
        image_path = self._create_test_image(
            pattern='checkerboard',
            brightness=128,
            blur=0
        )
        
        score, metrics = self.evaluator._calculate_focus(cv2.imread(image_path))
        
        # Sharp image should have high Laplacian variance
        self.assertGreater(metrics['laplacian_variance'], 100)
        self.assertGreater(score, 2.0)
        self.assertIn(metrics['sharpness_category'], ['acceptable', 'sharp', 'very_sharp'])
    
    def test_focus_evaluation_blurry_image(self):
        """Test focus evaluation on a blurry image."""
        # Create blurred image
        image_path = self._create_test_image(
            pattern='checkerboard',
            brightness=128,
            blur=15  # Heavy blur
        )
        
        score, metrics = self.evaluator._calculate_focus(cv2.imread(image_path))
        
        # Blurry image should have low Laplacian variance
        self.assertLess(score, 3.0)
        self.assertIn(metrics['sharpness_category'], ['very_blurry', 'blurry', 'acceptable'])
    
    def test_exposure_evaluation_well_exposed(self):
        """Test exposure evaluation on well-exposed image."""
        # Create image with good brightness distribution
        image_path = self._create_test_image(
            pattern='gradient',
            brightness=128
        )
        
        score, metrics = self.evaluator._calculate_exposure(cv2.imread(image_path))
        
        # Well-exposed image should have good score
        self.assertGreater(score, 3.0)
        self.assertLess(metrics['highlight_clip_percent'], 10.0)
        self.assertLess(metrics['shadow_clip_percent'], 10.0)
    
    def test_exposure_evaluation_overexposed(self):
        """Test exposure evaluation on overexposed image."""
        # Create very bright image
        image_path = self._create_test_image(
            pattern='solid',
            brightness=250
        )
        
        score, metrics = self.evaluator._calculate_exposure(cv2.imread(image_path))
        
        # Overexposed image should have lower score
        self.assertLess(score, 4.0)
        self.assertGreater(metrics['mean_brightness'], 200)
    
    def test_exposure_evaluation_underexposed(self):
        """Test exposure evaluation on underexposed image."""
        # Create very dark image
        image_path = self._create_test_image(
            pattern='solid',
            brightness=30
        )
        
        score, metrics = self.evaluator._calculate_exposure(cv2.imread(image_path))
        
        # Underexposed image should have lower score
        self.assertLess(score, 4.0)
        self.assertLess(metrics['mean_brightness'], 80)
    
    def test_composition_evaluation_rule_of_thirds(self):
        """Test composition evaluation with rule of thirds alignment."""
        # Create image with elements at rule of thirds intersections
        image_path = self._create_test_image(
            pattern='thirds',
            brightness=128
        )
        
        score, metrics = self.evaluator._calculate_composition(cv2.imread(image_path))
        
        # Image with rule of thirds alignment should score reasonably
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 5.0)
        self.assertIn('composition_category', metrics)
    
    def test_composition_balance(self):
        """Test visual balance calculation."""
        # Create balanced image
        image_path = self._create_test_image(
            pattern='solid',
            brightness=128
        )
        
        img = cv2.imread(image_path)
        balance_score = self.evaluator._calculate_balance(img)
        
        # Solid color should be perfectly balanced
        self.assertGreater(balance_score, 4.0)
    
    def test_face_detection_availability(self):
        """Test face detection initialization."""
        # Check if face detection is available
        self.assertIsNotNone(self.evaluator.face_detector)
        
        # If enabled, should be either CascadeClassifier or DNN
        if self.evaluator.face_detection_enabled:
            self.assertTrue(
                isinstance(self.evaluator.face_detector, cv2.CascadeClassifier) or
                hasattr(self.evaluator.face_detector, 'setInput')
            )
    
    def test_face_detection_no_faces(self):
        """Test face detection on image without faces."""
        # Create simple pattern without faces
        image_path = self._create_test_image(
            pattern='checkerboard',
            brightness=128
        )
        
        img = cv2.imread(image_path)
        num_faces, locations = self.evaluator._detect_faces(img)
        
        # Should detect 0 faces
        self.assertEqual(num_faces, 0)
        self.assertEqual(len(locations), 0)
    
    def test_overall_evaluation(self):
        """Test complete image evaluation."""
        # Create test image
        image_path = self._create_test_image(
            pattern='checkerboard',
            brightness=128
        )
        
        results = self.evaluator.evaluate(image_path)
        
        # Check all required fields are present
        self.assertIn('focus_score', results)
        self.assertIn('exposure_score', results)
        self.assertIn('composition_score', results)
        self.assertIn('faces_detected', results)
        self.assertIn('face_locations', results)
        self.assertIn('overall_score', results)
        self.assertIn('metrics', results)
        
        # Check score ranges
        self.assertGreaterEqual(results['focus_score'], 0.0)
        self.assertLessEqual(results['focus_score'], 5.0)
        self.assertGreaterEqual(results['exposure_score'], 0.0)
        self.assertLessEqual(results['exposure_score'], 5.0)
        self.assertGreaterEqual(results['composition_score'], 0.0)
        self.assertLessEqual(results['composition_score'], 5.0)
        self.assertGreaterEqual(results['overall_score'], 0.0)
        self.assertLessEqual(results['overall_score'], 5.0)
        
        # Check metrics structure
        self.assertIn('focus', results['metrics'])
        self.assertIn('exposure', results['metrics'])
        self.assertIn('composition', results['metrics'])
    
    def test_overall_score_calculation(self):
        """Test overall score calculation logic."""
        # Test without faces
        score = self.evaluator._calculate_overall_score(4.0, 4.0, 4.0, 0)
        self.assertAlmostEqual(score, 4.0, places=1)
        
        # Test with faces (should get bonus)
        score_with_faces = self.evaluator._calculate_overall_score(4.0, 4.0, 4.0, 2)
        self.assertGreater(score_with_faces, score)
        
        # Test score capping at 5.0
        score_max = self.evaluator._calculate_overall_score(5.0, 5.0, 5.0, 10)
        self.assertLessEqual(score_max, 5.0)
    
    def test_invalid_image_path(self):
        """Test handling of invalid image path."""
        with self.assertRaises(ValueError):
            self.evaluator.evaluate('nonexistent_image.jpg')
    
    def test_sharpness_categorization(self):
        """Test sharpness categorization."""
        self.assertEqual(self.evaluator._categorize_sharpness(50), 'very_blurry')
        self.assertEqual(self.evaluator._categorize_sharpness(200), 'blurry')
        self.assertEqual(self.evaluator._categorize_sharpness(400), 'acceptable')
        self.assertEqual(self.evaluator._categorize_sharpness(700), 'sharp')
        self.assertEqual(self.evaluator._categorize_sharpness(1500), 'very_sharp')
    
    def test_exposure_categorization(self):
        """Test exposure categorization."""
        self.assertEqual(
            self.evaluator._categorize_exposure(128, 0.15, 0.02),
            'overexposed'
        )
        self.assertEqual(
            self.evaluator._categorize_exposure(128, 0.02, 0.15),
            'underexposed'
        )
        self.assertEqual(
            self.evaluator._categorize_exposure(80, 0.02, 0.02),
            'dark'
        )
        self.assertEqual(
            self.evaluator._categorize_exposure(170, 0.02, 0.02),
            'bright'
        )
        self.assertEqual(
            self.evaluator._categorize_exposure(128, 0.02, 0.02),
            'well_exposed'
        )
    
    def test_composition_categorization(self):
        """Test composition categorization."""
        self.assertEqual(self.evaluator._categorize_composition(4.5), 'excellent')
        self.assertEqual(self.evaluator._categorize_composition(3.5), 'good')
        self.assertEqual(self.evaluator._categorize_composition(2.5), 'acceptable')
        self.assertEqual(self.evaluator._categorize_composition(1.5), 'poor')


class TestImageQualityEvaluatorIntegration(unittest.TestCase):
    """Integration tests with real-world scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.evaluator = ImageQualityEvaluator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_batch_evaluation(self):
        """Test evaluating multiple images."""
        # Create multiple test images
        images = []
        for i in range(3):
            img_path = os.path.join(self.temp_dir, f'test_{i}.jpg')
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            cv2.imwrite(img_path, img)
            images.append(img_path)
        
        # Evaluate all images
        results = []
        for img_path in images:
            result = self.evaluator.evaluate(img_path)
            results.append(result)
        
        # Check all evaluations completed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn('overall_score', result)
    
    def test_different_image_sizes(self):
        """Test evaluation with different image sizes."""
        sizes = [(320, 240), (640, 480), (1920, 1080), (4000, 3000)]
        
        for width, height in sizes:
            img_path = os.path.join(self.temp_dir, f'test_{width}x{height}.jpg')
            img = np.full((height, width, 3), 128, dtype=np.uint8)
            cv2.imwrite(img_path, img)
            
            # Should handle all sizes without error
            result = self.evaluator.evaluate(img_path)
            self.assertIsNotNone(result)
            self.assertIn('overall_score', result)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestImageQualityEvaluator))
    suite.addTests(loader.loadTestsFromTestCase(TestImageQualityEvaluatorIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
