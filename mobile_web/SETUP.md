# Mobile Web UI Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd mobile_web
npm install
```

This will install:
- React 18.2.0
- React Router DOM 6.20.0
- React Scripts 5.0.1
- Tailwind CSS 3.3.5
- Web Vitals 3.5.0

### 2. Start Development Server

```bash
npm start
```

The app will automatically open at `http://localhost:3000`

### 3. Build for Production

```bash
npm run build
```

The optimized production build will be created in the `build/` directory.

## Project Structure

```
mobile_web/
├── public/                 # Static files
│   ├── index.html         # HTML template
│   ├── manifest.json      # PWA manifest
│   ├── robots.txt         # SEO robots file
│   └── favicon.ico        # App icon (placeholder)
│
├── src/
│   ├── components/        # Reusable components
│   │   ├── Layout.js      # Main layout with navigation
│   │   └── Navigation.js  # Bottom navigation bar
│   │
│   ├── pages/             # Page components (routes)
│   │   ├── Dashboard.js   # Main dashboard
│   │   ├── ApprovalQueue.js # Photo approval interface
│   │   ├── Sessions.js    # Session management
│   │   ├── Settings.js    # App settings
│   │   └── NotFound.js    # 404 page
│   │
│   ├── App.js             # Main app with routing
│   ├── App.css            # Global app styles
│   ├── index.js           # Entry point
│   ├── index.css          # Tailwind CSS imports
│   ├── service-worker.js  # PWA service worker
│   ├── serviceWorkerRegistration.js # SW registration
│   └── reportWebVitals.js # Performance monitoring
│
├── .env                   # Environment variables
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── package.json          # Dependencies and scripts
├── tailwind.config.js    # Tailwind configuration
├── postcss.config.js     # PostCSS configuration
└── README.md             # Project documentation
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:5100
REACT_APP_WS_URL=ws://localhost:5100/ws

# App Configuration
REACT_APP_NAME=Junmai AutoDev
REACT_APP_VERSION=1.0.0

# Feature Flags
REACT_APP_ENABLE_NOTIFICATIONS=true
REACT_APP_ENABLE_OFFLINE=true
```

### Tailwind CSS

Customize design tokens in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          // Custom color palette
        }
      }
    }
  }
}
```

## Features Implemented

### ✅ React Project Setup
- Create React App with PWA template
- React 18 with modern hooks
- Functional components throughout

### ✅ Tailwind CSS Integration
- Utility-first CSS framework
- Custom color palette
- Responsive design utilities
- Mobile-first approach

### ✅ PWA Configuration
- Service worker with Workbox
- Offline caching strategies
- App manifest for installation
- Push notification support

### ✅ React Router Setup
- Client-side routing
- Nested routes
- 404 handling
- Navigation guards (ready for auth)

### ✅ Layout Components
- Main layout wrapper
- Bottom navigation bar
- Responsive design
- Touch-friendly UI

### ✅ Page Components (Placeholders)
- Dashboard page
- Approval queue page
- Sessions page
- Settings page
- 404 page

## Routing Structure

```
/                          → Redirect to /dashboard
/dashboard                 → Dashboard page
/approval                  → Approval queue
/sessions                  → Sessions list
/sessions/:id              → Session detail
/settings                  → Settings page
*                          → 404 Not Found
```

## PWA Features

### Service Worker

The service worker provides:

1. **Precaching**: App shell and static assets
2. **Runtime Caching**:
   - API calls: NetworkFirst strategy (5 min cache)
   - Images: StaleWhileRevalidate (30 days)
3. **Offline Support**: Cached content available offline
4. **Push Notifications**: Ready for backend integration

### Installation

Users can install the app:

1. Visit the app in a mobile browser
2. Tap "Add to Home Screen" when prompted
3. App appears as a native icon

### Manifest

The `manifest.json` defines:
- App name and short name
- Icons (192x192, 512x512)
- Display mode: standalone
- Theme colors
- Orientation: portrait

## Development Workflow

### 1. Start Development

```bash
npm start
```

- Hot reload enabled
- Opens at `http://localhost:3000`
- Service worker disabled in development

### 2. Test PWA Features

```bash
npm run build
npx serve -s build
```

- Service worker active
- Test offline functionality
- Test installation prompt

### 3. Build for Production

```bash
npm run build
```

- Optimized bundle
- Minified code
- Service worker generated
- Ready for deployment

## Integration with Backend

### API Connection

The app expects the backend API at:
- **Development**: `http://localhost:5100/api`
- **Production**: Configure via `REACT_APP_API_URL`

### WebSocket Connection

Real-time updates via WebSocket:
- **Development**: `ws://localhost:5100/ws`
- **Production**: Configure via `REACT_APP_WS_URL`

### CORS Configuration

Ensure the backend allows requests from:
- Development: `http://localhost:3000`
- Production: Your deployment domain

## Next Steps

### Task 33: Mobile Dashboard Implementation
- Connect to real API endpoints
- Display system status
- Show active sessions
- Real-time updates via WebSocket

### Task 34: Approval Interface
- Swipe gesture implementation
- Photo comparison view
- Approve/reject actions
- Touch-optimized controls

### Task 35: Push Notifications
- Notification permission request
- Push subscription management
- Notification click handling
- Background sync

## Troubleshooting

### npm install fails

```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Service worker not updating

```bash
# Clear browser cache
# Or use incognito mode
# Or unregister SW in DevTools
```

### Tailwind styles not applying

```bash
# Ensure PostCSS is configured
# Check tailwind.config.js paths
# Restart development server
```

## Browser DevTools

### Testing PWA

1. Open Chrome DevTools
2. Go to Application tab
3. Check:
   - Manifest
   - Service Workers
   - Cache Storage
   - Push Notifications

### Performance

1. Open Lighthouse
2. Run PWA audit
3. Check scores:
   - Performance
   - Accessibility
   - Best Practices
   - SEO
   - PWA

## Requirements Fulfilled

This setup completes **Task 32** requirements:

- ✅ Create React App project initialization
- ✅ Tailwind CSS configuration
- ✅ PWA setup (manifest.json, service worker)
- ✅ React Router configuration
- ✅ Requirements 9.1, 9.2, 9.4 addressed

## Additional Resources

- [React Documentation](https://react.dev/)
- [React Router](https://reactrouter.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [Workbox](https://developers.google.com/web/tools/workbox)

## Support

For issues specific to the mobile web UI, check:
1. Browser console for errors
2. Network tab for API calls
3. Application tab for PWA features
4. Service worker status

For backend integration issues, refer to the main project documentation.
