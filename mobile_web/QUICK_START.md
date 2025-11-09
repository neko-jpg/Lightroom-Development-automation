# Quick Start Guide - Junmai AutoDev Mobile Web

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
cd mobile_web
npm install
```

### 2. Start Development Server
```bash
npm start
```
Opens at `http://localhost:3000`

### 3. Build for Production
```bash
npm run build
```

## 📱 What's Included

✅ **React 18** - Modern React with hooks  
✅ **React Router 6** - Client-side routing  
✅ **Tailwind CSS** - Utility-first styling  
✅ **PWA** - Service worker + offline support  
✅ **Mobile-First** - Optimized for smartphones  

## 🗂️ Project Structure

```
mobile_web/
├── src/
│   ├── components/     # Layout, Navigation
│   ├── pages/          # Dashboard, Approval, Sessions, Settings
│   ├── App.js          # Main app with routing
│   └── index.js        # Entry point
├── public/
│   ├── manifest.json   # PWA manifest
│   └── index.html      # HTML template
└── package.json        # Dependencies
```

## 🔗 Routes

- `/dashboard` - System overview
- `/approval` - Photo approval queue
- `/sessions` - Session management
- `/settings` - App configuration

## 🔧 Configuration

Edit `.env` for API settings:
```env
REACT_APP_API_URL=http://localhost:5100
REACT_APP_WS_URL=ws://localhost:5100/ws
```

## 📝 Next Tasks

- **Task 33**: Implement dashboard with real data
- **Task 34**: Add swipe-based approval interface
- **Task 35**: Integrate push notifications

## 📚 Documentation

- `README.md` - Full project documentation
- `SETUP.md` - Detailed setup guide
- `TASK_32_COMPLETION_SUMMARY.md` - Implementation details

## 🆘 Troubleshooting

**npm install fails?**
```bash
npm cache clean --force
npm install
```

**Styles not working?**
```bash
# Restart dev server
npm start
```

**Need help?**
Check `SETUP.md` for detailed troubleshooting.

---

**Status**: ✅ Ready for development  
**Version**: 1.0.0  
**Last Updated**: 2025-11-09
