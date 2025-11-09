# Junmai AutoDev - Architecture Documentation

## Overview

Junmai AutoDev is a comprehensive automated photo development system that integrates Adobe Lightroom Classic with AI-powered selection and context-aware processing. The system is designed to automate the entire photography workflow from import to export.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Desktop GUI   │  Mobile Web UI  │  Lightroom Plugin (Lua)    │
│    (PyQt6)      │   (React PWA)   │                            │
└────────┬────────┴────────┬────────┴──────────┬─────────────────┘
         │                 │                    │
         └─────────────────┼────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  REST API   │
                    │  (Flask)    │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ WebSocket│      │Job Queue│      │  Cache  │
    │  Server  │      │ (Celery)│      │ (Redis) │
    └─────────┘      └────┬────┘      └─────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │   AI    │      │ Context │      │  EXIF   │
    │ Selector│      │ Engine  │      │Analyzer │
    │(Ollama) │      │         │      │         │
    └─────────┘      └─────────┘      └─────────┘
                           │
                    ┌──────▼──────┐
                    │  Database   │
                    │  (SQLite)   │
                    └─────────────┘
```

## Core Components

### 1. Local Bridge (Python Backend)

**Location**: `local_bridge/`

The local bridge is the central processing hub that coordinates all system operations.

#### Key Modules

##### 1.1 Flask Application (`app.py`)
- REST API server
- WebSocket server integration
- Request routing and middleware
- CORS configuration
- Authentication handling

##### 1.2 AI Selection Engine (`ai_selector.py`)
- Integration with Ollama LLM
- Image quality evaluation
- Focus, exposure, and composition analysis
- Face detection
- Star rating generation (1-5)
- Tag recommendation

##### 1.3 EXIF Analyzer (`exif_analyzer.py`)
- Metadata extraction from RAW/JPEG files
- Camera settings parsing
- GPS location analysis
- Context hint inference
- Time-of-day detection

##### 1.4 Context Engine (`context_engine.py`)
- Rule-based context determination
- Scene classification (backlit, low-light, landscape, etc.)
- Context scoring algorithm
- 20+ predefined scenarios

##### 1.5 Preset Engine (`preset_manager.py`)
- Context-to-preset mapping
- Preset version management
- Learning-based adjustments
- A/B testing support

##### 1.6 Job Queue System
- **Job Queue Manager** (`job_queue_manager.py`): Job lifecycle management
- **Priority Manager** (`priority_manager.py`): Dynamic priority calculation
- **Resource Manager** (`resource_manager.py`): CPU/GPU resource monitoring
- **Celery Tasks** (`celery_tasks.py`): Async task execution

##### 1.7 File Processing
- **Hot Folder Watcher** (`hot_folder_watcher.py`): File system monitoring
- **File Import Processor** (`file_import_processor.py`): Import handling
- **Auto Export Engine** (`auto_export_engine.py`): Export automation

##### 1.8 Storage & Caching
- **Cache Manager** (`cache_manager.py`): Redis-based caching
- **Database Models** (`models/database.py`): SQLAlchemy ORM
- **Schema** (`schema.py`): Database schema definitions

##### 1.9 Error Handling & Recovery
- **Error Handler** (`error_handler.py`): Error classification and handling
- **Retry Manager** (`retry_manager.py`): Exponential backoff retry logic
- **Failsafe Manager** (`failsafe_manager.py`): State recovery and backup

##### 1.10 Notification System
- **Desktop Notifier** (`desktop_notifier.py`): OS-native notifications
- **Email Notifier** (`email_notifier.py`): SMTP email notifications
- **LINE Notifier** (`line_notifier.py`): LINE Notify integration

##### 1.11 GPU & Performance
- **GPU Manager** (`gpu_manager.py`): GPU memory and temperature monitoring
- **Performance Metrics** (`performance_metrics.py`): System metrics collection
- **Model Manager** (`model_manager.py`): Multi-model support

### 2. Desktop GUI (PyQt6)

**Location**: `gui_qt/`

Modern desktop interface built with PyQt6 for system monitoring and control.

#### Components

##### 2.1 Main Window (`main_window.py`)
- Tab-based navigation
- Menu bar and toolbar
- Status bar with system info
- Theme switching (dark/light)

##### 2.2 Dashboard Widgets (`widgets/dashboard_widgets.py`)
- System status display
- Active sessions overview
- Quick actions panel
- Recent activity log

##### 2.3 Session Management (`widgets/session_widgets.py`)
- Session list view
- Progress tracking
- Session operations (pause, resume, delete)

##### 2.4 Approval Queue (`widgets/approval_widgets.py`)
- Before/after comparison
- AI score display
- Keyboard shortcuts
- Batch approval

##### 2.5 Settings (`widgets/settings_widgets.py`)
- Hot folder configuration
- AI settings
- Processing options
- Notification preferences

##### 2.6 Statistics (`widgets/statistics_widgets.py`)
- Daily/weekly/monthly stats
- Chart visualization (matplotlib)
- Preset usage analysis
- Export functionality

### 3. Mobile Web UI (React PWA)

**Location**: `mobile_web/`

Progressive Web App for mobile access and remote monitoring.

#### Structure

##### 3.1 Pages
- **Dashboard** (`src/pages/Dashboard.js`): System overview
- **Sessions** (`src/pages/Sessions.js`): Session management
- **Approval Queue** (`src/pages/ApprovalQueue.js`): Swipe-based approval
- **Settings** (`src/pages/Settings.js`): Configuration

##### 3.2 Components
- **Layout** (`src/components/Layout.js`): App shell
- **Navigation** (`src/components/Navigation.js`): Bottom navigation
- **System Status** (`src/components/SystemStatus.js`): Status cards
- **Session List** (`src/components/SessionList.js`): Session cards

##### 3.3 Services
- **API Service** (`src/services/api.js`): REST API client
- **Notification Service** (`src/services/notificationService.js`): Push notifications

##### 3.4 PWA Features
- **Service Worker** (`src/service-worker.js`): Offline support
- **Manifest** (`public/manifest.json`): App metadata
- **Push Notifications**: Web Push API integration

### 4. Lightroom Plugin (Lua)

**Location**: `JunmaiAutoDev.lrdevplugin/`

Lua-based plugin for Adobe Lightroom Classic integration.

#### Components

##### 4.1 Main Entry (`Main.lua`)
- Plugin initialization
- Menu item registration
- Job processing loop

##### 4.2 WebSocket Client (`WebSocketClient.lua`)
- Real-time communication with local bridge
- Progress reporting
- Error handling

##### 4.3 Job Runner (`JobRunner.lua`)
- Develop settings application
- Virtual copy creation
- Snapshot management

##### 4.4 Control Panel (`ShowControlPanel.lua`)
- Plugin UI dialog
- Manual job submission
- Status display

## Data Flow

### 1. Photo Import Flow

```
SD Card/Camera
    ↓
Hot Folder (File System)
    ↓
Hot Folder Watcher (Python watchdog)
    ↓
File Import Processor
    ↓
EXIF Analyzer → Extract metadata
    ↓
Database (photos table)
    ↓
Job Queue (import_complete event)
```

### 2. AI Selection Flow

```
Photo Import Complete
    ↓
AI Selector Task (Celery)
    ↓
├─ Image Quality Analysis (OpenCV)
│  ├─ Focus Score (Laplacian variance)
│  ├─ Exposure Score (Histogram)
│  ├─ Composition Score (Rule of thirds)
│  └─ Face Detection (OpenCV DNN)
│
└─ LLM Evaluation (Ollama)
   ├─ Prompt Generation
   ├─ Model Inference
   └─ Score Parsing (1-5 stars)
    ↓
Combined Score (70% technical + 30% LLM)
    ↓
Database Update (ai_score, context_tag)
    ↓
Context Engine → Determine scenario
    ↓
Preset Engine → Select preset
    ↓
Job Queue (develop_ready event)
```

### 3. Development Flow

```
Develop Ready Event
    ↓
Priority Queue (sorted by score + age)
    ↓
Resource Manager (check CPU/GPU)
    ↓
Lightroom Job Creation
    ↓
WebSocket → Lightroom Plugin
    ↓
Lua Job Runner
    ↓
├─ Create Virtual Copy
├─ Create Snapshot
├─ Apply Develop Settings
└─ Report Progress
    ↓
WebSocket → Local Bridge
    ↓
Database Update (status = completed)
    ↓
Approval Queue
```

### 4. Approval & Export Flow

```
Approval Queue
    ↓
User Review (Desktop/Mobile)
    ↓
Approval Decision
    ↓
├─ Approved → Export Queue
├─ Rejected → Learning Data
└─ Modified → Learning Data + Export Queue
    ↓
Auto Export Engine
    ↓
├─ Apply Export Preset
├─ Generate File Name
└─ Export to Destination
    ↓
Cloud Sync (Optional)
    ↓
├─ rclone Integration
└─ Upload to Dropbox/Google Drive
    ↓
Notification (Desktop/Email/LINE)
```

## Database Schema

### Core Tables

#### sessions
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_folder TEXT,
    total_photos INTEGER DEFAULT 0,
    processed_photos INTEGER DEFAULT 0,
    status TEXT CHECK(status IN ('importing', 'selecting', 
                                  'developing', 'exporting', 'completed'))
);
```

#### photos
```sql
CREATE TABLE photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(id),
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    
    -- EXIF data
    camera_make TEXT,
    camera_model TEXT,
    lens TEXT,
    focal_length REAL,
    aperture REAL,
    shutter_speed TEXT,
    iso INTEGER,
    capture_time TIMESTAMP,
    gps_lat REAL,
    gps_lon REAL,
    
    -- AI evaluation
    ai_score REAL CHECK(ai_score BETWEEN 1 AND 5),
    focus_score REAL,
    exposure_score REAL,
    composition_score REAL,
    subject_type TEXT,
    detected_faces INTEGER DEFAULT 0,
    
    -- Context
    context_tag TEXT,
    selected_preset TEXT,
    
    -- Status
    status TEXT CHECK(status IN ('imported', 'analyzed', 'queued', 
                                  'processing', 'completed', 'failed', 'rejected')),
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP
);
```

#### jobs
```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    photo_id INTEGER REFERENCES photos(id),
    priority INTEGER CHECK(priority IN (1, 2, 3)),
    config_json TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'processing', 
                                  'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);
```

#### presets
```sql
CREATE TABLE presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    version TEXT NOT NULL,
    context_tags TEXT, -- JSON array
    config_template TEXT NOT NULL, -- JSON
    blend_amount INTEGER DEFAULT 100,
    usage_count INTEGER DEFAULT 0,
    avg_approval_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Architecture

### REST API Endpoints

#### Session Management
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/:id` - Get session details
- `POST /api/sessions` - Create new session
- `DELETE /api/sessions/:id` - Delete session

#### Photo Management
- `GET /api/photos` - List photos (with filters)
- `GET /api/photos/:id` - Get photo details
- `PATCH /api/photos/:id` - Update photo
- `GET /api/photos/:id/thumbnail` - Get thumbnail

#### Job Management
- `GET /api/jobs` - List jobs
- `GET /api/jobs/:id` - Get job details
- `POST /api/jobs` - Create job
- `DELETE /api/jobs/:id` - Cancel job

#### Approval Queue
- `GET /api/approval/queue` - Get pending approvals
- `POST /api/approval/:photo_id/approve` - Approve photo
- `POST /api/approval/:photo_id/reject` - Reject photo

#### Statistics
- `GET /api/statistics/daily` - Daily statistics
- `GET /api/statistics/weekly` - Weekly statistics
- `GET /api/statistics/presets` - Preset usage stats

### WebSocket Events

#### Client → Server
- `subscribe_session` - Subscribe to session updates
- `subscribe_jobs` - Subscribe to job updates
- `ping` - Keep-alive

#### Server → Client
- `photo_imported` - New photo imported
- `photo_analyzed` - AI analysis complete
- `job_started` - Job processing started
- `job_completed` - Job completed
- `job_failed` - Job failed
- `system_status` - System status update

## Configuration Management

### System Configuration (`config.json`)

```json
{
  "version": "2.0",
  "system": {
    "hot_folders": ["D:/Photos/Inbox"],
    "lightroom_catalog": "D:/Lightroom/Catalog.lrcat",
    "temp_folder": "C:/Temp/JunmaiAutoDev",
    "log_level": "INFO"
  },
  "ai": {
    "llm_provider": "ollama",
    "llm_model": "llama3.1:8b-instruct",
    "ollama_host": "http://localhost:11434",
    "gpu_memory_limit_mb": 6144,
    "selection_threshold": 3.5
  },
  "processing": {
    "auto_import": true,
    "auto_select": true,
    "auto_develop": true,
    "max_concurrent_jobs": 3,
    "cpu_limit_percent": 80
  }
}
```

## Security Architecture

### Authentication
- JWT-based authentication for API access
- Token expiration and refresh
- API key management for external integrations

### Authorization
- Role-based access control (future)
- Resource-level permissions

### Data Protection
- Local-only processing (no cloud AI)
- Encrypted configuration storage
- Secure credential management

## Performance Optimization

### Caching Strategy
- **EXIF Cache**: 24-hour TTL in Redis
- **AI Evaluation Cache**: 7-day TTL in Redis
- **Thumbnail Cache**: Persistent file cache

### Resource Management
- CPU usage monitoring and throttling
- GPU memory allocation limits
- Temperature-based processing adjustment
- Idle time detection for batch processing

### Database Optimization
- Indexed queries on status and session_id
- Connection pooling
- Prepared statements

## Error Handling & Recovery

### Error Categories
1. **Transient Errors**: Network timeouts, temporary resource unavailability
2. **Resource Errors**: Disk full, GPU OOM, catalog locked
3. **Fatal Errors**: Corrupted files, invalid configuration

### Recovery Strategies
- **Retry with Exponential Backoff**: 3 attempts with increasing delays
- **Failsafe State Saving**: Checkpoint creation before operations
- **Automatic Rollback**: Snapshot restoration on failure
- **Dead Letter Queue**: Failed jobs moved to manual review

## Deployment Architecture

### Development Environment
- Python 3.9+
- Node.js 16+
- Redis 6+
- Ollama with Llama 3.1 8B
- Adobe Lightroom Classic

### Production Deployment
- Standalone executable (PyInstaller)
- Embedded SQLite database
- Local Redis instance
- System service/daemon

## Monitoring & Observability

### Logging
- Structured JSON logs
- Log rotation (daily)
- Separate logs for errors, performance, and audit

### Metrics
- Processing time per photo
- Success/failure rates
- GPU/CPU utilization
- Queue depth and latency

### Health Checks
- `/api/system/health` endpoint
- Component status monitoring
- Resource availability checks

## Technology Stack

### Backend
- **Python 3.9+**: Core application
- **Flask**: REST API framework
- **Flask-SocketIO**: WebSocket support
- **Celery**: Async task queue
- **Redis**: Cache and message broker
- **SQLAlchemy**: ORM
- **SQLite**: Database

### AI/ML
- **Ollama**: LLM runtime
- **Llama 3.1**: Language model
- **OpenCV**: Image processing
- **ONNX Runtime**: Model inference

### Frontend
- **PyQt6**: Desktop GUI
- **React 18**: Mobile web UI
- **Tailwind CSS**: Styling
- **Workbox**: PWA support

### Integration
- **Lua**: Lightroom plugin
- **Lightroom SDK**: Plugin API
- **rclone**: Cloud sync

## Future Architecture Considerations

### Scalability
- Multi-user support
- Distributed processing
- Cloud deployment option

### Extensibility
- Plugin system for custom processors
- External AI model integration
- Custom preset marketplace

### Integration
- Adobe Photoshop integration
- Capture One support
- Cloud storage providers

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-09  
**Maintained By**: Junmai AutoDev Development Team
