"""
Example usage of Photo Grouping functionality.

Demonstrates how to:
1. Calculate perceptual hashes for photos
2. Group similar photos together
3. Select the best photo in each group
4. Save grouping results to database
"""

import logging
from pathlib import Path
from models.database import init_db, get_session, Photo, Session as DBSession
from photo_grouper import PhotoGrouper, PhotoGroupDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_grouping():
    """Example: Basic photo grouping."""
    print("\n" + "="*60)
    print("Example 1: Basic Photo Grouping")
    print("="*60)
    
    # Initialize database
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    
    try:
        # Get photos from a session
        session = db.query(DBSession).first()
        if not session:
            print("No sessions found in database. Please import photos first.")
            return
        
        photos = db.query(Photo).filter(Photo.session_id == session.id).all()
        if not photos:
            print(f"No photos found in session {session.id}")
            return
        
        print(f"\nFound {len(photos)} photos in session '{session.name}'")
        
        # Prepare photo data for grouping
        photo_data = []
        for photo in photos:
            photo_data.append({
                'id': photo.id,
                'file_path': photo.file_path,
                'phash': photo.phash,  # Use existing hash if available
                'ai_score': photo.ai_score or 3.0,
                'focus_score': photo.focus_score or 3.0,
                'exposure_score': photo.exposure_score or 3.0,
                'composition_score': photo.composition_score or 3.0
            })
        
        # Initialize grouper
        grouper = PhotoGrouper(similarity_threshold=10)
        
        # Group photos
        print("\nGrouping similar photos...")
        groups = grouper.group_photos(photo_data)
        
        # Display results
        print(f"\nGrouping Results:")
        print(f"  Total photos: {len(photos)}")
        print(f"  Groups found: {len(groups)}")
        print(f"  Photos in groups: {sum(len(g.photo_ids) for g in groups)}")
        
        for group in groups:
            print(f"\n  Group {group.group_id}:")
            print(f"    Photos: {len(group.photo_ids)}")
            print(f"    Best photo ID: {group.best_photo_id}")
            print(f"    Avg similarity: {group.avg_similarity:.2f}")
            print(f"    Photo IDs: {group.photo_ids}")
        
        # Save groups to database
        if groups:
            print("\nSaving groups to database...")
            db_handler = PhotoGroupDatabase(db)
            
            for group in groups:
                group_id = db_handler.save_group(group, session_id=session.id)
                print(f"  Saved group {group_id}")
            
            print("\nGroups saved successfully!")
    
    finally:
        db.close()


def example_calculate_hashes():
    """Example: Calculate and save perceptual hashes for photos."""
    print("\n" + "="*60)
    print("Example 2: Calculate Perceptual Hashes")
    print("="*60)
    
    # Initialize database
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    
    try:
        # Get photos without hashes
        photos = db.query(Photo).filter(Photo.phash == None).limit(10).all()
        
        if not photos:
            print("All photos already have perceptual hashes.")
            return
        
        print(f"\nCalculating hashes for {len(photos)} photos...")
        
        # Initialize grouper and database handler
        grouper = PhotoGrouper()
        db_handler = PhotoGroupDatabase(db)
        
        # Calculate and save hashes
        for i, photo in enumerate(photos, 1):
            try:
                print(f"  [{i}/{len(photos)}] {photo.file_name}...", end=' ')
                
                # Calculate hash
                phash = grouper.calculate_phash(photo.file_path)
                
                # Save to database
                db_handler.save_photo_hash(photo.id, phash)
                
                print(f"✓ {phash}")
            
            except Exception as e:
                print(f"✗ Error: {e}")
        
        print("\nHash calculation complete!")
    
    finally:
        db.close()


def example_find_duplicates():
    """Example: Find near-duplicate photos."""
    print("\n" + "="*60)
    print("Example 3: Find Duplicate Photos")
    print("="*60)
    
    # Initialize database
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    
    try:
        # Get photos from a session
        session = db.query(DBSession).first()
        if not session:
            print("No sessions found in database.")
            return
        
        photos = db.query(Photo).filter(
            Photo.session_id == session.id,
            Photo.phash != None
        ).all()
        
        if len(photos) < 2:
            print("Need at least 2 photos with hashes to find duplicates.")
            return
        
        print(f"\nSearching for duplicates among {len(photos)} photos...")
        
        # Prepare photo data
        photo_data = []
        for photo in photos:
            photo_data.append({
                'id': photo.id,
                'file_path': photo.file_path,
                'phash': photo.phash,
                'ai_score': photo.ai_score or 3.0,
                'focus_score': photo.focus_score or 3.0,
                'exposure_score': photo.exposure_score or 3.0,
                'composition_score': photo.composition_score or 3.0
            })
        
        # Find duplicates with strict threshold
        grouper = PhotoGrouper()
        duplicate_groups = grouper.find_duplicates(photo_data, strict_threshold=5)
        
        # Display results
        if duplicate_groups:
            print(f"\nFound {len(duplicate_groups)} duplicate groups:")
            
            for i, group in enumerate(duplicate_groups, 1):
                print(f"\n  Duplicate Group {i}:")
                print(f"    Photo IDs: {group}")
                
                # Show photo details
                for photo_id in group:
                    photo = next(p for p in photos if p.id == photo_id)
                    print(f"      - {photo.file_name} (score: {photo.ai_score:.2f})")
        else:
            print("\nNo duplicates found.")
    
    finally:
        db.close()


def example_get_best_photos():
    """Example: Get best photos from groups."""
    print("\n" + "="*60)
    print("Example 4: Get Best Photos from Groups")
    print("="*60)
    
    # Initialize database
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    
    try:
        # Get a session
        session = db.query(DBSession).first()
        if not session:
            print("No sessions found in database.")
            return
        
        # Get groups for session
        db_handler = PhotoGroupDatabase(db)
        groups = db_handler.get_groups_for_session(session.id)
        
        if not groups:
            print(f"No photo groups found for session '{session.name}'")
            return
        
        print(f"\nPhoto groups in session '{session.name}':")
        print(f"  Total groups: {len(groups)}")
        
        # Get best photos
        best_photo_ids = db_handler.get_best_photos_for_session(session.id)
        
        print(f"\nBest photos selected from groups:")
        print(f"  Total: {len(best_photo_ids)}")
        
        # Show details of best photos
        for photo_id in best_photo_ids:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                print(f"\n  Photo ID {photo_id}:")
                print(f"    File: {photo.file_name}")
                print(f"    AI Score: {photo.ai_score:.2f}")
                print(f"    Focus: {photo.focus_score:.2f}")
                print(f"    Exposure: {photo.exposure_score:.2f}")
                print(f"    Composition: {photo.composition_score:.2f}")
    
    finally:
        db.close()


def example_similarity_comparison():
    """Example: Compare similarity between two photos."""
    print("\n" + "="*60)
    print("Example 5: Compare Photo Similarity")
    print("="*60)
    
    # Initialize database
    init_db('sqlite:///data/junmai.db')
    db = get_session()
    
    try:
        # Get two photos with hashes
        photos = db.query(Photo).filter(Photo.phash != None).limit(2).all()
        
        if len(photos) < 2:
            print("Need at least 2 photos with hashes for comparison.")
            return
        
        photo1, photo2 = photos[0], photos[1]
        
        print(f"\nComparing photos:")
        print(f"  Photo 1: {photo1.file_name}")
        print(f"  Photo 2: {photo2.file_name}")
        
        # Calculate similarity
        grouper = PhotoGrouper()
        
        # Hash distance
        distance = grouper.calculate_hash_distance(photo1.phash, photo2.phash)
        print(f"\nHash distance: {distance}")
        
        # Similarity score (0-1)
        similarity = grouper.calculate_similarity_score(photo1.phash, photo2.phash)
        print(f"Similarity score: {similarity:.4f} ({similarity*100:.2f}%)")
        
        # Interpretation
        if distance <= 5:
            print("Interpretation: Near duplicates (very similar)")
        elif distance <= 10:
            print("Interpretation: Similar photos (likely same scene)")
        elif distance <= 20:
            print("Interpretation: Somewhat similar")
        else:
            print("Interpretation: Different photos")
    
    finally:
        db.close()


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("PHOTO GROUPING EXAMPLES")
    print("="*60)
    
    try:
        # Example 1: Calculate hashes
        example_calculate_hashes()
        
        # Example 2: Basic grouping
        example_basic_grouping()
        
        # Example 3: Find duplicates
        example_find_duplicates()
        
        # Example 4: Get best photos
        example_get_best_photos()
        
        # Example 5: Similarity comparison
        example_similarity_comparison()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
    
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == '__main__':
    main()
