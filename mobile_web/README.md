# Junmai AutoDev - Mobile Web UI

Progressive Web App (PWA) for Junmai AutoDev - AI-powered Lightroom automation system.

## Features

- 📱 **Mobile-First Design**: Optimized for smartphones and tablets
- 🔄 **Real-time Updates**: WebSocket integration for live status updates
- 📊 **Dashboard**: System status and session overview
- ✅ **Approval Queue**: Swipe-based photo approval interface
- 📁 **Session Management**: Track and manage photo processing sessions
- ⚙️ **Settings**: Configure system preferences
- 🔔 **Push Notifications**: Get notified about processing completion
- 📴 **Offline Support**: Service worker caching for offline access

## Technology Stack

- **React 18**: Modern React with hooks
- **React Router 6**: Client-side routing
- **Tailwind CSS**: Utility-first CSS framework
- **PWA**: Progressive Web App with service worker
- **Workbox**: Service worker libraries for caching strategies

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Junmai AutoDev backend running on `http://localhost:5100`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

### Build for Production

```bash
# Create optimized production build
npm run build

# The build folder will contain the production-ready files
```

### Deployment

The production build can be served by any static file server. For integration with the Junmai AutoDev backend:

1. Build the production version: `npm run build`
2. Copy the `build` folder contents to the backend's `web` directory
3. The backend Flask server will serve the mobile UI at `/mobile`

## Project Structure

```
mobile_web/
├── public/
│   ├── index.html          # HTML template
│   ├── manifest.json       # PWA manifest
│   └── robots.txt
├── src/
│   ├── components/         # Reusable components
│   │   ├── Layout.js       # Main layout wrapper
│   │   └── Navigation.js   # Bottom navigation bar
│   ├── pages/              # Page components
│   │   ├── Dashboard.js    # Dashboard page
│   │   ├── ApprovalQueue.js # Approval interface
│   │   ├── Sessions.js     # Session management
│   │   ├── Settings.js     # Settings page
│   │   └── NotFound.js     # 404 page
│   ├── App.js              # Main app component with routing
│   ├── App.css             # Global styles
│   ├── index.js            # Entry point
│   ├── index.css           # Tailwind imports
│   ├── service-worker.js   # Service worker
│   └── serviceWorkerRegistration.js # SW registration
├── tailwind.config.js      # Tailwind configuration
├── postcss.config.js       # PostCSS configuration
└── package.json            # Dependencies and scripts
```

## PWA Features

### Service Worker

The app includes a service worker that provides:

- **Offline caching**: App shell and static assets
- **API caching**: Network-first strategy for API calls
- **Image caching**: Stale-while-revalidate for images
- **Background sync**: Queue failed requests for retry

### Installation

Users can install the app on their device:

1. Open the app in a mobile browser
2. Tap "Add to Home Screen" when prompted
3. The app will appear as a native app icon

### Push Notifications

The service worker supports push notifications for:

- Processing completion
- Approval requests
- Error alerts

## API Integration

The app connects to the Junmai AutoDev backend API:

- **Base URL**: `http://localhost:5100/api`
- **WebSocket**: `ws://localhost:5100/ws`

### API Endpoints Used

- `GET /api/system/status` - System status
- `GET /api/sessions` - Session list
- `GET /api/sessions/:id` - Session details
- `GET /api/approval/queue` - Approval queue
- `POST /api/approval/:id/approve` - Approve photo
- `POST /api/approval/:id/reject` - Reject photo

## Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (irreversible)

### Customization

#### Tailwind CSS

Customize colors, fonts, and other design tokens in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom colors
      }
    }
  }
}
```

#### Service Worker

Modify caching strategies in `src/service-worker.js`:

```javascript
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    // Customize cache settings
  })
);
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers with PWA support

## Requirements Mapping

This implementation addresses the following requirements from the design document:

- **Requirement 9.1**: Mobile browser accessible Web UI
- **Requirement 9.2**: Display processing status and session list
- **Requirement 9.4**: PWA with push notification support

## Next Steps

The following features will be implemented in subsequent tasks:

- **Task 33**: Mobile dashboard implementation with real-time data
- **Task 34**: Swipe-based approval interface
- **Task 35**: Push notification integration

## License

Part of the Junmai AutoDev project.

## Support

For issues and questions, please refer to the main project documentation.
