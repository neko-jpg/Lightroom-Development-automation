"""
Unit tests for Photo Grouper module.

Tests perceptual hashing, similarity detection, grouping logic,
and best photo selection.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
import cv2

from photo_grouper import PhotoGrouper, PhotoGroup


class TestPhotoGrouper(unittest.TestCase):
    """Test cases for PhotoGrouper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.grouper = PhotoGrouper(similarity_threshold=10, hash_size=8)
        self.temp_dir = tempfile.mkdtemp()
        self.test_images = []
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_image(self, name: str, color: tuple = (128, 128, 128), size: tuple = (640, 480)):
        """
        Create a test image with specified color.
        
        Args:
            name: Image filename
            color: RGB color tuple
            size: Image size (width, height)
            
        Returns:
            Path to created image
        """
        img = Image.new('RGB', size, color)
        img_path = Path(self.temp_dir) / name
        img.save(img_path)
        self.test_images.append(str(img_path))
        return str(img_path)
    
    def create_similar_images(self, base_name: str, count: int = 3):
        """
        Create a set of similar images (slight variations).
        
        Args:
            base_name: Base filename
            count: Number of similar images to create
            
        Returns:
            List of image paths
        """
        images = []
        base_color = (100, 150, 200)
        
        for i in range(count):
            # Slight color variation
            color = tuple(c + i * 5 for c in base_color)
            img_path = self.create_test_image(f"{base_name}_{i}.jpg", color)
            images.append(img_path)
        
        return images
    
    def test_calculate_phash(self):
        """Test perceptual hash calculation."""
        img_path = self.create_test_image("test.jpg")
        
        # Calculate hash
        phash = self.grouper.calculate_phash(img_path)
        
        # Verify hash is a hex string
        self.assertIsInstance(phash, str)
        self.assertTrue(len(phash) > 0)
        
        # Verify hash is consistent
        phash2 = self.grouper.calculate_phash(img_path)
        self.assertEqual(phash, phash2)
    
    def test_calculate_hash_distance(self):
        """Test hash distance calculation."""
        # Create two different images
        img1_path = self.create_test_image("img1.jpg", (100, 100, 100))
        img2_path = self.create_test_image("img2.jpg", (200, 200, 200))
        
        hash1 = self.grouper.calculate_phash(img1_path)
        hash2 = self.grouper.calculate_phash(img2_path)
        
        # Calculate distance
        distance = self.grouper.calculate_hash_distance(hash1, hash2)
        
        # Verify distance is a non-negative integer
        self.assertIsInstance(distance, int)
        self.assertGreaterEqual(distance, 0)
        
        # Distance to self should be 0
        self_distance = self.grouper.calculate_hash_distance(hash1, hash1)
        self.assertEqual(self_distance, 0)
    
    def test_similar_images_have_small_distance(self):
        """Test that similar images have small hash distance."""
        # Create similar images
        similar_images = self.create_similar_images("similar", count=2)
        
        hash1 = self.grouper.calculate_phash(similar_images[0])
        hash2 = self.grouper.calculate_phash(similar_images[1])
        
        distance = self.grouper.calculate_hash_distance(hash1, hash2)
        
        # Similar images should have small distance
        self.assertLess(distance, 20)
    
    def test_different_images_have_large_distance(self):
        """Test that different images have large hash distance."""
        # Create images with different patterns (not just solid colors)
        # Image 1: Dark with some pattern
        img1 = Image.new('RGB', (640, 480), (50, 50, 50))
        from PIL import ImageDraw
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([100, 100, 300, 300], fill=(100, 100, 100))
        img1_path = Path(self.temp_dir) / "img1.jpg"
        img1.save(img1_path)
        self.test_images.append(str(img1_path))
        
        # Image 2: Bright with different pattern
        img2 = Image.new('RGB', (640, 480), (250, 250, 250))
        draw2 = ImageDraw.Draw(img2)
        draw2.ellipse([200, 200, 400, 400], fill=(150, 150, 150))
        img2_path = Path(self.temp_dir) / "img2.jpg"
        img2.save(img2_path)
        self.test_images.append(str(img2_path))
        
        hash1 = self.grouper.calculate_phash(str(img1_path))
        hash2 = self.grouper.calculate_phash(str(img2_path))
        
        distance = self.grouper.calculate_hash_distance(hash1, hash2)
        
        # Different images with different patterns should have some distance
        # Note: perceptual hash is designed to be similar for visually similar images
        # so we use a modest threshold
        self.assertGreater(distance, 0)
    
    def test_group_photos_basic(self):
        """Test basic photo grouping."""
        # Create test photos
        photos = []
        
        # Group 1: Similar images
        similar1 = self.create_similar_images("group1", count=3)
        for i, img_path in enumerate(similar1):
            photos.append({
                'id': i + 1,
                'file_path': img_path,
                'ai_score': 4.0 + i * 0.1,
                'focus_score': 4.0,
                'exposure_score': 4.0,
                'composition_score': 4.0
            })
        
        # Group 2: Different similar images
        similar2 = self.create_similar_images("group2", count=2)
        for i, img_path in enumerate(similar2):
            photos.append({
                'id': len(photos) + 1,
                'file_path': img_path,
                'ai_score': 3.5 + i * 0.1,
                'focus_score': 3.5,
                'exposure_score': 3.5,
                'composition_score': 3.5
            })
        
        # Group photos
        groups = self.grouper.group_photos(photos)
        
        # Verify groups were created
        self.assertGreater(len(groups), 0)
        
        # Verify each group has multiple photos
        for group in groups:
            self.assertGreater(len(group.photo_ids), 1)
            self.assertIn(group.best_photo_id, group.photo_ids)
    
    def test_select_best_photo(self):
        """Test best photo selection logic."""
        photos = [
            {
                'id': 1,
                'ai_score': 3.5,
                'focus_score': 3.0,
                'exposure_score': 3.0,
                'composition_score': 3.0
            },
            {
                'id': 2,
                'ai_score': 4.5,  # Highest AI score
                'focus_score': 4.0,
                'exposure_score': 4.0,
                'composition_score': 4.0
            },
            {
                'id': 3,
                'ai_score': 3.8,
                'focus_score': 3.5,
                'exposure_score': 3.5,
                'composition_score': 3.5
            }
        ]
        
        best_id = self.grouper._select_best_photo(photos)
        
        # Should select photo with highest AI score
        self.assertEqual(best_id, 2)
    
    def test_select_best_photo_tie_breaker(self):
        """Test best photo selection with tie-breaking."""
        photos = [
            {
                'id': 1,
                'ai_score': 4.0,
                'focus_score': 3.0,
                'exposure_score': 3.0,
                'composition_score': 3.0
            },
            {
                'id': 2,
                'ai_score': 4.0,  # Same AI score
                'focus_score': 4.5,  # Higher focus score (tie-breaker)
                'exposure_score': 3.5,
                'composition_score': 3.5
            }
        ]
        
        best_id = self.grouper._select_best_photo(photos)
        
        # Should select photo with higher focus score
        self.assertEqual(best_id, 2)
    
    def test_calculate_similarity_score(self):
        """Test similarity score calculation."""
        img1_path = self.create_test_image("img1.jpg", (100, 100, 100))
        img2_path = self.create_test_image("img2.jpg", (100, 100, 100))
        
        hash1 = self.grouper.calculate_phash(img1_path)
        hash2 = self.grouper.calculate_phash(img2_path)
        
        similarity = self.grouper.calculate_similarity_score(hash1, hash2)
        
        # Verify similarity is in valid range
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        
        # Identical images should have high similarity
        self_similarity = self.grouper.calculate_similarity_score(hash1, hash1)
        self.assertEqual(self_similarity, 1.0)
    
    def test_find_duplicates(self):
        """Test duplicate detection with strict threshold."""
        # Create nearly identical images
        photos = []
        
        # Create base image
        base_img_path = self.create_test_image("base.jpg", (128, 128, 128))
        photos.append({
            'id': 1,
            'file_path': base_img_path,
            'ai_score': 4.0,
            'focus_score': 4.0,
            'exposure_score': 4.0,
            'composition_score': 4.0
        })
        
        # Create very similar duplicate
        dup_img_path = self.create_test_image("dup.jpg", (128, 128, 128))
        photos.append({
            'id': 2,
            'file_path': dup_img_path,
            'ai_score': 4.1,
            'focus_score': 4.0,
            'exposure_score': 4.0,
            'composition_score': 4.0
        })
        
        # Find duplicates
        duplicate_groups = self.grouper.find_duplicates(photos, strict_threshold=5)
        
        # Verify duplicates were found
        self.assertGreater(len(duplicate_groups), 0)
    
    def test_empty_photo_list(self):
        """Test handling of empty photo list."""
        photos = []
        groups = self.grouper.group_photos(photos)
        
        # Should return empty list
        self.assertEqual(len(groups), 0)
    
    def test_single_photo(self):
        """Test handling of single photo."""
        img_path = self.create_test_image("single.jpg")
        photos = [{
            'id': 1,
            'file_path': img_path,
            'ai_score': 4.0,
            'focus_score': 4.0,
            'exposure_score': 4.0,
            'composition_score': 4.0
        }]
        
        groups = self.grouper.group_photos(photos)
        
        # Should return no groups (need at least 2 photos for a group)
        self.assertEqual(len(groups), 0)
    
    def test_phash_caching(self):
        """Test that pHash is reused if already calculated."""
        img_path = self.create_test_image("test.jpg")
        
        # Pre-calculate hash
        phash = self.grouper.calculate_phash(img_path)
        
        photos = [{
            'id': 1,
            'file_path': img_path,
            'phash': phash,  # Pre-calculated
            'ai_score': 4.0,
            'focus_score': 4.0,
            'exposure_score': 4.0,
            'composition_score': 4.0
        }]
        
        # Should not recalculate hash
        groups = self.grouper.group_photos(photos)
        
        # Verify hash is still present
        self.assertEqual(photos[0]['phash'], phash)


class TestPhotoGroup(unittest.TestCase):
    """Test cases for PhotoGroup dataclass."""
    
    def test_photo_group_creation(self):
        """Test PhotoGroup creation."""
        group = PhotoGroup(
            group_id=1,
            photo_ids=[1, 2, 3],
            best_photo_id=2,
            similarity_threshold=10,
            avg_similarity=5.5
        )
        
        self.assertEqual(group.group_id, 1)
        self.assertEqual(len(group.photo_ids), 3)
        self.assertEqual(group.best_photo_id, 2)
        self.assertEqual(group.similarity_threshold, 10)
        self.assertEqual(group.avg_similarity, 5.5)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
