# Phantom Bot - Complete Setup Guide

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- 4GB+ RAM
- Residential proxies (recommended)
- Captcha service API key (2Captcha or CapMonster)

### Installation

```bash
# 1. Clone and navigate to project
cd bot_webhook

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers (for advanced features)
playwright install chromium

# 5. Initialize database
python -c "from phantom.utils.database import init_db; import asyncio; asyncio.run(init_db())"

# 6. Install frontend dependencies
cd frontend
npm install
cd ..
```

### Configuration

1. **Copy and edit config file**:
```bash
cp config.yaml config.local.yaml
```

2. **Edit `config.local.yaml`** with your settings:

```yaml
# Captcha (REQUIRED)
captcha:
  primary_provider: "2captcha"
  providers:
    2captcha:
      api_key: "YOUR_2CAPTCHA_KEY_HERE"
    capmonster:
      api_key: "YOUR_CAPMONSTER_KEY_HERE"  # Optional fallback

# Discord Notifications (RECOMMENDED)
notifications:
  discord:
    enabled: true
    webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE"
    success_webhook: ""  # Optional: separate webhook for successes
    failure_webhook: ""  # Optional: separate webhook for failures

# Proxy (HIGHLY RECOMMENDED)
# Add your proxies later via the web UI
```

### First Run

**Option 1: Web UI (Recommended)**

```bash
# Terminal 1 - Start backend
source venv/bin/activate
python main.py --mode server --port 8081

# Terminal 2 - Start frontend
cd frontend
npm run dev
```

Open browser to `http://localhost:5173`

**Option 2: CLI Mode**

```bash
source venv/bin/activate
python main.py --cli
```

---

## Detailed Setup

### 1. Adding Profiles

Profiles contain your shipping/billing information and payment cards.

**Via Web UI:**
1. Navigate to "Profiles" tab
2. Click "Add Profile"
3. Fill in all fields
4. Save

**Via CLI:**
```python
from phantom.core.profile import ProfileManager, Profile, Address, PaymentCard

pm = ProfileManager()

profile = Profile(
    name="Main Profile",
    email="your@email.com",
    phone="5551234567",
    shipping=Address(
        first_name="John",
        last_name="Doe",
        address1="123 Main St",
        address2="Apt 4",
        city="New York",
        state="NY",
        zip_code="10001",
        country="United States"
    ),
    card=PaymentCard(
        holder_name="John Doe",
        number="4111111111111111",
        expiry_month="12",
        expiry_year="2025",
        cvv="123"
    )
)

pm.add_profile(profile)
```

### 2. Adding Proxies

**Via Web UI:**
1. Navigate to "Proxies" tab
2. Click "Add Proxy Group"
3. Name your group (e.g., "Residential ISP")
4. Paste proxies (one per line) in format:
   - `http://user:pass@ip:port`
   - `http://ip:port`
   - `user:pass@ip:port`
5. Click "Test Proxies" to validate
6. Save

**Recommended Proxy Providers:**
- Residential: Smartproxy, Bright Data, Oxylabs
- ISP: Soax, NetNut
- Datacenter: MyPrivateProxy (for monitors only)

**Proxy Tips:**
- Use residential for checkout (higher success rate)
- Use datacenter for monitoring (cheaper)
- Test proxies before important drops
- Rotate proxies every 1-2 weeks

### 3. Setting Up Monitors

Monitors watch stores for new products and restocks.

**Shopify Stores:**

```bash
# Via Web UI
1. Go to "Monitors" tab
2. Click "Setup Shopify"
3. Select "Use Default Stores" or add custom stores
4. Set target sizes (e.g., 10, 10.5, 11)
5. Click "Start Monitoring"
```

**Default Shopify Stores Included:**
- DTLR, Shoe Palace, Jimmy Jazz, Hibbett
- Social Status, Undefeated, Concepts, Kith
- Notre, Bodega, and more

**Footsites:**

```bash
# Via Web UI
1. Go to "Monitors" tab
2. Click "Setup Footsites"
3. Select sites (Footlocker, Champs, Eastbay)
4. Add keywords (e.g., "Jordan 1", "Dunk Low")
5. Set target sizes
6. Click "Start Monitoring"
```

### 4. Creating Tasks

Tasks are checkout attempts for specific products.

**Quick Task (Recommended):**
1. Wait for monitor to detect a product
2. Click "Create Task" on the product card
3. Select profile and proxy group
4. Click "Start"

**Manual Task:**
1. Go to "Tasks" tab
2. Click "Create Task"
3. Fill in:
   - Site: Select store
   - Product URL or keywords
   - Sizes (in priority order)
   - Mode: Normal (default), Fast, or Safe
   - Profile and proxy group
4. Click "Create"
5. Click "Start" to begin

**Task Modes:**
- **Normal**: Standard checkout flow (recommended)
- **Fast**: Skip delays, aggressive timing (for hyped drops)
- **Safe**: Extra delays, more human-like (if getting banned)

### 5. Running a Drop

**Pre-Drop Checklist:**
- [ ] Profiles created and tested
- [ ] Proxies added and tested
- [ ] Monitors running for target stores
- [ ] Discord webhook configured
- [ ] Captcha balance checked
- [ ] Tasks created or auto-task enabled

**During Drop:**
1. Monitor the dashboard for product detection
2. Tasks will auto-start if configured
3. Watch for Discord notifications
4. Manual intervention if needed (checkout links sent on decline)

**Post-Drop:**
1. Check "Analytics" tab for success rate
2. Review which profiles/proxies performed best
3. Export data for accounting

---

## Advanced Configuration

### Auto-Task Creation

Automatically create and start tasks when monitors detect profitable products.

```yaml
# In config.yaml
intelligence:
  enabled: true
  research:
    profit_threshold: 20  # Minimum $20 profit
```

```python
# Via API or CLI
from phantom.monitors.manager import MonitorManager

manager = MonitorManager()
manager.enable_auto_tasks(
    enabled=True,
    min_confidence=0.7,  # 70% match confidence
    min_priority="medium"  # medium or high priority only
)
```

### Market Intelligence

Get real-time profit analysis before copping.

```python
from phantom.intelligence.pricing import PriceTracker

tracker = PriceTracker()

# Analyze a product
analysis = await tracker.analyze_profit(
    sku="DZ5485-612",  # Jordan 1 High
    retail_price=180.00
)

print(f"Resale: ${analysis.best_resale}")
print(f"Profit: ${analysis.estimated_profit}")
print(f"Margin: {analysis.profit_margin}%")
print(f"Recommendation: {tracker.get_recommendation(analysis)}")
```

### Webhook Customization

**Multiple Webhooks:**
```yaml
notifications:
  discord:
    webhook_url: "https://..."  # General notifications
    success_webhook: "https://..."  # Successes only
    failure_webhook: "https://..."  # Failures/declines
    restock_webhook: "https://..."  # Restock alerts
    mention_role: "123456789"  # Role ID to @mention
```

**Custom Embeds:**
Edit `phantom/notifications/discord.py` to customize embed colors, fields, and formatting.

### Performance Tuning

```yaml
performance:
  max_concurrent_tasks: 50  # Increase for more power
  max_concurrent_monitors: 25
  request_timeout: 30
  checkout_timeout: 60

delays:
  monitor:
    aggressive: 1500  # Faster monitoring (higher ban risk)
    default: 3000
    safe: 5000  # Slower but safer
```

**Recommendations:**
- Start with default settings
- Increase concurrency if you have good proxies
- Use aggressive delays only for hyped drops
- Monitor proxy ban rates and adjust

---

## Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database errors
```bash
# Reset database (WARNING: deletes all data)
rm data/phantom.db
python -c "from phantom.utils.database import init_db; import asyncio; asyncio.run(init_db())"
```

### Proxies not working
1. Test proxies manually: `curl -x http://user:pass@ip:port https://google.com`
2. Check format (must include http://)
3. Verify credentials with provider
4. Try different proxy group

### Captcha errors
1. Check API key is correct
2. Verify balance: https://2captcha.com/enterpage
3. Try fallback provider (CapMonster)
4. Check site isn't using invisible captcha

### Low success rate
1. Use residential proxies (not datacenter)
2. Switch to "Safe" mode
3. Reduce concurrent tasks
4. Check if site has new anti-bot measures
5. Update fingerprints (rotate more frequently)

### Monitor not detecting products
1. Check store URL is correct
2. Verify keywords match product titles
3. Increase monitor delay (reduce rate limiting)
4. Check if store changed their API

---

## Best Practices

### Proxy Management
- **Ratio**: 1 proxy per 3-5 tasks
- **Rotation**: Replace every 1-2 weeks
- **Testing**: Test before every major drop
- **Quality**: Residential > ISP > Datacenter

### Profile Strategy
- Create 3-5 profiles with different cards
- Use real addresses (package forwarding if needed)
- Vary email addresses (gmail+tag@gmail.com)
- Test profiles on low-value items first

### Task Organization
- Use task groups for different releases
- Name tasks clearly (e.g., "Jordan 1 High - Size 10")
- Set realistic size ranges (3-5 sizes max)
- Don't run 100+ tasks on one proxy group

### Drop Strategy
1. **Research** (1 week before):
   - Check profit potential
   - Identify which stores will stock
   - Prepare keywords/URLs

2. **Setup** (1 day before):
   - Create tasks
   - Test proxies
   - Verify captcha balance
   - Enable monitors

3. **Execution** (drop time):
   - Start tasks 30s before drop
   - Monitor Discord for updates
   - Be ready for manual checkout if needed

4. **Post-Drop**:
   - Analyze success rate
   - Update strategy for next drop
   - Rotate proxies if banned

---

## FAQ

**Q: How many tasks should I run?**
A: Start with 10-20 tasks. Scale up as you get more proxies and experience.

**Q: What's a good success rate?**
A: 10-20% on hyped drops is excellent. 5-10% is average. <5% needs optimization.

**Q: Do I need residential proxies?**
A: Highly recommended. Datacenter proxies have <2% success rate on most sites.

**Q: How much does it cost to run?**
A: Proxies: $50-200/month, Captcha: $10-50/month, depending on volume.

**Q: Can I run this on a VPS?**
A: Yes, but you'll need to use CLI mode or set up remote access to the web UI.

**Q: Is this legal?**
A: Using bots violates most sites' Terms of Service but is not illegal. Use at your own risk.

**Q: Will I get banned?**
A: Possible. Use good proxies, vary your patterns, and don't be too aggressive.

**Q: Can I resell items bought with this?**
A: Yes, but be aware of tax implications and platform fees (StockX, GOAT, eBay).

---

## Getting Help

1. **Check logs**: `tail -f phantom.log`
2. **Discord**: Join our community (link in README)
3. **GitHub Issues**: Report bugs and request features
4. **Documentation**: Full API docs at `/docs` when server is running

---

## Next Steps

1. ✅ Complete setup
2. ✅ Add 1-2 profiles
3. ✅ Add proxy group (10+ proxies)
4. ✅ Start Shopify monitors
5. ✅ Create test task on low-value item
6. ✅ Join Discord for drop alerts
7. ✅ Practice on non-hyped releases
8. ✅ Scale up for major drops

**Good luck copping! 👟**
