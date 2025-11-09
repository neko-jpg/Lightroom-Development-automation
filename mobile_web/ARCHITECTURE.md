# Mobile Web UI Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Mobile Browser                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Junmai AutoDev PWA                      │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │         React Application                   │ │  │
│  │  │  ┌────────────┐  ┌────────────┐            │ │  │
│  │  │  │  Router    │  │  Layout    │            │ │  │
│  │  │  └────────────┘  └────────────┘            │ │  │
│  │  │                                             │ │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐   │ │  │
│  │  │  │Dashboard │ │Approval  │ │Sessions  │   │ │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘   │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │         Service Worker                      │ │  │
│  │  │  • Offline caching                          │ │  │
│  │  │  • Push notifications                       │ │  │
│  │  │  • Background sync                          │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/WebSocket
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Backend API Server                          │
│              (Flask - Port 5100)                         │
│                                                          │
│  /api/system/status    /api/sessions                    │
│  /api/approval/queue   /ws (WebSocket)                  │
└─────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
App (Router)
│
├── Layout
│   ├── Outlet (Page Content)
│   └── Navigation (Bottom Bar)
│
├── Dashboard
│   ├── System Status Card
│   ├── Today's Stats Card
│   ├── Active Sessions Card
│   └── Quick Actions Card
│
├── ApprovalQueue
│   ├── Queue Status
│   ├── Photo Viewer (swipe)
│   └── Action Buttons
│
├── Sessions
│   ├── Session List
│   └── Session Detail
│
├── Settings
│   ├── System Settings
│   ├── Connection Settings
│   └── About Info
│
└── NotFound (404)
```

## Data Flow

```
┌──────────────┐
│   User       │
│   Action     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   React      │
│   Component  │
└──────┬───────┘
       │
       ▼
┌──────────────┐      ┌──────────────┐
│   API Call   │─────▶│   Backend    │
│   (fetch)    │      │   API        │
└──────┬───────┘      └──────┬───────┘
       │                     │
       │◀────────────────────┘
       │   Response
       ▼
┌──────────────┐
│   Update     │
│   State      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Re-render  │
│   UI         │
└──────────────┘
```

## Routing Flow

```
User navigates to URL
       │
       ▼
React Router matches route
       │
       ├─── / ──────────────────▶ Redirect to /dashboard
       │
       ├─── /dashboard ─────────▶ Dashboard Component
       │
       ├─── /approval ──────────▶ ApprovalQueue Component
       │
       ├─── /sessions ──────────▶ Sessions List
       │
       ├─── /sessions/:id ──────▶ Session Detail
       │
       ├─── /settings ──────────▶ Settings Component
       │
       └─── /* ─────────────────▶ NotFound Component
```

## Service Worker Caching Strategy

```
Request Type          Strategy              Cache Duration
─────────────────────────────────────────────────────────
App Shell            Precache              Permanent
Static Assets        Precache              Permanent
API Calls            NetworkFirst          5 minutes
Images               StaleWhileRevalidate  30 days
```

## State Management (Future)

```
┌─────────────────────────────────────────────────────┐
│                  Global State                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │   User     │  │  Sessions  │  │   System   │    │
│  │   Auth     │  │   Data     │  │   Status   │    │
│  └────────────┘  └────────────┘  └────────────┘    │
└─────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │Settings│      │Sessions│      │Dashboard│
    └────────┘      └────────┘      └────────┘
```

## PWA Installation Flow

```
1. User visits app in browser
         │
         ▼
2. Service worker registers
         │
         ▼
3. Manifest.json loads
         │
         ▼
4. Browser shows "Add to Home Screen"
         │
         ▼
5. User taps "Add"
         │
         ▼
6. App icon appears on home screen
         │
         ▼
7. App opens in standalone mode
```

## Build Process

```
Source Code (src/)
       │
       ▼
Webpack bundling
       │
       ├─── JavaScript minification
       ├─── CSS processing (Tailwind)
       ├─── Asset optimization
       └─── Service worker generation
       │
       ▼
Production Build (build/)
       │
       ├─── index.html
       ├─── static/js/main.[hash].js
       ├─── static/css/main.[hash].css
       ├─── service-worker.js
       └─── manifest.json
```

## Technology Stack

```
┌─────────────────────────────────────────────────────┐
│                   Frontend Layer                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │   React    │  │   Router   │  │  Tailwind  │    │
│  │    18      │  │     6      │  │    CSS     │    │
│  └────────────┘  └────────────┘  └────────────┘    │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                    PWA Layer                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │  Service   │  │  Manifest  │  │   Push     │    │
│  │  Worker    │  │   .json    │  │   Notify   │    │
│  └────────────┘  └────────────┘  └────────────┘    │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                  Network Layer                       │
│  ┌────────────┐  ┌────────────┐                     │
│  │   Fetch    │  │ WebSocket  │                     │
│  │    API     │  │            │                     │
│  └────────────┘  └────────────┘                     │
└─────────────────────────────────────────────────────┘
```

## File Organization

```
mobile_web/
│
├── Configuration
│   ├── package.json          # Dependencies
│   ├── tailwind.config.js    # Styling
│   ├── postcss.config.js     # CSS processing
│   └── .env                  # Environment
│
├── Public Assets
│   ├── index.html            # HTML template
│   ├── manifest.json         # PWA manifest
│   └── favicon.ico           # App icon
│
├── Source Code
│   ├── Entry Points
│   │   ├── index.js          # App entry
│   │   └── index.css         # Global styles
│   │
│   ├── Core
│   │   ├── App.js            # Main component
│   │   └── App.css           # App styles
│   │
│   ├── Components
│   │   ├── Layout.js         # Layout wrapper
│   │   └── Navigation.js     # Bottom nav
│   │
│   ├── Pages
│   │   ├── Dashboard.js      # Dashboard
│   │   ├── ApprovalQueue.js  # Approval
│   │   ├── Sessions.js       # Sessions
│   │   ├── Settings.js       # Settings
│   │   └── NotFound.js       # 404
│   │
│   └── PWA
│       ├── service-worker.js           # SW logic
│       ├── serviceWorkerRegistration.js # SW setup
│       └── reportWebVitals.js          # Metrics
│
└── Documentation
    ├── README.md             # Overview
    ├── SETUP.md              # Setup guide
    ├── QUICK_START.md        # Quick start
    ├── ARCHITECTURE.md       # This file
    └── TASK_32_COMPLETION_SUMMARY.md
```

## Performance Optimization

```
┌─────────────────────────────────────────────────────┐
│              Optimization Strategies                 │
│                                                      │
│  Code Splitting                                      │
│  ├─── React.lazy() for routes                       │
│  └─── Dynamic imports                               │
│                                                      │
│  Caching                                            │
│  ├─── Service worker precaching                     │
│  ├─── API response caching                          │
│  └─── Image caching                                 │
│                                                      │
│  Bundle Optimization                                │
│  ├─── Tree shaking                                  │
│  ├─── Minification                                  │
│  └─── Compression                                   │
│                                                      │
│  Asset Optimization                                 │
│  ├─── Image lazy loading                            │
│  ├─── Font subsetting                               │
│  └─── CSS purging                                   │
└─────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                Security Layers                       │
│                                                      │
│  Transport Security                                  │
│  └─── HTTPS (required for PWA)                      │
│                                                      │
│  Authentication (Future)                            │
│  ├─── JWT tokens                                    │
│  └─── Secure storage                                │
│                                                      │
│  API Security                                       │
│  ├─── CORS validation                               │
│  ├─── Rate limiting                                 │
│  └─── Input sanitization                            │
│                                                      │
│  Content Security                                   │
│  ├─── CSP headers                                   │
│  └─── XSS prevention                                │
└─────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
Development                Production
─────────────────────────────────────────────────
localhost:3000            Backend serves /mobile
                                 │
React Dev Server          Static files in build/
                                 │
Hot reload enabled        Service worker active
                                 │
SW disabled               Offline support enabled
```

## Future Enhancements

```
Phase 1 (Current)         Phase 2 (Next)         Phase 3 (Future)
─────────────────────────────────────────────────────────────────
✅ Basic routing          → Real-time data       → Advanced features
✅ PWA setup              → WebSocket            → Offline editing
✅ Placeholder pages      → API integration      → Background sync
✅ Tailwind CSS           → Push notifications   → Advanced caching
                          → Swipe gestures       → Performance opt
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-09  
**Status**: Initial Architecture
