# 👻 Phantom Bot - Advanced Sneaker Automation Suite

> **The most sophisticated all-in-one sneaker bot with built-in market intelligence**

## 🚀 Features

### Core Bot Engine
- **Multi-threaded task execution** with adaptive concurrency (50+ concurrent tasks)
- **Smart proxy rotation** with health monitoring and automatic failover
- **Profile management** with encrypted card storage (AES-256)
- **Session persistence** for warm browser sessions

### 🧠 Anti-Bot Evasion
- **Fingerprint randomization** - Canvas, WebGL, AudioContext spoofing
- **TLS fingerprint rotation** - JA3/JA4 hash manipulation
- **Request pattern humanization** - ML-based timing patterns
- **Adaptive delays** - Learn optimal timing per site

### 📊 Market Intelligence
- **Dynamic data sources** - Live pricing from StockX & GOAT
- **Auto-learned products** - Monitors discover and catalog new products
- **Intelligent keyword generation** - 20+ brand expansions with model/colorway detection
- **Profit calculator** - Filters products by minimum profit threshold
- **Release calendar sync** - Nike SNKRS, Adidas Confirmed, Shopify drops

### 🛒 Checkout Modules
- **Shopify** - Normal, Fast, Preload, Safe modes
- **Footsites** - Foot Locker, Champs, Eastbay, Finish Line
- **Nike SNKRS** - Account generation, entry automation
- **Adidas** - Splash bypass, queue manipulation

### 🔐 Captcha Integration
- **2Captcha** / **Anti-Captcha** / **CapMonster**
- **Harvester management** with cookie persistence

### 📱 Notifications & Analytics
- **Discord webhooks** - Success, failure, restock alerts
- **Desktop notifications** - Native OS alerts
- **Analytics dashboard** - Success rates, spending, profits

---

## 📁 Project Structure

```
phantom-bot/
├── main.py                   # Entry point (CLI + server modes)
├── config.yaml               # Main configuration
├── requirements.txt          # Python dependencies
│
├── phantom/                  # Core Python modules
│   ├── core/                 # Bot engine
│   │   ├── engine.py         # Main orchestrator (singleton)
│   │   ├── task.py           # Task models and execution
│   │   ├── proxy.py          # Proxy manager with health checks
│   │   └── profile.py        # Profile/payment handling
│   │
│   ├── monitors/             # Site monitoring
│   │   ├── base.py           # BaseMonitor abstract class
│   │   ├── shopify_monitor.py# Shopify store monitor
│   │   ├── footsites.py      # Footsite monitor
│   │   ├── keywords.py       # Keyword matching engine
│   │   ├── products.py       # Curated product database
│   │   ├── data_sources.py   # 🆕 StockX/GOAT/learned products
│   │   ├── manager.py        # Multi-monitor orchestrator
│   │   └── sites.py          # Store definitions
│   │
│   ├── checkout/             # Checkout modules
│   │   └── shopify.py        # Shopify checkout flow
│   │
│   ├── evasion/              # Anti-bot systems
│   │   ├── fingerprint.py    # Browser fingerprinting
│   │   ├── tls.py            # TLS fingerprint rotation
│   │   └── humanizer.py      # Human behavior simulation
│   │
│   ├── intelligence/         # Market intelligence
│   │   ├── pricing.py        # Price tracking
│   │   ├── calendar.py       # Release calendar
│   │   └── research.py       # Product research
│   │
│   ├── captcha/              # Captcha solving
│   │   ├── solver.py         # 2Captcha/CapMonster integration
│   │   └── harvester.py      # Cookie harvesting
│   │
│   ├── notifications/        # Alerts & webhooks
│   │   ├── discord.py        # Discord integration
│   │   └── desktop.py        # Desktop notifications
│   │
│   ├── api/                  # REST API (FastAPI)
│   │   └── routes.py         # All API endpoints + WebSocket
│   │
│   └── utils/                # Utilities
│       ├── config.py         # Configuration loader
│       ├── crypto.py         # AES encryption
│       └── database.py       # SQLite/PostgreSQL
│
├── frontend/                 # React + TypeScript + Vite
│   └── src/
│       ├── App.tsx           # Main app with routing
│       ├── api/              # API client
│       ├── store/            # Redux store
│       └── components/       # UI components
│           ├── Dashboard.tsx # Main dashboard
│           ├── Tasks.tsx     # Task management
│           ├── Monitors.tsx  # Monitor controls
│           ├── Profiles.tsx  # Profile management
│           ├── Proxies.tsx   # Proxy management
│           ├── Intelligence.tsx # Market intel
│           ├── Analytics.tsx # Analytics dashboard
│           └── Settings.tsx  # Bot settings
│
└── data/                     # Data storage
```

---

## 🛠 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/phantom-bot
cd phantom-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start the bot
python main.py
```

---

## ⚡ Quick Start

### Start Backend API Server
```bash
source venv/bin/activate
python main.py --mode server --port 8080
```

### Start Frontend Dev Server
```bash
cd frontend
npm install  # first time only
npm run dev
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080

### CLI Mode
```bash
python main.py --mode cli
```

---

## 🆕 Dynamic Data Sources

The bot now automatically fetches live pricing and trending products:

```python
from phantom.monitors import create_data_source, product_db

# Create data source with StockX + GOAT
source = create_data_source()

# Fetch trending products and add to database
await product_db.refresh_from_source(source, limit=50, min_profit=30.0)

# Update prices for existing products
await product_db.update_prices_from_source(source)
```

### Data Source Architecture

| Source | Data | Rate Limit |
|--------|------|------------|
| **StockX** | Trending, pricing, style codes | 3s between requests |
| **GOAT** | Pricing, search | 3s between requests |
| **MonitorLearned** | Products discovered by monitors | N/A |

---

## 🔑 Keyword Intelligence

Enhanced keyword generation with 20+ brand expansions:

```python
from phantom.monitors import KeywordMatcher

# Auto-generate optimal keywords
keywords = KeywordMatcher.generate_keywords_for_product(
    "Air Jordan 1 Retro High OG Chicago",
    style_code="DZ5485-612"
)
# Output: SKU:DZ5485-612, +jordan, +jordan 1, +aj1, +chicago, -gs, -toddler...
```

### Supported Brands
Jordan, Nike, Adidas, Yeezy, New Balance, ASICS, Converse, Vans, Puma, Reebok, Saucony, Off-White, Travis Scott, Fragment, Union, Sacai, Fear of God

---

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
captcha:
  provider: "2captcha"
  api_key: "YOUR_API_KEY"

notifications:
  discord_webhook: "https://discord.com/api/webhooks/..."
  desktop_alerts: true

intelligence:
  stockx_api: true
  goat_api: true

performance:
  max_concurrent_tasks: 50
  max_concurrent_monitors: 20

proxy:
  test_on_start: true
  rotation_strategy: "round_robin"  # or random, sticky
```

---

## 📜 License

Proprietary - All rights reserved.

---

Built with ❤️ for the sneaker community
