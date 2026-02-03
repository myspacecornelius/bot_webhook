# Phantom Bot - Deployment Guide

## 🎉 Production Deployment Complete

### Backend (Fly.io)
- **URL**: https://phantom-bot-api.fly.dev
- **Status**: ✅ Live and Running
- **Features**:
  - FastAPI REST API
  - WebSocket real-time updates
  - Shopify checkout with password bypass
  - Quick task creation
  - Monitor management

### Frontend (Ready for Netlify)
- **Build**: ✅ Complete (`frontend/dist`)
- **Backend URL**: Configured to use Fly.io
- **WebSocket**: Configured for production

---

## 🚀 Novel Features Implemented

### 1. **Advanced Monitor Configuration**
- **Quick Presets**: One-click setup for popular products
  - Nike Dunks (Purple theme)
  - Air Jordans (Red theme)
  - Yeezys (Cyan theme)
  - New Balance (Green theme)
- **Smart Filtering**: Price range, keywords, store selection
- **Visual Store Cards**: Real-time stats and health monitoring

### 2. **Enhanced Product Feed**
- **Visual Product Cards**: 
  - Product images
  - Profit indicators with color coding
  - Priority badges (HIGH PROFIT glow effect)
  - Available sizes display
- **Advanced Filters**:
  - Priority level (High/Medium/Low)
  - Minimum profit threshold
  - Maximum price cap
  - Store-specific filtering
- **One-Click Quick Tasks**: Create tasks directly from product cards
- **Sound Notifications**: Audio alerts for high-priority products
- **Real-time Stats**: Total products, high priority count, average profit

### 3. **Real-time Updates**
- WebSocket integration for live data
- Automatic reconnection with exponential backoff
- Live connection status indicator
- Reduced polling (10-15s intervals)

### 4. **Password Page Bypass**
- Automatic detection of password-protected Shopify stores
- Multiple bypass strategies:
  - Direct API access (products.json)
  - Common password attempts
  - Preview theme URL bypass

---

## 📦 Deployment Instructions

### Deploy Frontend to Netlify

#### Option 1: Netlify Drop (Easiest)
1. Go to https://app.netlify.com/drop
2. Drag the `frontend/dist` folder onto the page
3. Get your live URL instantly

#### Option 2: Netlify CLI
```bash
cd frontend
npx netlify-cli deploy --prod --dir=dist
```

#### Option 3: Git Integration
1. Push code to GitHub
2. Connect repository to Netlify
3. Build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Environment variables: `VITE_API_URL=https://phantom-bot-api.fly.dev/api`

---

## 🔧 Local Development

### Start Backend
```bash
cd /Users/davidnichols/bot_webhook
source venv/bin/activate
python main.py --mode server --port 8081
```

### Start Frontend
```bash
cd /Users/davidnichols/bot_webhook/frontend
npm run dev
```

Frontend will be at `http://localhost:5173`

---

## 🎯 Key Improvements Summary

| Feature | Status | Impact |
|---------|--------|--------|
| WebSocket Real-time Updates | ✅ | Reduced CPU usage, instant updates |
| Password Page Bypass | ✅ | Access more Shopify stores |
| Quick Task System | ✅ | Faster task creation from URLs |
| Monitor Presets | ✅ | One-click configuration |
| Advanced Filtering | ✅ | Find profitable products faster |
| Visual Product Cards | ✅ | Better UX, profit visibility |
| Sound Notifications | ✅ | Never miss high-priority items |
| Production Deployment | ✅ | Accessible from anywhere |

---

## 🌐 Production URLs

Once frontend is deployed:
- **Frontend**: `https://[your-netlify-subdomain].netlify.app`
- **Backend API**: `https://phantom-bot-api.fly.dev`
- **WebSocket**: `wss://phantom-bot-api.fly.dev/ws/events`

---

## 📝 Next Steps

1. **Deploy Frontend**: Use one of the Netlify options above
2. **Test End-to-End**: Verify monitors, tasks, and WebSocket connection
3. **Add Profiles**: Configure payment/shipping information
4. **Add Proxies**: Upload residential proxies for better success rates
5. **Start Monitoring**: Use quick presets or custom configuration

---

## 🎨 Novel UI Features

- **Animated Product Cards**: Hover effects, scale transitions
- **Glow Effects**: High-priority products pulse with green glow
- **Color-Coded Profits**: Green (high), yellow (medium), red (low)
- **Smart Badges**: Priority indicators, store tags, match confidence
- **Responsive Grid**: Adapts from 1-4 columns based on screen size
- **Dark Theme**: Optimized for long monitoring sessions

---

Built with ❤️ for the sneaker community
