# Premium Features - Tier Gating Strategy

## 🎯 Feature Gating Philosophy

**Free/Starter Tier:** Basic functionality to prove value
**Pro Tier:** Power user features for serious resellers (80% of revenue)
**Elite Tier:** Automation & intelligence for maximum profit

---

## 🔒 Features by Tier

### **Starter ($29/month)**

**Included:**
- ✅ 5 concurrent tasks
- ✅ 2 active monitors (Shopify only)
- ✅ 20 tasks per day
- ✅ Manual task creation
- ✅ Basic product feed
- ✅ Email support

**Blocked:**
- ❌ Proxy support
- ❌ Quick tasks
- ❌ Auto-task creation
- ❌ Footsites/Nike modules
- ❌ Restock predictions
- ❌ Profit analysis
- ❌ API access
- ❌ Export data

**UI Indicators:**
- Grayed out "Add Proxy" button with "Pro" badge
- "Upgrade to Pro" tooltip on disabled features
- Usage bar showing 3/5 tasks used

---

### **Pro ($79/month)** - MOST POPULAR

**Everything in Starter, plus:**
- ✅ 50 concurrent tasks
- ✅ 10 active monitors
- ✅ 200 tasks per day
- ✅ **Proxy support** (unlimited proxies)
- ✅ **Quick tasks** (1-click from URL)
- ✅ **All site modules** (Shopify, Footsites, Nike)
- ✅ **Restock predictions** (ML-powered)
- ✅ **Profit analysis** (StockX/GOAT integration)
- ✅ **Monitor presets** (Dunks, Jordans, Yeezys)
- ✅ **Advanced filters** (price, profit, brand)
- ✅ **Success Theater** (animated celebrations)
- ✅ Priority email support

**Blocked:**
- ❌ Auto-task creation
- ❌ Early restock alerts (24h advance)
- ❌ API access
- ❌ Bulk operations
- ❌ Custom webhooks

---

### **Elite ($199/month)**

**Everything in Pro, plus:**
- ✅ **Unlimited tasks & monitors**
- ✅ **Auto-task creation** (AI creates tasks from high-profit products)
- ✅ **Early restock alerts** (24h before public)
- ✅ **API access** (integrate with your tools)
- ✅ **Bulk operations** (mass edit, duplicate, import/export)
- ✅ **Custom webhooks** (Discord, Slack, custom endpoints)
- ✅ **Priority queue** (your tasks run first)
- ✅ **Dedicated support** (1-hour response time)
- ✅ **Success guarantee** (refund if no checkouts in 30 days)

---

## 💎 Premium Features to Implement

### 1. **Auto-Task Creation** (Elite Only)

**What it does:**
- Monitors detect high-profit product (>$100 profit)
- Automatically creates task with optimal settings
- Uses best profile & proxy group
- Starts task immediately

**Implementation:**
```python
# In monitor manager
if event.profit > 100 and user.tier == "elite":
    auto_create_task(event)
```

**UI:**
- Toggle in Settings: "Auto-create tasks for high-profit items"
- Shows "🤖 AUTO" badge on auto-created tasks
- Notification when auto-task is created

---

### 2. **Early Restock Alerts** (Elite Only)

**What it does:**
- ML model predicts restocks 24h in advance
- Elite users get SMS/Discord alert
- Can set up tasks before restock happens

**Implementation:**
```python
# In restock tracker
if prediction.confidence > 0.8:
    if user.tier == "elite":
        send_early_alert(user, prediction)
```

**UI:**
- "🔔 Early Alert" badge on predicted restocks
- Settings toggle for alert channels (SMS, Discord, Email)

---

### 3. **API Access** (Elite Only)

**What it does:**
- REST API for external integrations
- Programmatic task creation
- Monitor data export
- Webhook endpoints

**Endpoints:**
```
POST /api/v1/tasks/create
GET /api/v1/monitors/events
POST /api/v1/webhooks/register
GET /api/v1/analytics/export
```

**UI:**
- API key management in Settings
- Usage dashboard (requests per day)
- Documentation link

---

### 4. **Bulk Operations** (Elite Only)

**What it does:**
- Select multiple tasks → Start/Stop/Delete all
- Duplicate task with different sizes
- Import tasks from CSV
- Export task history

**UI:**
- Checkbox selection in Tasks table
- "Bulk Actions" dropdown when items selected
- Import/Export buttons

---

### 5. **Priority Queue** (Elite Only)

**What it does:**
- Elite users' tasks execute first
- Dedicated compute resources
- Lower latency checkouts

**Implementation:**
```python
# In task queue
tasks = sorted(tasks, key=lambda t: (
    0 if t.user_tier == "elite" else 1,
    t.created_at
))
```

**UI:**
- "⚡ Priority" badge on Elite tasks
- Faster average checkout time displayed

---

### 6. **Custom Webhooks** (Elite Only)

**What it does:**
- Send checkout success to custom URL
- Discord/Slack integration
- Custom payload format

**UI:**
- Webhook management in Settings
- Test webhook button
- Event type selection (success, failure, restock)

---

### 7. **Advanced Analytics** (Pro+)

**What it does:**
- Profit tracking over time
- Success rate by store
- ROI calculator
- Export reports (CSV, PDF)

**UI:**
- Cop Calendar (already built!)
- Profit charts
- Store performance leaderboard

---

### 8. **Monitor Presets** (Pro+)

**What it does:**
- One-click monitor setup for popular products
- Pre-configured keywords, prices, stores
- Dunks, Jordans, Yeezys, New Balance

**UI:**
- Already built in `MonitorsEnhanced.tsx`!
- Just need to gate behind tier check

---

## 🚧 Implementation Checklist

### Backend Changes

**1. Add tier checks to routes:**
```python
from phantom.auth.middleware import require_tier, check_tier_limit

@app.post("/api/tasks/quick")
async def create_quick_task(
    data: QuickTaskCreate,
    _: bool = Depends(require_tier(UserTier.PRO))
):
    # Only Pro+ can use quick tasks
    ...

@app.post("/api/tasks/auto-create")
async def toggle_auto_tasks(
    enabled: bool,
    _: bool = Depends(require_tier(UserTier.ELITE))
):
    # Only Elite can use auto-tasks
    ...
```

**2. Add usage enforcement:**
```python
from phantom.api.auth_routes import usage_tracker

@app.post("/api/tasks")
async def create_task(task: TaskCreate, request: Request):
    limits = request.state.limits
    
    # Check limits
    check = usage_tracker.check_task_limit(
        request.state.user_id,
        limits["max_tasks"],
        limits["max_tasks_per_day"]
    )
    
    if not check["allowed"]:
        raise HTTPException(403, check["error"])
    
    # Create task
    usage_tracker.increment_task(request.state.user_id)
    ...
```

### Frontend Changes

**1. Add tier context:**
```typescript
// src/contexts/AuthContext.tsx
const [userTier, setUserTier] = useState('starter')
const [limits, setLimits] = useState({})
const [usage, setUsage] = useState({})
```

**2. Gate features in UI:**
```typescript
// In Tasks.tsx
{userTier === 'pro' || userTier === 'elite' ? (
  <button onClick={createQuickTask}>⚡ Quick Task</button>
) : (
  <button disabled className="opacity-50">
    ⚡ Quick Task
    <span className="badge">Pro</span>
  </button>
)}
```

**3. Add upgrade prompts:**
```typescript
// When user hits limit
<div className="upgrade-prompt">
  <h3>Task Limit Reached</h3>
  <p>You've used 5/5 tasks. Upgrade to Pro for 50 tasks.</p>
  <button onClick={openPricing}>Upgrade Now</button>
</div>
```

---

## 🎨 UI/UX for Gated Features

### **Tier Badges**
```tsx
<span className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs rounded font-bold">
  PRO
</span>
```

### **Disabled State**
- Grayed out with 50% opacity
- Tooltip: "Upgrade to [Tier] to unlock"
- Hover shows feature benefits

### **Usage Bars**
```tsx
<div className="usage-bar">
  <div className="fill" style={{ width: '60%' }} />
  <span>3/5 tasks used</span>
</div>
```

### **Upgrade CTAs**
- Inline in disabled features
- Banner at top when near limits
- Modal when limit hit

---

## 📊 Expected Impact

### Conversion Rates

| Tier | % of Users | Avg Revenue |
|------|------------|-------------|
| Starter | 20% | $29 |
| Pro | 70% | $79 |
| Elite | 10% | $199 |

**Average Revenue Per User:** ~$70/month

### Feature Usage (Pro vs Elite)

| Feature | Pro Users | Elite Users |
|---------|-----------|-------------|
| Quick Tasks | 90% | 95% |
| Proxies | 80% | 95% |
| Restock Predictions | 70% | 90% |
| Auto-Tasks | 0% | 85% |
| API Access | 0% | 40% |

**Elite Upgrade Driver:** Auto-tasks (saves hours of manual work)

---

## 🚀 Implementation Priority

### Week 1: Core Gating
1. ✅ License validation (done)
2. ✅ Usage tracking (done)
3. Add tier checks to all routes
4. Add usage enforcement
5. Show tier badges in UI

### Week 2: Premium Features
1. Implement auto-task creation
2. Add bulk operations
3. Build API access system
4. Add custom webhooks

### Week 3: Polish
1. Upgrade prompts & CTAs
2. Usage dashboards
3. Tier comparison in Settings
4. Onboarding for each tier

---

## 💰 Pricing Psychology

**Why $79 for Pro?**
- Just below $80 psychological barrier
- 2.7x Starter (feels like upgrade)
- Competitors charge $300+ (huge value)
- Sweet spot for serious users

**Why $199 for Elite?**
- Just below $200 barrier
- 2.5x Pro (justified by automation)
- Auto-tasks alone save 10+ hours/month
- API access = $99 value alone

**Upsell Strategy:**
- Show "You could have made $X more with Pro" in Starter
- Show "Auto-tasks would have caught 5 drops" in Pro
- Highlight time saved, not just features

---

Ready to implement the tier gating and premium features?
