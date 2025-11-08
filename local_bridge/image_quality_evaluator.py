"""
Image Quality Evaluator Module

This module provides comprehensive image quality evaluation including:
- Focus evaluation using Laplacian variance
- Exposure evaluation using histogram analysis
- Composition evaluation using Rule of Thirds
- Face detection using OpenCV DNN

Requirements: 2.2, 2.3
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class ImageQualityEvaluator:
    """
    Evaluates image quality across multiple dimensions:
    - Focus (sharpness)
    - Exposure (brightness distribution)
    - Composition (rule of thirds)
    - Face detection
    """
    
    def __init__(self, face_detection_model_path: Optional[str] = None):
        """
        Initialize the image quality evaluator.
        
        Args:
            face_detection_model_path: Path to OpenCV DNN face detection model
        """
        self.face_detector = None
        self.face_detection_enabled = False
        
        # Try to load face detection model
        if face_detection_model_path:
            self._load_face_detector(face_detection_model_path)
        else:
            # Try default paths
            self._try_load_default_face_detector()
    
    def _load_face_detector(self, model_path: str) -> bool:
        """Load OpenCV DNN face detection model."""
        try:
            if not os.path.exists(model_path):
                logger.warning(f"Face detection model not found at {model_path}")
                return False
            
            # Load the model (assuming Caffe model format)
            prototxt_path = model_path.replace('.caffemodel', '.prototxt')
            if os.path.exists(prototxt_path):
                self.face_detector = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
                self.face_detection_enabled = True
                logger.info("Face detection model loaded successfully")
                return True
            else:
                logger.warning(f"Prototxt file not found: {prototxt_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to load face detection model: {e}")
            return False
    
    def _try_load_default_face_detector(self):
        """Try to load face detector from default locations."""
        # Common paths for OpenCV DNN models
        default_paths = [
            "models/deploy.prototxt",
            "models/res10_300x300_ssd_iter_140000.caffemodel",
            "../models/deploy.prototxt",
            "../models/res10_300x300_ssd_iter_140000.caffemodel"
        ]
        
        # Try Haar Cascade as fallback
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_detector = cv2.CascadeClassifier(cascade_path)
            if not self.face_detector.empty():
                self.face_detection_enabled = True
                logger.info("Using Haar Cascade for face detection (fallback)")
                return True
        except Exception as e:
            logger.warning(f"Could not load Haar Cascade: {e}")
        
        logger.warning("Face detection disabled - no model found")
        return False
    
    def evaluate(self, image_path: str) -> Dict:
        """
        Perform comprehensive image quality evaluation.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing evaluation results:
            {
                'focus_score': float (0-5),
                'exposure_score': float (0-5),
                'composition_score': float (0-5),
                'faces_detected': int,
                'face_locations': List[Tuple[int, int, int, int]],
                'overall_score': float (0-5),
                'metrics': Dict with detailed metrics
            }
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Perform individual evaluations
            focus_score, focus_metrics = self._calculate_focus(img)
            exposure_score, exposure_metrics = self._calculate_exposure(img)
            composition_score, composition_metrics = self._calculate_composition(img)
            faces, face_locations = self._detect_faces(img)
            
            # Calculate overall score (weighted average)
            overall_score = self._calculate_overall_score(
                focus_score, exposure_score, composition_score, faces
            )
            
            return {
                'focus_score': round(focus_score, 2),
                'exposure_score': round(exposure_score, 2),
                'composition_score': round(composition_score, 2),
                'faces_detected': faces,
                'face_locations': face_locations,
                'overall_score': round(overall_score, 2),
                'metrics': {
                    'focus': focus_metrics,
                    'exposure': exposure_metrics,
                    'composition': composition_metrics
                }
            }
        
        except Exception as e:
            logger.error(f"Error evaluating image {image_path}: {e}")
            raise
    
    def _calculate_focus(self, img: np.ndarray) -> Tuple[float, Dict]:
        """
        Calculate focus score using Laplacian variance.
        
        Higher variance indicates sharper image.
        
        Args:
            img: Input image (BGR format)
            
        Returns:
            Tuple of (score 0-5, metrics dict)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # Normalize to 0-5 scale
        # Typical values: <100 (blurry), 100-500 (acceptable), >500 (sharp)
        if variance < 100:
            score = variance / 100 * 2.0  # 0-2 for very blurry
        elif variance < 500:
            score = 2.0 + (variance - 100) / 400 * 2.0  # 2-4 for acceptable
        else:
            score = 4.0 + min((variance - 500) / 500, 1.0)  # 4-5 for sharp
        
        score = min(score, 5.0)
        
        metrics = {
            'laplacian_variance': round(variance, 2),
            'sharpness_category': self._categorize_sharpness(variance)
        }
        
        return score, metrics
    
    def _categorize_sharpness(self, variance: float) -> str:
        """Categorize sharpness based on Laplacian variance."""
        if variance < 100:
            return 'very_blurry'
        elif variance < 300:
            return 'blurry'
        elif variance < 500:
            return 'acceptable'
        elif variance < 1000:
            return 'sharp'
        else:
            return 'very_sharp'
    
    def _calculate_exposure(self, img: np.ndarray) -> Tuple[float, Dict]:
        """
        Calculate exposure score using histogram analysis.
        
        Evaluates:
        - Overall brightness
        - Highlight clipping
        - Shadow clipping
        - Histogram distribution
        
        Args:
            img: Input image (BGR format)
            
        Returns:
            Tuple of (score 0-5, metrics dict)
        """
        # Convert to grayscale for luminance analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()  # Normalize
        
        # Calculate metrics
        mean_brightness = gray.mean()
        std_brightness = gray.std()
        
        # Check for clipping
        highlight_clip = hist[250:].sum()  # Percentage of near-white pixels
        shadow_clip = hist[:5].sum()  # Percentage of near-black pixels
        
        # Calculate histogram spread (dynamic range)
        cumsum = np.cumsum(hist)
        p5 = np.searchsorted(cumsum, 0.05)  # 5th percentile
        p95 = np.searchsorted(cumsum, 0.95)  # 95th percentile
        dynamic_range = p95 - p5
        
        # Score calculation
        score = 5.0
        
        # Penalize for poor brightness (ideal: 100-150)
        if mean_brightness < 80 or mean_brightness > 170:
            score -= 1.0
        elif mean_brightness < 90 or mean_brightness > 160:
            score -= 0.5
        
        # Penalize for clipping
        if highlight_clip > 0.05:  # More than 5% clipped highlights
            score -= min(highlight_clip * 10, 1.5)
        if shadow_clip > 0.05:  # More than 5% clipped shadows
            score -= min(shadow_clip * 10, 1.5)
        
        # Penalize for poor dynamic range
        if dynamic_range < 100:
            score -= 1.0
        elif dynamic_range < 150:
            score -= 0.5
        
        # Ensure score is in valid range
        score = max(0.0, min(score, 5.0))
        
        metrics = {
            'mean_brightness': round(mean_brightness, 2),
            'std_brightness': round(std_brightness, 2),
            'highlight_clip_percent': round(highlight_clip * 100, 2),
            'shadow_clip_percent': round(shadow_clip * 100, 2),
            'dynamic_range': int(dynamic_range),
            'exposure_category': self._categorize_exposure(mean_brightness, highlight_clip, shadow_clip)
        }
        
        return score, metrics
    
    def _categorize_exposure(self, mean_brightness: float, highlight_clip: float, shadow_clip: float) -> str:
        """Categorize exposure quality."""
        if highlight_clip > 0.1:
            return 'overexposed'
        elif shadow_clip > 0.1:
            return 'underexposed'
        elif mean_brightness < 90:
            return 'dark'
        elif mean_brightness > 160:
            return 'bright'
        else:
            return 'well_exposed'
    
    def _calculate_composition(self, img: np.ndarray) -> Tuple[float, Dict]:
        """
        Calculate composition score using Rule of Thirds.
        
        Evaluates how well important elements align with rule of thirds grid.
        
        Args:
            img: Input image (BGR format)
            
        Returns:
            Tuple of (score 0-5, metrics dict)
        """
        height, width = img.shape[:2]
        
        # Define rule of thirds lines
        third_h = height // 3
        third_w = width // 3
        
        # Power points (intersections of rule of thirds lines)
        power_points = [
            (third_w, third_h),
            (2 * third_w, third_h),
            (third_w, 2 * third_h),
            (2 * third_w, 2 * third_h)
        ]
        
        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Calculate edge density at power points and lines
        power_point_scores = []
        roi_size = min(width, height) // 10  # Region of interest around power points
        
        for px, py in power_points:
            # Extract region around power point
            x1 = max(0, px - roi_size // 2)
            x2 = min(width, px + roi_size // 2)
            y1 = max(0, py - roi_size // 2)
            y2 = min(height, py + roi_size // 2)
            
            roi = edges[y1:y2, x1:x2]
            edge_density = roi.sum() / (roi.size * 255)  # Normalize
            power_point_scores.append(edge_density)
        
        # Calculate edge density along rule of thirds lines
        line_scores = []
        line_width = max(1, min(width, height) // 50)
        
        # Vertical lines
        for x in [third_w, 2 * third_w]:
            x1 = max(0, x - line_width)
            x2 = min(width, x + line_width)
            line_roi = edges[:, x1:x2]
            line_scores.append(line_roi.sum() / (line_roi.size * 255))
        
        # Horizontal lines
        for y in [third_h, 2 * third_h]:
            y1 = max(0, y - line_width)
            y2 = min(height, y + line_width)
            line_roi = edges[y1:y2, :]
            line_scores.append(line_roi.sum() / (line_roi.size * 255))
        
        # Calculate overall composition score
        avg_power_point_score = np.mean(power_point_scores)
        avg_line_score = np.mean(line_scores)
        
        # Normalize to 0-5 scale
        # Higher edge density at power points/lines indicates better composition
        composition_score = (avg_power_point_score * 3 + avg_line_score * 2) * 50
        composition_score = min(composition_score, 5.0)
        
        # Add bonus for balanced composition
        balance_score = self._calculate_balance(img)
        composition_score = (composition_score * 0.7 + balance_score * 0.3)
        
        metrics = {
            'power_point_alignment': round(avg_power_point_score, 4),
            'line_alignment': round(avg_line_score, 4),
            'balance_score': round(balance_score, 2),
            'composition_category': self._categorize_composition(composition_score)
        }
        
        return composition_score, metrics
    
    def _calculate_balance(self, img: np.ndarray) -> float:
        """
        Calculate visual balance by comparing left/right and top/bottom halves.
        
        Returns score 0-5 where 5 is perfectly balanced.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # Split into halves
        left = gray[:, :width//2]
        right = gray[:, width//2:]
        top = gray[:height//2, :]
        bottom = gray[height//2:, :]
        
        # Calculate mean brightness for each half
        left_mean = left.mean()
        right_mean = right.mean()
        top_mean = top.mean()
        bottom_mean = bottom.mean()
        
        # Calculate balance (lower difference = better balance)
        lr_diff = abs(left_mean - right_mean) / 255
        tb_diff = abs(top_mean - bottom_mean) / 255
        
        # Convert to 0-5 score (perfect balance = 5)
        balance_score = 5.0 - (lr_diff + tb_diff) * 5
        balance_score = max(0.0, min(balance_score, 5.0))
        
        return balance_score
    
    def _categorize_composition(self, score: float) -> str:
        """Categorize composition quality."""
        if score >= 4.0:
            return 'excellent'
        elif score >= 3.0:
            return 'good'
        elif score >= 2.0:
            return 'acceptable'
        else:
            return 'poor'
    
    def _detect_faces(self, img: np.ndarray) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """
        Detect faces in the image using OpenCV DNN or Haar Cascade.
        
        Args:
            img: Input image (BGR format)
            
        Returns:
            Tuple of (number of faces, list of face bounding boxes)
            Each bounding box is (x, y, width, height)
        """
        if not self.face_detection_enabled:
            return 0, []
        
        try:
            # Check if using Haar Cascade or DNN
            if isinstance(self.face_detector, cv2.CascadeClassifier):
                return self._detect_faces_haar(img)
            else:
                return self._detect_faces_dnn(img)
        
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return 0, []
    
    def _detect_faces_haar(self, img: np.ndarray) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """Detect faces using Haar Cascade."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        face_locations = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
        return len(faces), face_locations
    
    def _detect_faces_dnn(self, img: np.ndarray) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """Detect faces using OpenCV DNN."""
        height, width = img.shape[:2]
        
        # Prepare blob for DNN
        blob = cv2.dnn.blobFromImage(
            cv2.resize(img, (300, 300)),
            1.0,
            (300, 300),
            (104.0, 177.0, 123.0)
        )
        
        self.face_detector.setInput(blob)
        detections = self.face_detector.forward()
        
        faces = []
        confidence_threshold = 0.5
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                (x1, y1, x2, y2) = box.astype("int")
                
                # Convert to (x, y, w, h) format
                x = max(0, x1)
                y = max(0, y1)
                w = min(width - x, x2 - x1)
                h = min(height - y, y2 - y1)
                
                faces.append((x, y, w, h))
        
        return len(faces), faces
    
    def _calculate_overall_score(
        self,
        focus_score: float,
        exposure_score: float,
        composition_score: float,
        faces_detected: int
    ) -> float:
        """
        Calculate overall image quality score.
        
        Weighted average with bonus for face detection.
        
        Args:
            focus_score: Focus quality (0-5)
            exposure_score: Exposure quality (0-5)
            composition_score: Composition quality (0-5)
            faces_detected: Number of faces detected
            
        Returns:
            Overall score (0-5)
        """
        # Base weights
        weights = {
            'focus': 0.35,
            'exposure': 0.35,
            'composition': 0.30
        }
        
        # Calculate weighted average
        overall = (
            focus_score * weights['focus'] +
            exposure_score * weights['exposure'] +
            composition_score * weights['composition']
        )
        
        # Bonus for face detection (portraits are often more valuable)
        if faces_detected > 0:
            face_bonus = min(faces_detected * 0.1, 0.3)  # Max 0.3 bonus
            overall = min(overall + face_bonus, 5.0)
        
        return overall


def main():
    """Example usage of ImageQualityEvaluator."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python image_quality_evaluator.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Initialize evaluator
    evaluator = ImageQualityEvaluator()
    
    # Evaluate image
    print(f"Evaluating: {image_path}")
    results = evaluator.evaluate(image_path)
    
    # Print results
    print("\n=== Image Quality Evaluation Results ===")
    print(f"Overall Score: {results['overall_score']:.2f} / 5.0")
    print(f"\nFocus Score: {results['focus_score']:.2f} / 5.0")
    print(f"  - Laplacian Variance: {results['metrics']['focus']['laplacian_variance']}")
    print(f"  - Category: {results['metrics']['focus']['sharpness_category']}")
    
    print(f"\nExposure Score: {results['exposure_score']:.2f} / 5.0")
    print(f"  - Mean Brightness: {results['metrics']['exposure']['mean_brightness']}")
    print(f"  - Highlight Clipping: {results['metrics']['exposure']['highlight_clip_percent']}%")
    print(f"  - Shadow Clipping: {results['metrics']['exposure']['shadow_clip_percent']}%")
    print(f"  - Category: {results['metrics']['exposure']['exposure_category']}")
    
    print(f"\nComposition Score: {results['composition_score']:.2f} / 5.0")
    print(f"  - Power Point Alignment: {results['metrics']['composition']['power_point_alignment']}")
    print(f"  - Balance Score: {results['metrics']['composition']['balance_score']}")
    print(f"  - Category: {results['metrics']['composition']['composition_category']}")
    
    print(f"\nFaces Detected: {results['faces_detected']}")
    if results['face_locations']:
        print(f"  Face Locations: {results['face_locations']}")


if __name__ == '__main__':
    main()
