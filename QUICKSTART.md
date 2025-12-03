# 🚀 Quick Start Guide - Outbound Omega v2

Get up and running in 5 minutes!

---

## Step 1: Install Dependencies

```bash
cd Outbound-Omega
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Minimum required configuration:
ANTHROPIC_API_KEY=your-anthropic-key-here
ZOHO_USERNAME=your-email@domain.com
ZOHO_PASSWORD=your-zoho-password

# Compliance (update with your info):
PHYSICAL_ADDRESS=Your Company Address Here
COMPANY_NAME=Your Company Name
```

---

## Step 3: Start the Server

```bash
python run.py
```

Open: **http://localhost:5001**

---

## Step 4: Import Some Leads

Use the API to ingest leads from your scraper:

```bash
curl -X POST http://localhost:5001/api/scraper/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "leads": [
      {
        "company_name": "Test Company",
        "website": "https://example.com",
        "contact_name": "John Doe",
        "contact_email": "john@example.com",
        "phone": "555-1234",
        "location": "Atlanta, GA",
        "market_type": "Construction",
        "source": "test"
      }
    ],
    "search_criteria": {
      "business_type": "construction",
      "location": "Atlanta"
    }
  }'
```

---

## Step 5: Create an Email Sequence

```bash
curl -X POST http://localhost:5001/api/sequences \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Basic Outreach",
    "description": "3-step outreach sequence",
    "default_from_address": "outreach@yourcompany.com",
    "steps": [
      {
        "step_order": 1,
        "delay_days": 0,
        "template_context": {
          "tone": "professional",
          "goal": "introduction"
        }
      },
      {
        "step_order": 2,
        "delay_days": 3,
        "template_context": {
          "tone": "friendly",
          "goal": "follow-up"
        }
      },
      {
        "step_order": 3,
        "delay_days": 7,
        "template_context": {
          "tone": "casual",
          "goal": "final-check-in"
        }
      }
    ]
  }'
```

---

## Step 6: Add Leads to Sequence

```bash
curl -X POST http://localhost:5001/api/outbound/add-to-sequence \
  -H "Content-Type: application/json" \
  -d '{
    "lead_ids": [1, 2, 3],
    "sequence_id": 1
  }'
```

---

## Step 7: Run Outbound (Dry Run)

Test without actually sending:

```bash
curl -X POST http://localhost:5001/api/outbound/run \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "outreach@yourcompany.com",
    "dry_run": true
  }'
```

Or use the UI:
1. Go to **Outbound** tab
2. Check "Dry Run"
3. Click "Run Outbound Cycle"

---

## Step 8: Send Real Emails

When ready:

```bash
curl -X POST http://localhost:5001/api/outbound/run \
  -H "Content-Type: application/json" \
  -d '{
    "from_address": "outreach@yourcompany.com",
    "dry_run": false
  }'
```

---

## 🎉 You're All Set!

### What to Do Next:

- **View Dashboard**: See stats and recent activities
- **Check Leads**: Filter by status, see who was contacted
- **Create Campaigns**: Organize leads by niche/market
- **Monitor Unsubscribes**: Check `/unsubscribe` logs
- **Customize UI**: Edit `static/styles.css` for your brand

### Need Help?

- Read the full docs: `OUTBOUND_README.md`
- Check API endpoints in the README
- Review troubleshooting section

---

## 🔥 Pro Tips

1. **Always test with dry_run first**
2. **Start with small sequences** (2-3 steps)
3. **Monitor your send limits** (default: 50/day)
4. **Use multiple from addresses** to distribute sending
5. **Check lead scores** to prioritize high-value leads
6. **Track activities** to see what's working

---

## 🐛 Common Issues

**"No API key"**: Make sure `.env` has `ANTHROPIC_API_KEY` set

**"SMTP error"**: Check Zoho credentials, use app password if 2FA enabled

**"No leads found"**: Run `/api/scraper/ingest` first to add leads

**"Daily limit reached"**: Increase `MAX_EMAILS_PER_DAY` in `.env`

---

**Happy Outbounding! 🚀**
