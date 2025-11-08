# Photo Grouping Implementation Summary

## Overview

Implementation of similar photo grouping functionality using perceptual hashing (pHash). This feature automatically groups similar photos together and selects the best photo in each group based on quality scores.

**Implementation Date:** 2025-11-08  
**Task:** 10. 類似写真グループ化機能の実装  
**Requirements:** 2.3

## Features Implemented

### 1. Perceptual Hash (pHash) Calculation
- Uses `imagehash` library for efficient perceptual hash computation
- 64-bit hash (8x8 hash size) for good balance between accuracy and performance
- Consistent hash generation for identical images
- Handles various image formats (JPEG, PNG, RAW)

### 2. Similarity Detection
- Hamming distance calculation between perceptual hashes
- Configurable similarity threshold (default: 10 bits difference)
- Similarity score conversion (0-1 scale) for intuitive understanding
- Efficient comparison using hash-based approach

### 3. Photo Grouping
- Union-Find algorithm for efficient connected component detection
- Groups photos based on similarity threshold
- Calculates average similarity within each group
- Only creates groups with 2+ photos (singles remain ungrouped)

### 4. Best Photo Selection
- Multi-criteria selection algorithm:
  1. Highest AI score (primary)
  2. Highest focus score (tie-breaker)
  3. Highest exposure score (secondary tie-breaker)
  4. Highest composition score (tertiary tie-breaker)
- Automatic selection of best representative from each group

### 5. Database Integration
- New `photo_groups` table for storing group metadata
- Extended `photos` table with:
  - `phash`: Perceptual hash storage
  - `photo_group_id`: Link to group
  - `is_best_in_group`: Flag for best photo
- Database migration script (002_add_photo_grouping.py)
- Efficient querying with proper indexes

### 6. Duplicate Detection
- Strict threshold mode for finding near-duplicates
- Separate from general grouping (stricter criteria)
- Useful for identifying accidental duplicate imports

## Files Created

### Core Implementation
- **`photo_grouper.py`** (420 lines)
  - `PhotoGrouper` class: Main grouping logic
  - `PhotoGroup` dataclass: Group representation
  - `PhotoGroupDatabase` class: Database operations

### Testing
- **`test_photo_grouper.py`** (350 lines)
  - 13 comprehensive unit tests
  - All tests passing ✓
  - Coverage of core functionality

### Examples
- **`example_photo_grouping_usage.py`** (350 lines)
  - 5 practical usage examples
  - Database integration demonstrations
  - Real-world workflow scenarios

### Database
- **`alembic/versions/002_add_photo_grouping.py`**
  - Migration for new schema
  - Upgrade and downgrade paths
  - Index creation for performance

### Documentation
- **`PHOTO_GROUPING_IMPLEMENTATION.md`** (this file)

## Files Modified

### Database Schema
- **`models/database.py`**
  - Added `PhotoGroup` model class
  - Extended `Photo` model with grouping fields
  - Added indexes for efficient queries

### Dependencies
- **`requirements.txt`**
  - Added `imagehash==4.3.1`
  - Added `Pillow==10.4.0`

## API Reference

### PhotoGrouper Class

```python
from photo_grouper import PhotoGrouper

# Initialize
grouper = PhotoGrouper(
    similarity_threshold=10,  # Max hash distance for similarity
    hash_size=8              # Hash size (8x8 = 64-bit)
)

# Calculate perceptual hash
phash = grouper.calculate_phash(image_path)

# Group photos
photos = [
    {
        'id': 1,
        'file_path': '/path/to/photo1.jpg',
        'ai_score': 4.5,
        'focus_score': 4.2,
        'exposure_score': 4.0,
        'composition_score': 4.3
    },
    # ... more photos
]
groups = grouper.group_photos(photos)

# Find duplicates (strict threshold)
duplicates = grouper.find_duplicates(photos, strict_threshold=5)

# Calculate similarity
similarity = grouper.calculate_similarity_score(hash1, hash2)
```

### PhotoGroupDatabase Class

```python
from photo_grouper import PhotoGroupDatabase
from models.database import get_session

# Initialize
db = get_session()
db_handler = PhotoGroupDatabase(db)

# Save perceptual hash
db_handler.save_photo_hash(photo_id, phash)

# Save group to database
group_id = db_handler.save_group(group, session_id=session_id)

# Get groups for session
groups = db_handler.get_groups_for_session(session_id)

# Get best photos
best_photo_ids = db_handler.get_best_photos_for_session(session_id)
```

## Usage Examples

### Example 1: Basic Grouping Workflow

```python
from models.database import init_db, get_session, Photo
from photo_grouper import PhotoGrouper, PhotoGroupDatabase

# Initialize
init_db('sqlite:///data/junmai.db')
db = get_session()

# Get photos
photos = db.query(Photo).filter(Photo.session_id == session_id).all()

# Prepare data
photo_data = [
    {
        'id': p.id,
        'file_path': p.file_path,
        'ai_score': p.ai_score,
        'focus_score': p.focus_score,
        'exposure_score': p.exposure_score,
        'composition_score': p.composition_score
    }
    for p in photos
]

# Group photos
grouper = PhotoGrouper(similarity_threshold=10)
groups = grouper.group_photos(photo_data)

# Save to database
db_handler = PhotoGroupDatabase(db)
for group in groups:
    db_handler.save_group(group, session_id=session_id)
```

### Example 2: Calculate Hashes for New Photos

```python
# Get photos without hashes
photos = db.query(Photo).filter(Photo.phash == None).all()

# Calculate and save hashes
grouper = PhotoGrouper()
db_handler = PhotoGroupDatabase(db)

for photo in photos:
    phash = grouper.calculate_phash(photo.file_path)
    db_handler.save_photo_hash(photo.id, phash)
```

### Example 3: Find and Handle Duplicates

```python
# Get photos with hashes
photos = db.query(Photo).filter(Photo.phash != None).all()

# Prepare data
photo_data = [...]  # Same as Example 1

# Find duplicates
grouper = PhotoGrouper()
duplicate_groups = grouper.find_duplicates(photo_data, strict_threshold=5)

# Process duplicates (e.g., mark for review or auto-delete)
for group in duplicate_groups:
    print(f"Duplicate photos: {group}")
    # Keep best, mark others for deletion
```

## Database Schema

### photo_groups Table

```sql
CREATE TABLE photo_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    created_at TIMESTAMP NOT NULL,
    similarity_threshold INTEGER NOT NULL,
    avg_similarity FLOAT,
    photo_count INTEGER DEFAULT 0,
    best_photo_id INTEGER
);
```

### photos Table (New Fields)

```sql
ALTER TABLE photos ADD COLUMN phash VARCHAR(64);
ALTER TABLE photos ADD COLUMN photo_group_id INTEGER REFERENCES photo_groups(id);
ALTER TABLE photos ADD COLUMN is_best_in_group BOOLEAN DEFAULT FALSE;
```

### Indexes

```sql
CREATE INDEX idx_photos_group ON photos(photo_group_id);
CREATE INDEX idx_photos_phash ON photos(phash);
CREATE INDEX idx_photo_groups_session ON photo_groups(session_id);
```

## Performance Characteristics

### Time Complexity
- Hash calculation: O(1) per image (constant time for fixed size)
- Similarity comparison: O(1) per pair (Hamming distance)
- Grouping: O(n²) for n photos (all-pairs comparison)
- Union-Find: O(n α(n)) ≈ O(n) (nearly linear)

### Space Complexity
- Hash storage: 64 bits (8 bytes) per photo
- Similarity matrix: O(n²) during grouping (temporary)
- Group storage: O(g) for g groups

### Optimization Notes
- Hashes are cached in database to avoid recalculation
- Similarity matrix is only computed during grouping
- Indexes ensure fast queries for grouped photos

## Testing Results

All 13 unit tests passing:

```
test_photo_group_creation ........................... ok
test_calculate_hash_distance ........................ ok
test_calculate_phash ................................ ok
test_calculate_similarity_score ..................... ok
test_different_images_have_large_distance ........... ok
test_empty_photo_list ............................... ok
test_find_duplicates ................................ ok
test_group_photos_basic ............................. ok
test_phash_caching .................................. ok
test_select_best_photo .............................. ok
test_select_best_photo_tie_breaker .................. ok
test_similar_images_have_small_distance ............. ok
test_single_photo ................................... ok

----------------------------------------------------------------------
Ran 13 tests in 0.557s

OK
```

## Integration Points

### With AI Selector
- Uses AI scores for best photo selection
- Can be called after AI evaluation completes
- Complements quality-based filtering

### With Session Management
- Groups are associated with sessions
- Can group photos within a session
- Supports batch processing workflows

### With Approval Queue
- Best photos can be auto-approved
- Non-best photos can be marked for review
- Reduces manual selection workload

## Configuration

### Similarity Threshold Guidelines

- **0-5**: Near duplicates (same shot, minor differences)
- **6-10**: Very similar (same scene, different angle/timing)
- **11-15**: Similar (same location/subject, different composition)
- **16-20**: Somewhat similar (related photos)
- **20+**: Different photos

### Recommended Settings

- **General grouping**: threshold = 10
- **Duplicate detection**: threshold = 5
- **Loose grouping**: threshold = 15
- **Hash size**: 8 (64-bit hash, good balance)

## Future Enhancements

### Potential Improvements
1. **GPU acceleration** for hash calculation (batch processing)
2. **Incremental grouping** (add new photos to existing groups)
3. **Multi-level grouping** (hierarchical similarity)
4. **Visual similarity** using deep learning (CLIP embeddings)
5. **Time-based grouping** (combine with temporal proximity)
6. **Location-based grouping** (combine with GPS data)

### API Endpoints (Future)
```
GET    /api/groups/:session_id          # Get groups for session
POST   /api/groups/:session_id/create   # Create groups
GET    /api/groups/:group_id            # Get group details
DELETE /api/groups/:group_id            # Delete group
GET    /api/photos/:photo_id/similar    # Find similar photos
```

## Troubleshooting

### Common Issues

**Issue: Hashes not being calculated**
- Solution: Ensure imagehash and Pillow are installed
- Check image file paths are valid
- Verify image format is supported

**Issue: Too many/few groups**
- Solution: Adjust similarity_threshold
- Lower threshold = stricter grouping (fewer, tighter groups)
- Higher threshold = looser grouping (more, larger groups)

**Issue: Wrong photo selected as best**
- Solution: Ensure AI scores are calculated first
- Check quality scores are properly set
- Review selection criteria weights

**Issue: Database migration fails**
- Solution: Check Alembic version
- Ensure database is not locked
- Run migration manually: `alembic upgrade head`

## Dependencies

### Required Packages
- `imagehash==4.3.1` - Perceptual hashing
- `Pillow==10.4.0` - Image loading
- `numpy==1.26.4` - Numerical operations
- `SQLAlchemy==2.0.44` - Database ORM

### Optional Packages
- `opencv-python` - Alternative image loading (already installed)

## Conclusion

The photo grouping feature is fully implemented and tested. It provides:

✓ Efficient perceptual hash-based similarity detection  
✓ Automatic grouping of similar photos  
✓ Intelligent best photo selection  
✓ Complete database integration  
✓ Comprehensive test coverage  
✓ Practical usage examples  

The implementation satisfies all requirements from task 10 and is ready for integration into the main workflow.

## References

- [imagehash Documentation](https://github.com/JohannesBuchner/imagehash)
- [Perceptual Hashing](https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html)
- Requirements: Section 2.3 (Similar Photo Grouping)
- Design: Phase 4, Task 10
