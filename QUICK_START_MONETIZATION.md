# 🚀 Quick Start: Monetization Setup

## What's Been Implemented

✅ **License Key System**
- JWT-based validation
- Tier-based limits (Starter, Pro, Elite)
- Usage tracking (tasks, monitors, daily limits)

✅ **Authentication Flow**
- Login screen with license activation
- Auto-validation on app load
- Secure token storage

✅ **Stripe Integration**
- Checkout session creation
- Webhook handling for subscriptions
- Automatic license generation on payment

✅ **Pricing Page**
- 3-tier pricing ($29, $79, $199)
- Feature comparison
- Direct Stripe checkout

---

## 🎯 To Go Live (30 Minutes)

### Step 1: Create Stripe Account (5 min)

1. Go to https://dashboard.stripe.com/register
2. Complete verification
3. Get your API keys from https://dashboard.stripe.com/apikeys

### Step 2: Create Stripe Products (10 min)

In Stripe Dashboard → Products:

1. **Create "Phantom Starter"**
   - Price: $29/month recurring
   - Copy the Price ID (starts with `price_...`)

2. **Create "Phantom Pro"**
   - Price: $79/month recurring
   - Copy the Price ID

3. **Create "Phantom Elite"**
   - Price: $199/month recurring
   - Copy the Price ID

### Step 3: Configure Environment Variables (5 min)

Create `/Users/davidnichols/bot_webhook/.env`:

```bash
LICENSE_SECRET=$(openssl rand -hex 32)
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
STRIPE_PRICE_STARTER=price_YOUR_STARTER_ID
STRIPE_PRICE_PRO=price_YOUR_PRO_ID
STRIPE_PRICE_ELITE=price_YOUR_ELITE_ID
```

### Step 4: Set Up Stripe Webhook (5 min)

1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://phantom-bot-api.fly.dev/api/auth/webhook/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
4. Copy webhook secret to `.env`

### Step 5: Deploy Updated Backend (5 min)

```bash
cd /Users/davidnichols/bot_webhook
flyctl deploy --remote-only
```

### Step 6: Test the Flow

1. Open `http://localhost:5173`
2. You'll see the login screen
3. Generate a test license:
   ```bash
   curl -X POST http://localhost:8081/api/auth/generate \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","tier":"pro","duration_days":30}'
   ```
4. Copy the license key and activate

---

## 💰 Revenue Tracking

### Monitor Your Growth

**Stripe Dashboard:**
- Real-time revenue
- Subscription metrics
- Churn rate
- MRR growth

**Your App:**
- Active users (count license validations)
- Usage per tier
- Popular features
- Conversion funnel

---

## 🎨 Customization Options

### Adjust Pricing

Edit `frontend/src/components/Pricing.tsx`:
- Change prices
- Add/remove features
- Modify tier names

### Adjust Limits

Edit `phantom/auth/license.py` → `TierLimits.LIMITS`:
```python
UserTier.PRO: {
    "max_tasks": 100,  # Increase limit
    "max_monitors": 20,
    # ...
}
```

### Add Free Trial

In `phantom/api/auth_routes.py`:
```python
# Generate 7-day trial license
license_key = license_validator.generate_license(
    user_id=user_id,
    email=email,
    tier=UserTier.PRO,  # Give Pro features
    duration_days=7  # 7-day trial
)
```

---

## 📊 Expected Results

### Month 1 (Conservative)
- 50 users × $40 avg = **$2,000 MRR**
- Costs: $50/month
- **Profit: $1,950**

### Month 3 (Realistic)
- 300 users × $45 avg = **$13,500 MRR**
- Costs: $200/month
- **Profit: $13,300**

### Month 6 (Aggressive)
- 1,000 users × $50 avg = **$50,000 MRR**
- Costs: $500/month
- **Profit: $49,500**

---

## 🔥 Marketing Launch Checklist

### Week 1: Soft Launch
- [ ] Post in r/sneakerbots
- [ ] Tweet with demo video
- [ ] Create Discord server
- [ ] Offer 50% launch discount

### Week 2: Content Push
- [ ] YouTube: "I made $500 in 1 week botting"
- [ ] Blog: Setup guides
- [ ] Twitter: Daily success screenshots
- [ ] Reddit: Answer questions, provide value

### Week 3: Partnerships
- [ ] Reach out to proxy providers (affiliate deals)
- [ ] Contact cook group owners (white-label)
- [ ] Influencer partnerships (commission-based)

---

## 🛡️ Security Best Practices

1. **Never commit `.env` file** (add to `.gitignore`)
2. **Rotate LICENSE_SECRET** monthly
3. **Monitor for license sharing** (track device IDs)
4. **Rate limit API endpoints** (prevent abuse)
5. **Use HTTPS only** in production

---

## 🎯 Next Steps

1. **Set up Stripe** (30 min)
2. **Deploy with auth** (10 min)
3. **Test end-to-end** (20 min)
4. **Launch marketing** (ongoing)

**You're ready to start making money!**
