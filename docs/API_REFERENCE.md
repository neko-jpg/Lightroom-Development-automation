# Junmai AutoDev - API Reference

## Overview

This document provides comprehensive API reference for the Junmai AutoDev REST API and WebSocket interface.

**Base URL**: `http://localhost:5100`  
**API Version**: v1  
**Authentication**: JWT Bearer Token (optional, configurable)

## Table of Contents

1. [Authentication](#authentication)
2. [Session Management](#session-management)
3. [Photo Management](#photo-management)
4. [Job Management](#job-management)
5. [Approval Queue](#approval-queue)
6. [Statistics](#statistics)
7. [System Management](#system-management)
8. [Notifications](#notifications)
9. [WebSocket Events](#websocket-events)
10. [Error Handling](#error-handling)

---

## Authentication

### POST /api/auth/login

Authenticate and receive JWT token.

**Request Body**:
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

### POST /api/auth/refresh

Refresh access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

### POST /api/auth/logout

Invalidate current token.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

---

## Session Management

### GET /api/sessions

List all sessions with optional filtering.

**Query Parameters**:
- `status` (optional): Filter by status (`importing`, `selecting`, `developing`, `exporting`, `completed`)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "sessions": [
    {
      "id": 1,
      "name": "2025-11-08_Wedding",
      "created_at": "2025-11-08T14:30:00Z",
      "import_folder": "D:/Photos/Wedding",
      "total_photos": 120,
      "processed_photos": 45,
      "status": "developing"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### GET /api/sessions/:id

Get detailed information about a specific session.

**Path Parameters**:
- `id`: Session ID

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "2025-11-08_Wedding",
  "created_at": "2025-11-08T14:30:00Z",
  "import_folder": "D:/Photos/Wedding",
  "total_photos": 120,
  "processed_photos": 45,
  "status": "developing",
  "statistics": {
    "avg_ai_score": 4.2,
    "approval_rate": 0.85,
    "avg_processing_time": 5.3
  },
  "photos": [
    {
      "id": 1001,
      "file_name": "IMG_5432.CR3",
      "ai_score": 4.5,
      "status": "completed"
    }
  ]
}
```

### POST /api/sessions

Create a new session.

**Request Body**:
```json
{
  "name": "2025-11-09_Portrait",
  "import_folder": "D:/Photos/Portrait"
}
```

**Response** (201 Created):
```json
{
  "id": 2,
  "name": "2025-11-09_Portrait",
  "created_at": "2025-11-09T10:00:00Z",
  "status": "importing"
}
```

### PATCH /api/sessions/:id

Update session information.

**Path Parameters**:
- `id`: Session ID

**Request Body**:
```json
{
  "name": "2025-11-09_Portrait_Updated",
  "status": "completed"
}
```

**Response** (200 OK):
```json
{
  "id": 2,
  "name": "2025-11-09_Portrait_Updated",
  "status": "completed"
}
```

### DELETE /api/sessions/:id

Delete a session and optionally its photos.

**Path Parameters**:
- `id`: Session ID

**Query Parameters**:
- `delete_photos` (optional): Boolean, delete associated photos (default: false)

**Response** (200 OK):
```json
{
  "message": "Session deleted successfully"
}
```

---

## Photo Management

### GET /api/photos

List photos with filtering and pagination.

**Query Parameters**:
- `session_id` (optional): Filter by session
- `status` (optional): Filter by status
- `min_score` (optional): Minimum AI score (1-5)
- `context_tag` (optional): Filter by context tag
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "photos": [
    {
      "id": 1001,
      "session_id": 1,
      "file_name": "IMG_5432.CR3",
      "file_path": "D:/Photos/Wedding/IMG_5432.CR3",
      "ai_score": 4.5,
      "focus_score": 4.8,
      "exposure_score": 4.2,
      "composition_score": 4.3,
      "subject_type": "portrait",
      "detected_faces": 2,
      "context_tag": "backlit_portrait",
      "selected_preset": "WhiteLayer_Transparency_v4",
      "status": "completed",
      "approved": false,
      "capture_time": "2025-11-08T15:30:00Z"
    }
  ],
  "total": 120,
  "limit": 50,
  "offset": 0
}
```

### GET /api/photos/:id

Get detailed information about a specific photo.

**Path Parameters**:
- `id`: Photo ID

**Response** (200 OK):
```json
{
  "id": 1001,
  "session_id": 1,
  "file_name": "IMG_5432.CR3",
  "file_path": "D:/Photos/Wedding/IMG_5432.CR3",
  "file_size": 25600000,
  "import_time": "2025-11-08T14:35:00Z",
  "camera_make": "Canon",
  "camera_model": "EOS R5",
  "lens": "RF 50mm F1.2 L USM",
  "focal_length": 50.0,
  "aperture": 1.2,
  "shutter_speed": "1/200",
  "iso": 400,
  "capture_time": "2025-11-08T15:30:00Z",
  "gps_lat": 35.6762,
  "gps_lon": 139.6503,
  "ai_score": 4.5,
  "focus_score": 4.8,
  "exposure_score": 4.2,
  "composition_score": 4.3,
  "subject_type": "portrait",
  "detected_faces": 2,
  "context_tag": "backlit_portrait",
  "selected_preset": "WhiteLayer_Transparency_v4",
  "status": "completed",
  "approved": false,
  "lr_catalog_id": "ABC123",
  "virtual_copy_id": "VC001"
}
```

### PATCH /api/photos/:id

Update photo information.

**Path Parameters**:
- `id`: Photo ID

**Request Body**:
```json
{
  "approved": true,
  "status": "completed"
}
```

**Response** (200 OK):
```json
{
  "id": 1001,
  "approved": true,
  "approved_at": "2025-11-09T10:00:00Z",
  "status": "completed"
}
```

### GET /api/photos/:id/thumbnail

Get photo thumbnail image.

**Path Parameters**:
- `id`: Photo ID

**Query Parameters**:
- `size` (optional): Thumbnail size (`small`, `medium`, `large`, default: `medium`)

**Response** (200 OK):
- Content-Type: `image/jpeg`
- Binary image data

---

## Job Management

### GET /api/jobs

List jobs with filtering.

**Query Parameters**:
- `status` (optional): Filter by status (`pending`, `processing`, `completed`, `failed`)
- `priority` (optional): Filter by priority (1-3)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "id": "job_abc123",
      "photo_id": 1001,
      "priority": 2,
      "status": "processing",
      "created_at": "2025-11-09T10:00:00Z",
      "started_at": "2025-11-09T10:01:00Z",
      "retry_count": 0
    }
  ],
  "total": 45,
  "limit": 50,
  "offset": 0
}
```

### GET /api/jobs/:id

Get detailed job information.

**Path Parameters**:
- `id`: Job ID

**Response** (200 OK):
```json
{
  "id": "job_abc123",
  "photo_id": 1001,
  "priority": 2,
  "config_json": "{\"preset\": \"WhiteLayer_v4\", \"blend\": 60}",
  "status": "completed",
  "created_at": "2025-11-09T10:00:00Z",
  "started_at": "2025-11-09T10:01:00Z",
  "completed_at": "2025-11-09T10:01:05Z",
  "retry_count": 0
}
```

### POST /api/jobs

Create a new job.

**Request Body**:
```json
{
  "photo_id": 1001,
  "priority": 2,
  "config": {
    "preset": "WhiteLayer_Transparency_v4",
    "blend": 60,
    "adjustments": {
      "exposure": -0.15,
      "highlights": -18,
      "shadows": 12
    }
  }
}
```

**Response** (201 Created):
```json
{
  "id": "job_abc123",
  "photo_id": 1001,
  "priority": 2,
  "status": "pending",
  "created_at": "2025-11-09T10:00:00Z"
}
```

### DELETE /api/jobs/:id

Cancel a pending or processing job.

**Path Parameters**:
- `id`: Job ID

**Response** (200 OK):
```json
{
  "message": "Job cancelled successfully"
}
```

### POST /api/jobs/:id/retry

Retry a failed job.

**Path Parameters**:
- `id`: Job ID

**Response** (200 OK):
```json
{
  "id": "job_abc123",
  "status": "pending",
  "retry_count": 1
}
```

---

## Approval Queue

### GET /api/approval/queue

Get photos pending approval.

**Query Parameters**:
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "queue": [
    {
      "id": 1001,
      "file_name": "IMG_5432.CR3",
      "ai_score": 4.5,
      "context_tag": "backlit_portrait",
      "selected_preset": "WhiteLayer_Transparency_v4",
      "thumbnail_url": "/api/photos/1001/thumbnail",
      "preview_url": "/api/photos/1001/preview"
    }
  ],
  "total": 12,
  "limit": 20,
  "offset": 0
}
```

### POST /api/approval/:photo_id/approve

Approve a photo for export.

**Path Parameters**:
- `photo_id`: Photo ID

**Request Body** (optional):
```json
{
  "export_presets": ["SNS", "Print"]
}
```

**Response** (200 OK):
```json
{
  "photo_id": 1001,
  "approved": true,
  "approved_at": "2025-11-09T10:00:00Z",
  "message": "Photo approved and queued for export"
}
```

### POST /api/approval/:photo_id/reject

Reject a photo.

**Path Parameters**:
- `photo_id`: Photo ID

**Request Body** (optional):
```json
{
  "reason": "Out of focus"
}
```

**Response** (200 OK):
```json
{
  "photo_id": 1001,
  "approved": false,
  "rejection_reason": "Out of focus",
  "message": "Photo rejected"
}
```

### POST /api/approval/:photo_id/modify

Request modifications to a photo.

**Path Parameters**:
- `photo_id`: Photo ID

**Request Body**:
```json
{
  "adjustments": {
    "exposure": -0.3,
    "highlights": -25
  },
  "preset": "WhiteLayer_Transparency_v4",
  "blend": 50
}
```

**Response** (200 OK):
```json
{
  "photo_id": 1001,
  "job_id": "job_xyz789",
  "message": "Modification job created"
}
```

---

## Statistics

### GET /api/statistics/daily

Get daily statistics.

**Query Parameters**:
- `date` (optional): Date in YYYY-MM-DD format (default: today)

**Response** (200 OK):
```json
{
  "date": "2025-11-09",
  "total_imported": 127,
  "total_selected": 89,
  "total_processed": 89,
  "total_exported": 45,
  "avg_processing_time": 5.3,
  "success_rate": 0.94,
  "avg_ai_score": 4.1,
  "preset_usage": {
    "WhiteLayer_Transparency_v4": 45,
    "LowLight_NR_v2": 23,
    "Landscape_Sky_v3": 21
  }
}
```

### GET /api/statistics/weekly

Get weekly statistics.

**Query Parameters**:
- `week` (optional): Week number (default: current week)
- `year` (optional): Year (default: current year)

**Response** (200 OK):
```json
{
  "week": 45,
  "year": 2025,
  "total_imported": 856,
  "total_selected": 623,
  "total_processed": 623,
  "total_exported": 312,
  "avg_processing_time": 5.1,
  "success_rate": 0.96,
  "daily_breakdown": [
    {
      "date": "2025-11-03",
      "total_imported": 120,
      "total_processed": 89
    }
  ]
}
```

### GET /api/statistics/monthly

Get monthly statistics.

**Query Parameters**:
- `month` (optional): Month (1-12, default: current month)
- `year` (optional): Year (default: current year)

**Response** (200 OK):
```json
{
  "month": 11,
  "year": 2025,
  "total_imported": 3420,
  "total_selected": 2567,
  "total_processed": 2567,
  "total_exported": 1284,
  "avg_processing_time": 5.2,
  "success_rate": 0.95,
  "top_contexts": [
    {"context": "backlit_portrait", "count": 456},
    {"context": "landscape_sky", "count": 234}
  ]
}
```

### GET /api/statistics/presets

Get preset usage statistics.

**Query Parameters**:
- `period` (optional): Time period (`day`, `week`, `month`, default: `month`)

**Response** (200 OK):
```json
{
  "period": "month",
  "presets": [
    {
      "name": "WhiteLayer_Transparency_v4",
      "version": "v4",
      "usage_count": 456,
      "avg_approval_rate": 0.87,
      "avg_processing_time": 5.1
    },
    {
      "name": "LowLight_NR_v2",
      "version": "v2",
      "usage_count": 234,
      "avg_approval_rate": 0.82,
      "avg_processing_time": 6.3
    }
  ]
}
```

---

## System Management

### GET /api/system/status

Get current system status.

**Response** (200 OK):
```json
{
  "status": "running",
  "lightroom_connected": true,
  "ollama_connected": true,
  "redis_connected": true,
  "gpu": {
    "available": true,
    "temperature": 45,
    "memory_used": 2100,
    "memory_total": 8192
  },
  "cpu": {
    "usage_percent": 35.2
  },
  "queue": {
    "pending_jobs": 12,
    "processing_jobs": 3
  },
  "uptime_seconds": 86400
}
```

### GET /api/system/health

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "ollama": "ok",
    "lightroom": "ok"
  },
  "timestamp": "2025-11-09T10:00:00Z"
}
```

### POST /api/system/pause

Pause all processing.

**Response** (200 OK):
```json
{
  "message": "System paused",
  "paused_at": "2025-11-09T10:00:00Z"
}
```

### POST /api/system/resume

Resume processing.

**Response** (200 OK):
```json
{
  "message": "System resumed",
  "resumed_at": "2025-11-09T10:00:00Z"
}
```

### GET /api/system/logs

Get system logs.

**Query Parameters**:
- `level` (optional): Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `limit` (optional): Number of log entries (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "logs": [
    {
      "timestamp": "2025-11-09T10:00:00Z",
      "level": "INFO",
      "message": "Photo processed successfully",
      "photo_id": 1001,
      "job_id": "job_abc123"
    }
  ],
  "total": 1000,
  "limit": 100,
  "offset": 0
}
```

---

## Notifications

### GET /api/notifications

Get notification history.

**Query Parameters**:
- `type` (optional): Notification type (`desktop`, `email`, `line`)
- `limit` (optional): Number of results (default: 50)

**Response** (200 OK):
```json
{
  "notifications": [
    {
      "id": 1,
      "type": "desktop",
      "title": "Processing Complete",
      "message": "89 photos processed successfully",
      "priority": "medium",
      "sent_at": "2025-11-09T10:00:00Z",
      "read": false
    }
  ],
  "total": 25,
  "limit": 50
}
```

### POST /api/notifications/test

Send test notification.

**Request Body**:
```json
{
  "type": "desktop",
  "title": "Test Notification",
  "message": "This is a test"
}
```

**Response** (200 OK):
```json
{
  "message": "Test notification sent",
  "success": true
}
```

---

## WebSocket Events

### Connection

Connect to WebSocket server:

```javascript
const ws = new WebSocket('ws://localhost:5100/ws');
```

### Client → Server Events

#### subscribe_session
Subscribe to session updates.

```json
{
  "type": "subscribe_session",
  "session_id": 1
}
```

#### subscribe_jobs
Subscribe to job updates.

```json
{
  "type": "subscribe_jobs"
}
```

#### ping
Keep-alive ping.

```json
{
  "type": "ping"
}
```

### Server → Client Events

#### photo_imported
New photo imported.

```json
{
  "type": "photo_imported",
  "session_id": 1,
  "photo_id": 1001,
  "file_name": "IMG_5432.CR3",
  "timestamp": "2025-11-09T10:00:00Z"
}
```

#### photo_analyzed
AI analysis complete.

```json
{
  "type": "photo_analyzed",
  "photo_id": 1001,
  "ai_score": 4.5,
  "context_tag": "backlit_portrait",
  "timestamp": "2025-11-09T10:00:05Z"
}
```

#### job_started
Job processing started.

```json
{
  "type": "job_started",
  "job_id": "job_abc123",
  "photo_id": 1001,
  "timestamp": "2025-11-09T10:01:00Z"
}
```

#### job_progress
Job progress update.

```json
{
  "type": "job_progress",
  "job_id": "job_abc123",
  "progress": 0.5,
  "stage": "applying_preset",
  "timestamp": "2025-11-09T10:01:03Z"
}
```

#### job_completed
Job completed successfully.

```json
{
  "type": "job_completed",
  "job_id": "job_abc123",
  "photo_id": 1001,
  "processing_time": 5.2,
  "timestamp": "2025-11-09T10:01:05Z"
}
```

#### job_failed
Job failed.

```json
{
  "type": "job_failed",
  "job_id": "job_abc123",
  "photo_id": 1001,
  "error": "GPU memory allocation failed",
  "timestamp": "2025-11-09T10:01:05Z"
}
```

#### system_status
System status update.

```json
{
  "type": "system_status",
  "status": "running",
  "queue_depth": 12,
  "cpu_usage": 35.2,
  "gpu_temp": 45,
  "timestamp": "2025-11-09T10:00:00Z"
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Photo with ID 9999 not found",
    "details": {
      "photo_id": 9999
    }
  }
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Codes

- `INVALID_REQUEST`: Invalid request format or parameters
- `AUTHENTICATION_REQUIRED`: Authentication token missing
- `INVALID_TOKEN`: Invalid or expired token
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `DUPLICATE_RESOURCE`: Resource already exists
- `VALIDATION_ERROR`: Request validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Internal server error
- `SERVICE_UNAVAILABLE`: Service temporarily unavailable
- `GPU_ERROR`: GPU-related error
- `LIGHTROOM_ERROR`: Lightroom integration error
- `OLLAMA_ERROR`: Ollama/LLM error

### Rate Limiting

API requests are rate-limited:

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699545600
```

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `limit`: Number of results per page (default: 50, max: 100)
- `offset`: Number of results to skip (default: 0)

**Response Headers**:
```
X-Total-Count: 1000
X-Limit: 50
X-Offset: 0
```

---

## Filtering

List endpoints support filtering via query parameters:

**Example**:
```
GET /api/photos?session_id=1&min_score=4.0&status=completed
```

---

## Sorting

List endpoints support sorting:

**Query Parameter**:
- `sort`: Field to sort by (prefix with `-` for descending)

**Example**:
```
GET /api/photos?sort=-ai_score
GET /api/sessions?sort=created_at
```

---

## Versioning

API version is included in the URL path:

```
/api/v1/sessions
/api/v2/sessions (future)
```

Current version: `v1` (implicit, no version prefix required)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-09  
**API Version**: v1
