# Extended API Reference

## Overview

This document provides a comprehensive reference for the extended REST API endpoints in Junmai AutoDev.

**Base URL**: `http://localhost:5100/api`

**Requirements**: 9.1

---

## Session Management Endpoints

### GET /api/sessions
Get list of sessions with filtering and pagination.

**Query Parameters**:
- `status` (optional): Filter by status
- `limit` (optional, default: 50): Maximum number of sessions
- `offset` (optional, default: 0): Pagination offset
- `active_only` (optional, default: false): Return only active sessions
- `sort` (optional, default: created_at): Sort field (created_at, name, total_photos)
- `order` (optional, default: desc): Sort order (asc, desc)

**Response**:
```json
{
  "sessions": [
    {
      "id": 1,
      "name": "Wedding 2025-11-08",
      "created_at": "2025-11-08T10:00:00",
      "import_folder": "/photos/wedding",
      "total_photos": 120,
      "processed_photos": 45,
      "status": "processing",
      "progress_percent": 37.5
    }
  ],
  "count": 1,
  "total": 1,
  "offset": 0,
  "limit": 50
}
```

### GET /api/sessions/{session_id}
Get detailed information about a specific session.

**Response**:
```json
{
  "id": 1,
  "name": "Wedding 2025-11-08",
  "created_at": "2025-11-08T10:00:00",
  "import_folder": "/photos/wedding",
  "total_photos": 120,
  "processed_photos": 45,
  "status": "processing",
  "progress_percent": 37.5,
  "photo_stats": {
    "imported": 120,
    "analyzed": 80,
    "completed": 45
  },
  "score_distribution": {
    "3": 20,
    "4": 40,
    "5": 15
  }
}
```

### POST /api/sessions
Create a new session.

**Request Body**:
```json
{
  "name": "Portrait Session",
  "import_folder": "/photos/portrait"
}
```

**Response**: 201 Created
```json
{
  "id": 2,
  "name": "Portrait Session",
  "import_folder": "/photos/portrait",
  "status": "importing",
  "created_at": "2025-11-08T11:00:00"
}
```

### PATCH /api/sessions/{session_id}
Update session information.

**Request Body**:
```json
{
  "name": "Updated Session Name",
  "status": "completed"
}
```

**Response**: 200 OK

### DELETE /api/sessions/{session_id}
Delete a session and all associated data.

**Response**: 200 OK
```json
{
  "message": "Session deleted successfully",
  "session_id": 1
}
```

---

## Photo Management Endpoints

### GET /api/photos
Get list of photos with filtering and pagination.

**Query Parameters**:
- `session_id` (optional): Filter by session ID
- `status` (optional): Filter by status
- `min_score` (optional): Minimum AI score
- `approved` (optional): Filter by approval status (true/false)
- `limit` (optional, default: 100): Maximum number of photos
- `offset` (optional, default: 0): Pagination offset
- `sort` (optional, default: import_time): Sort field
- `order` (optional, default: desc): Sort order

**Response**:
```json
{
  "photos": [
    {
      "id": 1,
      "session_id": 1,
      "file_name": "IMG_5432.CR3",
      "ai_score": 4.2,
      "status": "completed",
      "approved": false
    }
  ],
  "count": 1,
  "total": 1,
  "offset": 0,
  "limit": 100
}
```

### GET /api/photos/{photo_id}
Get detailed information about a specific photo.

**Response**: 200 OK

### PATCH /api/photos/{photo_id}
Update photo information.

**Request Body**:
```json
{
  "status": "approved",
  "approved": true,
  "context_tag": "backlit_portrait",
  "selected_preset": "WhiteLayer_v4"
}
```

**Response**: 200 OK

### GET /api/photos/{photo_id}/thumbnail
Get thumbnail for a photo.

**Query Parameters**:
- `size` (optional, default: medium): Thumbnail size (small=200, medium=400, large=800)

**Response**: JPEG image

---

## Job Management Endpoints

### GET /api/jobs
Get list of jobs with filtering and pagination.

**Query Parameters**:
- `status` (optional): Filter by status
- `photo_id` (optional): Filter by photo ID
- `priority` (optional): Filter by priority
- `limit` (optional, default: 100): Maximum number of jobs
- `offset` (optional, default: 0): Pagination offset

**Response**:
```json
{
  "jobs": [
    {
      "id": "abc123",
      "photo_id": 1,
      "priority": 2,
      "status": "pending",
      "created_at": "2025-11-08T10:00:00"
    }
  ],
  "count": 1,
  "total": 1
}
```

### GET /api/jobs/{job_id}
Get detailed information about a specific job.

**Response**: 200 OK

### POST /api/jobs
Create a new job.

**Request Body**:
```json
{
  "photo_id": 1,
  "config": {
    "version": "1.0",
    "pipeline": [],
    "safety": {"snapshot": true, "dryRun": false}
  },
  "priority": 2
}
```

**Response**: 201 Created

### DELETE /api/jobs/{job_id}
Delete/cancel a job.

**Response**: 200 OK

---

## Approval Queue Endpoints

### GET /api/approval/queue
Get approval queue (photos awaiting approval).

**Query Parameters**:
- `session_id` (optional): Filter by session ID
- `min_score` (optional): Minimum AI score
- `limit` (optional, default: 100): Maximum number of photos
- `offset` (optional, default: 0): Pagination offset

**Response**:
```json
{
  "photos": [
    {
      "id": 1,
      "file_name": "IMG_5432.CR3",
      "ai_score": 4.2,
      "status": "completed",
      "approved": false
    }
  ],
  "count": 1,
  "total": 1
}
```

### POST /api/approval/{photo_id}/approve
Approve a photo.

**Request Body** (optional):
```json
{
  "auto_export": false
}
```

**Response**: 200 OK
```json
{
  "message": "Photo approved successfully",
  "photo_id": 1,
  "export_triggered": false
}
```

### POST /api/approval/{photo_id}/reject
Reject a photo.

**Request Body** (optional):
```json
{
  "reason": "Poor focus"
}
```

**Response**: 200 OK

### POST /api/approval/{photo_id}/modify
Request modification of photo preset.

**Request Body**:
```json
{
  "new_preset": "WhiteLayer_v5",
  "adjustments": {
    "exposure": 0.5
  }
}
```

**Response**: 200 OK

---

## Statistics Endpoints

### GET /api/statistics/daily
Get daily statistics.

**Query Parameters**:
- `date` (optional, default: today): Specific date (YYYY-MM-DD format)

**Response**:
```json
{
  "date": "2025-11-08",
  "total_imported": 127,
  "total_processed": 89,
  "total_approved": 67,
  "total_rejected": 22,
  "success_rate": 75.28,
  "avg_ai_score": 3.85,
  "avg_processing_time": 2.3
}
```

### GET /api/statistics/weekly
Get weekly statistics (last 7 days).

**Response**:
```json
{
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-11-08"
  },
  "total_imported": 450,
  "total_processed": 380,
  "total_approved": 320,
  "success_rate": 84.21,
  "daily_breakdown": [
    {"date": "2025-11-01", "imported": 50},
    {"date": "2025-11-02", "imported": 75}
  ]
}
```

### GET /api/statistics/monthly
Get monthly statistics (current month).

**Response**:
```json
{
  "period": {
    "year": 2025,
    "month": 11,
    "start_date": "2025-11-01",
    "end_date": "2025-11-30"
  },
  "total_imported": 1200,
  "total_processed": 980,
  "total_approved": 850,
  "success_rate": 86.73,
  "subject_distribution": {
    "portrait": 450,
    "landscape": 320,
    "sports": 210
  }
}
```

### GET /api/statistics/presets
Get preset usage statistics.

**Query Parameters**:
- `days` (optional, default: 30): Number of days to analyze

**Response**:
```json
{
  "period_days": 30,
  "presets": [
    {
      "preset_name": "WhiteLayer_v4",
      "usage_count": 450,
      "approval_rate": 87.5,
      "approved_count": 394
    }
  ],
  "total_presets": 5
}
```

---

## System Management Endpoints

### GET /api/system/status
Get detailed system status.

**Response**:
```json
{
  "system": "running",
  "timestamp": "2025-11-08T12:00:00",
  "sessions": {
    "active": 3
  },
  "jobs": {
    "pending": 45,
    "processing": 2
  },
  "approval_queue": {
    "count": 12
  },
  "resources": {
    "cpu_percent": 45.2,
    "memory_percent": 62.5,
    "memory_used_mb": 5120,
    "memory_total_mb": 8192,
    "gpu": {
      "available": true,
      "temperature": 65,
      "memory_used_mb": 2048,
      "memory_total_mb": 8192,
      "utilization": 35
    }
  }
}
```

### GET /api/system/health
System health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T12:00:00",
  "database": "connected"
}
```

### POST /api/system/pause
Pause system processing.

**Response**: 200 OK
```json
{
  "message": "System processing paused successfully"
}
```

### POST /api/system/resume
Resume system processing.

**Response**: 200 OK
```json
{
  "message": "System processing resumed successfully"
}
```

### GET /api/system/info
Get system information.

**Response**:
```json
{
  "version": "2.0",
  "system_name": "Junmai AutoDev",
  "llm_provider": "ollama",
  "llm_model": "llama3.1:8b-instruct",
  "auto_import": true,
  "auto_select": true,
  "auto_develop": true,
  "auto_export": false
}
```

---

## Error Responses

All endpoints return standard error responses:

**400 Bad Request**:
```json
{
  "error": "Description of what went wrong"
}
```

**404 Not Found**:
```json
{
  "error": "Resource not found"
}
```

**500 Internal Server Error**:
```json
{
  "error": "Internal server error: details"
}
```

---

## Authentication

Currently, the API does not require authentication. This will be added in Phase 10 (Task 31).

---

## Rate Limiting

No rate limiting is currently implemented. This will be added in Phase 10 (Task 31).

---

## CORS

CORS is not currently configured. This will be added in Phase 10 (Task 31) for web UI access.
