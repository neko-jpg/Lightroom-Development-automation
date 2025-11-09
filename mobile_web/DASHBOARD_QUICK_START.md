# Mobile Dashboard - Quick Start Guide

## Overview

モバイルダッシュボードは、Junmai AutoDevシステムの状態を監視し、セッションを管理するためのモバイルファーストなWebインターフェースです。

## Features

### 📊 System Status
- システム稼働状態のリアルタイム表示
- Lightroom接続状態
- LLMモデル情報
- GPU温度・使用率（利用可能な場合）
- 自動更新: 5秒ごと

### 📈 Daily Statistics
- 本日の処理済み写真数
- 成功率（承認率）
- 平均処理時間
- 自動更新: 30秒ごと

### 📁 Active Sessions
- アクティブなセッション一覧
- 処理進捗バー
- 残り時間（ETA）表示
- タップでセッション詳細へ
- 自動更新: 10秒ごと

### ⚡ Quick Actions
- 承認キューへのアクセス（未承認数バッジ付き）
- セッション一覧へのアクセス
- 設定画面へのアクセス

## Getting Started

### 1. Start the Backend Server

```bash
cd local_bridge
python app.py
```

Backend server will start on `http://localhost:5100`

### 2. Start the Mobile Web App (Development)

```bash
cd mobile_web
npm start
```

The app will open at `http://localhost:3000`

### 3. Build for Production

```bash
cd mobile_web
npm run build
```

Production files will be in `mobile_web/build/`

## Configuration

### Environment Variables

Create a `.env` file in `mobile_web/` directory:

```env
REACT_APP_API_URL=http://localhost:5100
REACT_APP_WS_URL=ws://localhost:5100/ws
REACT_APP_NAME=Junmai AutoDev
REACT_APP_VERSION=1.0.0
REACT_APP_ENABLE_NOTIFICATIONS=true
REACT_APP_ENABLE_OFFLINE=true
```

## Component Architecture

```
Dashboard (Page)
├── SystemStatus (Component)
│   ├── System status
│   ├── Lightroom connection
│   ├── LLM info
│   └── Resource usage
├── DailyStats (Component)
│   ├── Photos processed
│   ├── Success rate
│   └── Average time
├── SessionList (Component)
│   ├── Session cards
│   ├── Progress bars
│   └── ETA calculation
└── QuickActions (Component)
    ├── Approval queue button
    ├── Sessions button
    └── Settings button
```

## API Integration

### API Service (`src/services/api.js`)

```javascript
import apiService from '../services/api';

// Get system status
const status = await apiService.getSystemStatus();

// Get sessions
const sessions = await apiService.getSessions({ active_only: true, limit: 10 });

// Get daily statistics
const stats = await apiService.getDailyStatistics();

// Get approval queue
const queue = await apiService.getApprovalQueue(100);
```

## Responsive Design

### Breakpoints
- Mobile: < 640px
- Tablet: 640px - 768px
- Desktop: > 768px

### Touch Targets
- Minimum size: 44x44px
- Adequate spacing between elements
- Tap feedback animations

## Auto-Refresh Strategy

| Component | Interval | Reason |
|-----------|----------|--------|
| SystemStatus | 5s | Real-time monitoring |
| SessionList | 10s | Progress updates |
| DailyStats | 30s | Statistical data |
| QuickActions | 15s | Approval count |

## Error Handling

All components include:
- Loading states
- Error messages
- Retry buttons
- Fallback displays

## Testing

### Manual Testing

1. **System Status**
   - Verify status badges display correctly
   - Check GPU info (if available)
   - Confirm auto-refresh works

2. **Sessions**
   - Create a test session
   - Verify progress bar updates
   - Check ETA calculation
   - Test navigation to session detail

3. **Statistics**
   - Process some photos
   - Verify counts update
   - Check success rate calculation

4. **Quick Actions**
   - Test all navigation buttons
   - Verify approval count badge

### Browser Testing

Test on:
- Chrome/Edge (Desktop & Mobile)
- Safari (iOS)
- Firefox
- Samsung Internet

## Troubleshooting

### Backend Connection Issues

**Problem**: "Failed to load status" error

**Solution**:
1. Verify backend is running: `http://localhost:5100/system/health`
2. Check CORS settings in backend
3. Verify `.env` file has correct `REACT_APP_API_URL`

### Build Errors

**Problem**: ESLint errors during build

**Solution**:
1. Check for undefined variables
2. Add `// eslint-disable-next-line` comments if needed
3. Run `npm run build` to see detailed errors

### Auto-Refresh Not Working

**Problem**: Data not updating automatically

**Solution**:
1. Check browser console for errors
2. Verify API endpoints are responding
3. Check network tab for failed requests

## Performance Tips

1. **Optimize API Calls**
   - Use appropriate refresh intervals
   - Implement request cancellation
   - Cache responses when possible

2. **Reduce Bundle Size**
   - Use code splitting
   - Lazy load components
   - Optimize images

3. **Improve Rendering**
   - Use React.memo for expensive components
   - Implement virtual scrolling for long lists
   - Debounce user inputs

## Next Steps

After completing the dashboard:

1. **Task 34**: Implement mobile approval interface
2. **Task 35**: Add push notifications
3. **Task 30**: Integrate WebSocket for real-time updates

## Resources

- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PWA Guide](https://web.dev/progressive-web-apps/)
- [Mobile Web Best Practices](https://developers.google.com/web/fundamentals)

## Support

For issues or questions:
1. Check the completion summary: `TASK_33_COMPLETION_SUMMARY.md`
2. Review the architecture: `ARCHITECTURE.md`
3. Check the main README: `README.md`

---

**Last Updated**: 2025-11-09  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
