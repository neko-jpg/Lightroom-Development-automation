# Mobile Approval Interface - Quick Start Guide

## Overview

The mobile approval interface allows you to review and approve/reject photos using intuitive swipe gestures on your mobile device.

## How to Use

### Basic Gestures

1. **Approve a Photo:**
   - Swipe right (→) on the photo card
   - Green checkmark appears during swipe
   - Photo is approved and next photo loads

2. **Reject a Photo:**
   - Swipe left (←) on the photo card
   - Red X appears during swipe
   - Photo is rejected and next photo loads

3. **View Details:**
   - Tap anywhere on the photo card
   - Details panel expands showing EXIF data and AI scores
   - Tap again to collapse

### Alternative Controls

If you prefer not to swipe, use the buttons at the bottom:
- **Green "Approve" button** - Approve current photo
- **Red "Reject" button** - Reject current photo

## Photo Information

### Always Visible
- File name
- AI score (1-5 stars)
- Context tag (e.g., "backlit_portrait")
- Selected preset
- Queue position (e.g., "1 / 12")

### Details Panel (Tap to View)
- Camera and lens information
- Shooting settings (ISO, aperture, shutter speed, focal length)
- Capture timestamp
- AI analysis scores (focus, exposure, composition)

## Tips for Best Experience

### Swipe Gestures
- Swipe at least 100px to trigger action
- Swipe horizontally (left/right) for best results
- Short swipes will reset the card position
- Visual feedback shows your swipe direction

### Navigation
- Photos advance automatically after approve/reject
- Queue reloads when you reach the end
- Progress indicator shows your position

### Performance
- Photos load from the backend API
- Thumbnails display when available
- Placeholder shown for missing images

## Troubleshooting

### Swipe Not Working
- Make sure you're swiping horizontally
- Swipe at least 100px distance
- Check that you're not scrolling vertically
- Use the buttons as fallback

### Photo Not Loading
- Check your internet connection
- Verify backend server is running
- Look for error message and use "Retry" button

### Details Not Showing
- Tap directly on the photo card
- Some photos may have limited EXIF data
- AI scores may not be available for all photos

## API Requirements

The approval interface requires these backend endpoints:

```
GET  /approval/queue?limit=100    # Get photos pending approval
POST /approval/{photoId}/approve  # Approve a photo
POST /approval/{photoId}/reject   # Reject a photo
```

## Example Workflow

1. Open the Approval Queue page
2. Review the first photo
3. Tap to see details (optional)
4. Swipe right to approve or left to reject
5. Next photo loads automatically
6. Repeat until queue is empty
7. "All Caught Up!" message appears

## Mobile Optimization

### Touch-Friendly Design
- Large touch targets (44px minimum)
- Clear visual feedback
- Smooth animations
- Prevented accidental touches

### Performance
- Optimized for 60fps animations
- Minimal re-renders during swipe
- Efficient touch event handling

## Browser Support

Works on:
- iOS Safari (12+)
- Chrome Mobile
- Firefox Mobile
- Samsung Internet
- Desktop browsers (with mouse fallback)

## Keyboard Shortcuts (Desktop)

While swipe gestures are for mobile, desktop users can use:
- Click "Approve" or "Reject" buttons
- Click on card to toggle details

## Next Steps

After approving photos:
1. Photos move to export queue (if auto-export enabled)
2. Check Dashboard for processing status
3. View statistics for approval rates
4. Export approved photos manually if needed

## Related Documentation

- `APPROVAL_INTERFACE_IMPLEMENTATION.md` - Technical details
- `DASHBOARD_QUICK_START.md` - Dashboard usage
- `ARCHITECTURE.md` - System architecture
- `TASK_34_COMPLETION_SUMMARY.md` - Implementation summary

## Support

For issues or questions:
1. Check error messages in the UI
2. Review browser console for errors
3. Verify backend API is running
4. Check network connectivity
