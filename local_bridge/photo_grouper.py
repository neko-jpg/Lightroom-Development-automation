"""
Photo Grouper Module

Implements similar photo grouping using perceptual hashing (pHash).
Groups similar photos together and automatically selects the best photo in each group.

Requirements: 2.3
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
from dataclasses import dataclass
import imagehash
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class PhotoGroup:
    """Represents a group of similar photos."""
    group_id: int
    photo_ids: List[int]
    best_photo_id: int
    similarity_threshold: float
    avg_similarity: float


class PhotoGrouper:
    """
    Groups similar photos using perceptual hashing (pHash).
    
    Uses imagehash library for efficient perceptual hash calculation
    and comparison. Groups photos based on hash distance threshold.
    """
    
    def __init__(
        self,
        similarity_threshold: int = 10,
        hash_size: int = 8
    ):
        """
        Initialize Photo Grouper.
        
        Args:
            similarity_threshold: Maximum hash distance for photos to be considered similar (default: 10)
            hash_size: Size of the perceptual hash (default: 8, resulting in 64-bit hash)
        """
        self.similarity_threshold = similarity_threshold
        self.hash_size = hash_size
        
        logger.info(
            f"Photo Grouper initialized (threshold={similarity_threshold}, hash_size={hash_size})"
        )
    
    def calculate_phash(self, image_path: str) -> str:
        """
        Calculate perceptual hash (pHash) for an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Hexadecimal string representation of the perceptual hash
        """
        try:
            # Load image using PIL
            img = Image.open(image_path)
            
            # Calculate perceptual hash
            phash = imagehash.phash(img, hash_size=self.hash_size)
            
            # Convert to hex string
            hash_str = str(phash)
            
            logger.debug(f"Calculated pHash for {Path(image_path).name}: {hash_str}")
            return hash_str
        
        except Exception as e:
            logger.error(f"Error calculating pHash for {image_path}: {e}")
            raise
    
    def calculate_hash_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two perceptual hashes.
        
        Args:
            hash1: First hash (hex string)
            hash2: Second hash (hex string)
            
        Returns:
            Hamming distance (number of differing bits)
        """
        try:
            # Convert hex strings back to imagehash objects
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            
            # Calculate Hamming distance
            distance = h1 - h2
            
            return distance
        
        except Exception as e:
            logger.error(f"Error calculating hash distance: {e}")
            return 999  # Return large distance on error
    
    def group_photos(
        self,
        photos: List[Dict]
    ) -> List[PhotoGroup]:
        """
        Group similar photos based on perceptual hash similarity.
        
        Args:
            photos: List of photo dictionaries containing:
                - id: Photo ID
                - file_path: Path to image file
                - phash: Perceptual hash (optional, will be calculated if missing)
                - ai_score: AI quality score (for best photo selection)
                
        Returns:
            List of PhotoGroup objects
        """
        try:
            logger.info(f"Grouping {len(photos)} photos...")
            
            # Calculate pHash for photos that don't have it
            for photo in photos:
                if 'phash' not in photo or not photo['phash']:
                    photo['phash'] = self.calculate_phash(photo['file_path'])
            
            # Build similarity matrix
            n = len(photos)
            similarity_matrix = np.zeros((n, n), dtype=int)
            
            for i in range(n):
                for j in range(i + 1, n):
                    distance = self.calculate_hash_distance(
                        photos[i]['phash'],
                        photos[j]['phash']
                    )
                    similarity_matrix[i][j] = distance
                    similarity_matrix[j][i] = distance
            
            # Group photos using connected components
            groups = self._find_connected_groups(similarity_matrix, photos)
            
            logger.info(f"Found {len(groups)} photo groups")
            return groups
        
        except Exception as e:
            logger.error(f"Error grouping photos: {e}")
            raise
    
    def _find_connected_groups(
        self,
        similarity_matrix: np.ndarray,
        photos: List[Dict]
    ) -> List[PhotoGroup]:
        """
        Find connected components in the similarity graph.
        
        Uses Union-Find algorithm to efficiently group similar photos.
        
        Args:
            similarity_matrix: Matrix of hash distances
            photos: List of photo dictionaries
            
        Returns:
            List of PhotoGroup objects
        """
        n = len(photos)
        parent = list(range(n))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Union photos that are similar
        for i in range(n):
            for j in range(i + 1, n):
                if similarity_matrix[i][j] <= self.similarity_threshold:
                    union(i, j)
        
        # Collect groups
        group_map = {}
        for i in range(n):
            root = find(i)
            if root not in group_map:
                group_map[root] = []
            group_map[root].append(i)
        
        # Create PhotoGroup objects
        groups = []
        group_id = 1
        
        for indices in group_map.values():
            if len(indices) > 1:  # Only create groups with multiple photos
                photo_ids = [photos[i]['id'] for i in indices]
                
                # Calculate average similarity within group
                similarities = []
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        similarities.append(similarity_matrix[indices[i]][indices[j]])
                avg_similarity = np.mean(similarities) if similarities else 0
                
                # Select best photo in group
                best_photo_id = self._select_best_photo(
                    [photos[i] for i in indices]
                )
                
                group = PhotoGroup(
                    group_id=group_id,
                    photo_ids=photo_ids,
                    best_photo_id=best_photo_id,
                    similarity_threshold=self.similarity_threshold,
                    avg_similarity=float(avg_similarity)
                )
                
                groups.append(group)
                group_id += 1
                
                logger.debug(
                    f"Group {group.group_id}: {len(photo_ids)} photos, "
                    f"best={best_photo_id}, avg_sim={avg_similarity:.2f}"
                )
        
        return groups
    
    def _select_best_photo(self, photos: List[Dict]) -> int:
        """
        Select the best photo from a group based on quality scores.
        
        Selection criteria (in order of priority):
        1. Highest AI score
        2. Highest focus score
        3. Highest exposure score
        4. Highest composition score
        
        Args:
            photos: List of photo dictionaries
            
        Returns:
            ID of the best photo
        """
        if not photos:
            raise ValueError("Cannot select best photo from empty group")
        
        # Sort by multiple criteria
        best_photo = max(
            photos,
            key=lambda p: (
                p.get('ai_score', 0),
                p.get('focus_score', 0),
                p.get('exposure_score', 0),
                p.get('composition_score', 0)
            )
        )
        
        logger.debug(
            f"Selected best photo: {best_photo['id']} "
            f"(score={best_photo.get('ai_score', 0):.2f})"
        )
        
        return best_photo['id']
    
    def calculate_similarity_score(self, hash1: str, hash2: str) -> float:
        """
        Calculate similarity score between two hashes (0-1 scale).
        
        Args:
            hash1: First hash (hex string)
            hash2: Second hash (hex string)
            
        Returns:
            Similarity score where 1.0 = identical, 0.0 = completely different
        """
        distance = self.calculate_hash_distance(hash1, hash2)
        max_distance = self.hash_size * self.hash_size  # Maximum possible distance
        
        # Convert distance to similarity (inverse)
        similarity = 1.0 - (distance / max_distance)
        
        return max(0.0, min(1.0, similarity))
    
    def find_duplicates(
        self,
        photos: List[Dict],
        strict_threshold: int = 5
    ) -> List[List[int]]:
        """
        Find near-duplicate photos (very similar, likely same shot).
        
        Args:
            photos: List of photo dictionaries
            strict_threshold: Stricter threshold for duplicates (default: 5)
            
        Returns:
            List of duplicate groups (each group is a list of photo IDs)
        """
        # Temporarily use stricter threshold
        original_threshold = self.similarity_threshold
        self.similarity_threshold = strict_threshold
        
        try:
            groups = self.group_photos(photos)
            duplicate_groups = [group.photo_ids for group in groups]
            
            logger.info(f"Found {len(duplicate_groups)} duplicate groups")
            return duplicate_groups
        
        finally:
            # Restore original threshold
            self.similarity_threshold = original_threshold


class PhotoGroupDatabase:
    """
    Database operations for photo grouping.
    
    Handles saving and retrieving photo groups from the database.
    """
    
    def __init__(self, db_session):
        """
        Initialize database handler.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    def save_photo_hash(self, photo_id: int, phash: str):
        """
        Save perceptual hash for a photo.
        
        Args:
            photo_id: Photo ID
            phash: Perceptual hash (hex string)
        """
        try:
            from models.database import Photo
            
            photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                photo.phash = phash
                self.db.commit()
                logger.debug(f"Saved pHash for photo {photo_id}")
            else:
                logger.warning(f"Photo {photo_id} not found in database")
        
        except Exception as e:
            logger.error(f"Error saving photo hash: {e}")
            self.db.rollback()
            raise
    
    def save_group(self, group: PhotoGroup, session_id: Optional[int] = None):
        """
        Save photo group to database.
        
        Args:
            group: PhotoGroup object
            session_id: Optional session ID to associate with group
        """
        try:
            from models.database import PhotoGroup as DBPhotoGroup, Photo
            
            # Create database photo group
            db_group = DBPhotoGroup(
                session_id=session_id,
                similarity_threshold=int(group.similarity_threshold),
                avg_similarity=group.avg_similarity,
                photo_count=len(group.photo_ids),
                best_photo_id=group.best_photo_id
            )
            
            self.db.add(db_group)
            self.db.flush()  # Get the group ID
            
            logger.info(
                f"Saving group {db_group.id}: "
                f"{len(group.photo_ids)} photos, best={group.best_photo_id}"
            )
            
            # Update photos to link to group
            for photo_id in group.photo_ids:
                photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
                if photo:
                    photo.photo_group_id = db_group.id
                    photo.is_best_in_group = (photo_id == group.best_photo_id)
                    logger.debug(
                        f"Photo {photo_id}: group={db_group.id}, "
                        f"best={photo.is_best_in_group}"
                    )
                else:
                    logger.warning(f"Photo {photo_id} not found in database")
            
            self.db.commit()
            return db_group.id
        
        except Exception as e:
            logger.error(f"Error saving group: {e}")
            self.db.rollback()
            raise
    
    def get_groups_for_session(self, session_id: int) -> List[Dict]:
        """
        Retrieve all photo groups for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of photo group dictionaries
        """
        try:
            from models.database import PhotoGroup as DBPhotoGroup, Photo
            
            logger.info(f"Retrieving groups for session {session_id}")
            
            # Query groups
            db_groups = self.db.query(DBPhotoGroup).filter(
                DBPhotoGroup.session_id == session_id
            ).all()
            
            groups = []
            for db_group in db_groups:
                # Get photos in this group
                photos = self.db.query(Photo).filter(
                    Photo.photo_group_id == db_group.id
                ).all()
                
                group_dict = {
                    'id': db_group.id,
                    'session_id': db_group.session_id,
                    'photo_count': db_group.photo_count,
                    'best_photo_id': db_group.best_photo_id,
                    'avg_similarity': db_group.avg_similarity,
                    'similarity_threshold': db_group.similarity_threshold,
                    'photo_ids': [p.id for p in photos],
                    'created_at': db_group.created_at.isoformat() if db_group.created_at else None
                }
                groups.append(group_dict)
            
            logger.info(f"Found {len(groups)} groups for session {session_id}")
            return groups
        
        except Exception as e:
            logger.error(f"Error retrieving groups: {e}")
            raise
    
    def get_best_photos_for_session(self, session_id: int) -> List[int]:
        """
        Get IDs of all best photos in groups for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of photo IDs that are marked as best in their groups
        """
        try:
            from models.database import Photo, PhotoGroup as DBPhotoGroup
            
            # Query photos that are best in their group for this session
            best_photos = self.db.query(Photo.id).join(
                DBPhotoGroup, Photo.photo_group_id == DBPhotoGroup.id
            ).filter(
                DBPhotoGroup.session_id == session_id,
                Photo.is_best_in_group == True
            ).all()
            
            photo_ids = [p.id for p in best_photos]
            logger.info(f"Found {len(photo_ids)} best photos for session {session_id}")
            
            return photo_ids
        
        except Exception as e:
            logger.error(f"Error retrieving best photos: {e}")
            raise


def main():
    """Example usage of Photo Grouper."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python photo_grouper.py <image_dir>")
        sys.exit(1)
    
    image_dir = Path(sys.argv[1])
    
    # Find all images in directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.cr2', '.nef', '.arw'}
    image_files = [
        f for f in image_dir.iterdir()
        if f.suffix.lower() in image_extensions
    ]
    
    if not image_files:
        print(f"No images found in {image_dir}")
        sys.exit(1)
    
    print(f"Found {len(image_files)} images")
    
    # Create photo dictionaries
    photos = []
    for i, img_file in enumerate(image_files, 1):
        photos.append({
            'id': i,
            'file_path': str(img_file),
            'ai_score': 3.0 + (i % 3),  # Dummy scores
            'focus_score': 3.5,
            'exposure_score': 3.5,
            'composition_score': 3.5
        })
    
    # Initialize grouper
    grouper = PhotoGrouper(similarity_threshold=10)
    
    # Group photos
    print("\nGrouping photos...")
    groups = grouper.group_photos(photos)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"PHOTO GROUPING RESULTS")
    print(f"{'='*60}")
    print(f"\nTotal photos: {len(photos)}")
    print(f"Groups found: {len(groups)}")
    print(f"Photos in groups: {sum(len(g.photo_ids) for g in groups)}")
    
    for group in groups:
        print(f"\n--- Group {group.group_id} ---")
        print(f"  Photos: {len(group.photo_ids)}")
        print(f"  Best photo ID: {group.best_photo_id}")
        print(f"  Avg similarity: {group.avg_similarity:.2f}")
        print(f"  Photo IDs: {group.photo_ids}")


if __name__ == '__main__':
    main()
