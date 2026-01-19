# 👻 Phantom Bot - Advanced Sneaker Automation Suite

> **The most sophisticated all-in-one sneaker bot with built-in market intelligence**

## 🚀 Features

### Core Bot Engine
- **Multi-threaded task execution** with adaptive concurrency
- **Smart proxy rotation** with health monitoring and automatic failover
- **Profile management** with card encryption and secure storage
- **Session persistence** for warm browser sessions

### 🧠 Novel Anti-Bot Evasion
- **Fingerprint randomization** - Canvas, WebGL, AudioContext spoofing
- **TLS fingerprint rotation** - JA3/JA4 hash manipulation
- **Request pattern humanization** - ML-based timing patterns
- **Adaptive delays** - Learn optimal timing per site
- **Residential proxy intelligence** - Auto-detect and avoid flagged IPs

### 📊 Market Intelligence (Replaces Cook Groups)
- **Automated restock prediction** - ML model trained on historical data
- **Real-time price tracking** - StockX, GOAT, eBay monitoring
- **Profit calculator** - Instant ROI analysis before purchase
- **Release calendar sync** - Nike SNKRS, Adidas Confirmed, Shopify drops
- **Keyword research** - Auto-generate optimal monitor keywords
- **Trend analysis** - Identify emerging hyped products

### 🛒 Checkout Modules
- **Shopify** - Normal, Fast, Preload, Safe modes
- **Nike SNKRS** - Account generation, entry automation
- **Footsites** - Foot Locker, Champs, Eastbay, Finish Line
- **Adidas** - Splash bypass, queue manipulation
- **YeezySupply** - Specialized checkout flow

### 🔐 Captcha Integration
- **2Captcha** / **Anti-Captcha** / **CapMonster**
- **Built-in AI solver** using vision models
- **Harvester management** with cookie persistence
- **One-click solving** for manual intervention

### 📱 Notifications & Analytics
- **Discord webhooks** - Success, failure, restock alerts
- **Desktop notifications** - Native OS alerts
- **Analytics dashboard** - Success rates, spending, profits
- **Export reports** - CSV/PDF for accounting

## 📁 Project Structure

```
phantom-bot/
├── phantom/
│   ├── core/                 # Core bot engine
│   │   ├── engine.py         # Main task orchestrator
│   │   ├── task.py           # Task models and execution
│   │   ├── proxy.py          # Proxy management
│   │   └── profile.py        # Profile/payment handling
│   ├── monitors/             # Site monitors
│   │   ├── base.py           # Base monitor class
│   │   ├── shopify.py        # Shopify monitor
│   │   └── keywords.py       # Keyword matching engine
│   ├── checkout/             # Checkout modules
│   │   ├── shopify.py        # Shopify checkout
│   │   ├── nike.py           # Nike SNKRS
│   │   └── footsites.py      # Footsites
│   ├── evasion/              # Anti-bot systems
│   │   ├── fingerprint.py    # Browser fingerprinting
│   │   ├── tls.py            # TLS fingerprint
│   │   └── humanizer.py      # Human behavior simulation
│   ├── intelligence/         # Market intelligence
│   │   ├── restock.py        # Restock prediction
│   │   ├── pricing.py        # Price tracking
│   │   ├── calendar.py       # Release calendar
│   │   └── research.py       # Keyword/product research
│   ├── captcha/              # Captcha solving
│   │   ├── solver.py         # Solver integrations
│   │   └── harvester.py      # Cookie harvesting
│   ├── notifications/        # Alerts & webhooks
│   │   ├── discord.py        # Discord integration
│   │   └── desktop.py        # Desktop notifications
│   ├── api/                  # REST API (FastAPI)
│   │   ├── main.py           # API server
│   │   └── routes/           # API endpoints
│   └── utils/                # Utilities
│       ├── crypto.py         # Encryption
│       ├── database.py       # SQLite/PostgreSQL
│       └── config.py         # Configuration
├── web/                      # React frontend
│   ├── src/
│   └── package.json
├── data/                     # Data storage
│   ├── profiles.db           # Encrypted profiles
│   ├── proxies.json          # Proxy lists
│   └── ml_models/            # Trained ML models
├── config.yaml               # Main configuration
├── requirements.txt          # Python dependencies
└── run.py                    # Entry point
```

## 🛠 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/phantom-bot
cd phantom-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m phantom.utils.database init

# Start the bot
python run.py
```

## ⚡ Quick Start

### Start Backend API Server
```bash
# From project root
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
python main.py --server --port 8081
```

### Start Frontend Dev Server
```bash
# In a separate terminal
cd frontend
npm install  # first time only
npm run dev
```

The frontend will be available at `http://localhost:5173` (or next available port).
The backend API runs at `http://localhost:8081`.

### Alternative: CLI Mode
```bash
python main.py --cli
```

### Run Specific Task Group
```bash
python main.py --group "Nike Dunks"
```

## 🔑 Configuration

Edit `config.yaml`:

```yaml
license_key: "YOUR-LICENSE-KEY"

captcha:
  provider: "2captcha"  # or capmonster, anticaptcha
  api_key: "YOUR_API_KEY"

notifications:
  discord_webhook: "https://discord.com/api/webhooks/..."
  desktop_alerts: true

intelligence:
  stockx_api: true
  goat_api: true
  auto_research: true

proxy:
  test_on_start: true
  rotation_strategy: "round_robin"  # or random, sticky
  health_check_interval: 300

performance:
  max_concurrent_tasks: 50
  max_concurrent_monitors: 20
```

## 📜 License

Proprietary - All rights reserved.

---

Built with ❤️ for the sneaker community
