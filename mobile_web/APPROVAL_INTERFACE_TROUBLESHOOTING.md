# Mobile Approval Interface - Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Swipe Not Working

**Symptoms:**
- Swiping doesn't move the card
- No visual feedback during swipe
- Card doesn't respond to touch

**Possible Causes:**
1. JavaScript not loaded
2. Touch events blocked
3. Processing state active
4. Browser compatibility issue

**Solutions:**

```javascript
// Check 1: Verify component is mounted
console.log('ApprovalQueue mounted');

// Check 2: Test touch events
document.addEventListener('touchstart', (e) => {
  console.log('Touch detected:', e.touches[0]);
});

// Check 3: Check processing state
console.log('isProcessing:', isProcessing);

// Check 4: Verify browser support
console.log('Touch support:', 'ontouchstart' in window);
```

**Quick Fixes:**
- Refresh the page
- Clear browser cache
- Try a different browser
- Use action buttons as fallback
- Check browser console for errors

### Issue 2: Card Doesn't Reset After Short Swipe

**Symptoms:**
- Card stays offset after short swipe
- No spring-back animation
- Card position stuck

**Possible Causes:**
1. Threshold calculation error
2. CSS transition not applied
3. State not updating

**Solutions:**

```javascript
// Check swipe offset
console.log('Swipe offset:', swipeOffset);

// Check threshold
const threshold = 100;
console.log('Threshold:', threshold);

// Verify reset logic
if (Math.abs(swipeOffset) < threshold) {
  setSwipeOffset(0); // Should reset
}
```

**Quick Fixes:**
- Tap the card to reset
- Refresh the page
- Complete the swipe (> 100px)
- Use action buttons instead

### Issue 3: Details Panel Won't Open

**Symptoms:**
- Tapping card does nothing
- Details don't expand
- No animation

**Possible Causes:**
1. Click event not firing
2. showDetails state not updating
3. CSS animation issue
4. Swipe event interfering

**Solutions:**

```javascript
// Check click handler
const handleClick = () => {
  console.log('Card clicked');
  setShowDetails(!showDetails);
};

// Check state
console.log('showDetails:', showDetails);

// Verify CSS
.details-panel {
  animation: expandDown 0.3s ease-out;
}
```

**Quick Fixes:**
- Tap directly on the card (not buttons)
- Wait for swipe to complete
- Try tapping again
- Check if details exist in data

### Issue 4: Photos Not Loading

**Symptoms:**
- Blank cards
- No images displayed
- Placeholder shown

**Possible Causes:**
1. API endpoint not responding
2. thumbnail_url missing
3. CORS issue
4. Network error

**Solutions:**

```javascript
// Check API response
const data = await apiService.getApprovalQueue();
console.log('Queue data:', data);

// Check photo object
console.log('Current photo:', currentPhoto);
console.log('Thumbnail URL:', currentPhoto?.thumbnail_url);

// Test image URL
const img = new Image();
img.onload = () => console.log('Image loaded');
img.onerror = () => console.log('Image failed');
img.src = currentPhoto.thumbnail_url;
```

**Quick Fixes:**
- Check network connection
- Verify backend is running
- Check API_URL environment variable
- Look for CORS errors in console
- Use retry button

### Issue 5: Approve/Reject Not Working

**Symptoms:**
- Swipe completes but no action
- API call fails
- Error message appears

**Possible Causes:**
1. Backend endpoint not available
2. Photo ID invalid
3. Network error
4. Authentication issue

**Solutions:**

```javascript
// Check API call
try {
  const result = await apiService.approvePhoto(photoId);
  console.log('Approve result:', result);
} catch (error) {
  console.error('Approve failed:', error);
}

// Check photo ID
console.log('Photo ID:', currentPhoto?.id);

// Test endpoint manually
fetch('http://localhost:5100/approval/123/approve', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
});
```

**Quick Fixes:**
- Check backend server status
- Verify photo has valid ID
- Check network tab in DevTools
- Try action buttons instead
- Refresh and try again

### Issue 6: Queue Not Advancing

**Symptoms:**
- Same photo stays after action
- Index doesn't increment
- Stuck on one photo

**Possible Causes:**
1. moveToNext() not called
2. currentIndex not updating
3. Queue array empty
4. State update issue

**Solutions:**

```javascript
// Check moveToNext function
const moveToNext = () => {
  console.log('Moving to next');
  console.log('Current index:', currentIndex);
  console.log('Queue length:', queue.length);
  
  if (currentIndex < queue.length - 1) {
    setCurrentIndex(currentIndex + 1);
  } else {
    loadQueue(); // Reload
  }
};

// Verify state updates
useEffect(() => {
  console.log('Index changed:', currentIndex);
}, [currentIndex]);
```

**Quick Fixes:**
- Refresh the page
- Check if queue has multiple photos
- Verify API returns array
- Look for JavaScript errors

### Issue 7: Animations Janky or Slow

**Symptoms:**
- Choppy animations
- Lag during swipe
- Low frame rate

**Possible Causes:**
1. Too many re-renders
2. Heavy computations
3. Large images
4. Device performance

**Solutions:**

```javascript
// Use React DevTools Profiler
// Check re-render count

// Optimize with useMemo
const photoInfo = useMemo(() => {
  return calculatePhotoInfo(currentPhoto);
}, [currentPhoto]);

// Use useCallback for handlers
const handleSwipe = useCallback(() => {
  // Handler logic
}, [dependencies]);

// Check image size
console.log('Image size:', currentPhoto?.file_size);
```

**Quick Fixes:**
- Close other apps
- Use smaller images
- Reduce animation duration
- Disable details panel
- Try on different device

### Issue 8: Empty State Not Showing

**Symptoms:**
- Blank screen when queue empty
- No "All Caught Up" message
- Loading spinner stuck

**Possible Causes:**
1. Loading state not cleared
2. Queue check logic error
3. Component not re-rendering

**Solutions:**

```javascript
// Check loading state
console.log('Loading:', loading);
console.log('Queue length:', queue.length);

// Verify empty check
if (!loading && !error && !queue.length) {
  // Should show empty state
  console.log('Should show empty state');
}

// Force re-render
setQueue([...queue]);
```

**Quick Fixes:**
- Refresh the page
- Wait for loading to complete
- Check API response
- Verify queue is array

### Issue 9: Touch Events Conflict with Scroll

**Symptoms:**
- Page scrolls during swipe
- Can't swipe horizontally
- Vertical scroll interferes

**Possible Causes:**
1. preventDefault() not called
2. Touch direction not detected
3. CSS touch-action not set

**Solutions:**

```javascript
// Improve touch detection
const handleTouchMove = (e) => {
  const deltaX = Math.abs(touchX - touchStartX.current);
  const deltaY = Math.abs(touchY - touchStartY.current);
  
  // Only prevent if horizontal swipe
  if (deltaX > deltaY) {
    e.preventDefault();
  }
};

// Add CSS
.swipe-card {
  touch-action: pan-y; /* Allow vertical scroll */
}
```

**Quick Fixes:**
- Swipe more horizontally
- Start swipe on card center
- Avoid swiping near edges
- Use action buttons

### Issue 10: Details Show Wrong Data

**Symptoms:**
- EXIF data incorrect
- AI scores don't match
- Old photo data shown

**Possible Causes:**
1. State not updating
2. Cached data
3. API returning wrong data
4. Race condition

**Solutions:**

```javascript
// Check current photo
console.log('Current photo:', currentPhoto);
console.log('Current index:', currentIndex);
console.log('Queue:', queue);

// Verify data freshness
useEffect(() => {
  console.log('Photo changed:', currentPhoto?.id);
}, [currentPhoto]);

// Clear cache
localStorage.clear();
sessionStorage.clear();
```

**Quick Fixes:**
- Refresh the page
- Clear browser cache
- Verify API data
- Check network tab

## Debugging Tools

### Browser Console Commands

```javascript
// Get component state (React DevTools)
$r.state

// Check API service
apiService.getApprovalQueue().then(console.log)

// Test touch events
document.addEventListener('touchstart', console.log)
document.addEventListener('touchmove', console.log)
document.addEventListener('touchend', console.log)

// Check CSS animations
getComputedStyle(element).animation

// Monitor performance
performance.mark('swipe-start')
performance.mark('swipe-end')
performance.measure('swipe', 'swipe-start', 'swipe-end')
```

### React DevTools

1. Install React DevTools extension
2. Open Components tab
3. Find ApprovalQueue component
4. Inspect props and state
5. Monitor re-renders with Profiler

### Network Tab

1. Open DevTools Network tab
2. Filter by XHR/Fetch
3. Check API calls
4. Verify response data
5. Look for errors

## Performance Optimization

### If Animations Are Slow

```css
/* Use GPU acceleration */
.card {
  transform: translateZ(0);
  will-change: transform;
}

/* Reduce animation complexity */
.card {
  transition: transform 0.2s ease-out; /* Shorter duration */
}
```

### If Memory Usage High

```javascript
// Clean up on unmount
useEffect(() => {
  return () => {
    // Cleanup
    setQueue([]);
    setSwipeOffset(0);
  };
}, []);

// Limit queue size
const data = await apiService.getApprovalQueue(50); // Smaller limit
```

## Browser-Specific Issues

### iOS Safari

**Issue:** Swipe triggers back navigation
**Solution:** Add to viewport meta tag
```html
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
```

### Chrome Mobile

**Issue:** Pull-to-refresh interferes
**Solution:** Add CSS
```css
body {
  overscroll-behavior-y: contain;
}
```

### Firefox Mobile

**Issue:** Touch events delayed
**Solution:** Add passive listeners
```javascript
element.addEventListener('touchstart', handler, { passive: true });
```

## Error Messages

### "Failed to load approval queue"

**Cause:** API endpoint not responding  
**Solution:** Check backend server, verify API_URL

### "Failed to approve: Network error"

**Cause:** Network connection lost  
**Solution:** Check internet, retry action

### "Photo ID is undefined"

**Cause:** Invalid photo object  
**Solution:** Reload queue, check API response

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Review browser console errors
3. Test on different browser
4. Verify backend is running
5. Check network connectivity

### Information to Provide

- Browser and version
- Device and OS
- Error messages
- Console logs
- Network tab screenshots
- Steps to reproduce

### Support Resources

- Implementation docs: `APPROVAL_INTERFACE_IMPLEMENTATION.md`
- Quick start: `APPROVAL_INTERFACE_QUICK_START.md`
- Demo guide: `APPROVAL_INTERFACE_DEMO.md`
- Task summary: `TASK_34_COMPLETION_SUMMARY.md`

## Prevention Tips

### Best Practices

1. Always test on real devices
2. Check network tab for API errors
3. Monitor console for warnings
4. Test with slow network
5. Test with empty queue
6. Test with single photo
7. Test error scenarios
8. Clear cache regularly

### Development Tips

1. Use React DevTools
2. Enable source maps
3. Test touch events
4. Monitor performance
5. Check memory usage
6. Profile animations
7. Test on multiple browsers

## Conclusion

Most issues can be resolved by:
1. Refreshing the page
2. Checking browser console
3. Verifying backend status
4. Testing network connection
5. Using fallback buttons

If issues persist, review the implementation documentation and check for updates.
