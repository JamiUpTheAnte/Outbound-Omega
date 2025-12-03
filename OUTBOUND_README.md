# Outbound Omega v2 🌌

A complete **local-first lead engine** that integrates lead scraping, CRM, AI-powered email generation, and outbound automation—all with a futuristic galaxy-themed UI.

---

## 🚀 Overview

**Outbound Omega v2** combines three core systems:

1. **System 1: Lead Scraper** (existing Python + Flask + Selenium scraper)
2. **System 2: Custom CRM** (SQLAlchemy-backed database for companies, contacts, leads)
3. **System 3: Outbound Machine** (AI email generation via Anthropic + Zoho email sending + CAN-SPAM compliance)

---

## ✨ Features

### CRM Features
- **Company Management**: Track companies with website, location, market type
- **Contact Management**: Store contact details with opt-out tracking
- **Lead Tracking**: Monitor lead status, scoring, and outreach history
- **Campaign Management**: Organize leads by campaigns and niches
- **Activity Logging**: Track all interactions (emails sent, replies, form completions)

### Outbound Machine
- **Email Sequences**: Multi-step drip campaigns with configurable delays
- **AI Email Generation**: Uses Anthropic Claude to generate personalized emails
- **Smart Scheduling**: Automatically determines who needs emails and when
- **Send Limits**: Configurable daily sending limits per address
- **CAN-SPAM Compliance**: Automatic footers, unsubscribe links, opt-out tracking
- **Multiple From Addresses**: Rotate between sending addresses

### UI/UX
- **Galaxy Theme**: Futuristic blues, purples, and animated star background
- **Dashboard**: Real-time stats and activity feed
- **Leads View**: Filterable table with company, contact, and status info
- **Campaigns & Sequences**: Manage campaigns and email sequences
- **Outbound Control**: Trigger outbound cycles with dry-run mode
- **Settings**: Configure sending limits, addresses, and compliance info

---

## 📋 Prerequisites

- Python 3.9+
- SQLite (included) or PostgreSQL (for production)
- Zoho email account (for sending)
- Anthropic API key (for AI email generation)

---

## 🛠️ Installation

### 1. Clone the Repository

```bash
cd Outbound-Omega
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Flask
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database (SQLite for local dev)
DATABASE_URL=sqlite:///outbound_omega.db

# Anthropic AI
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Zoho Email
ZOHO_SMTP_HOST=smtp.zoho.com
ZOHO_SMTP_PORT=587
ZOHO_USERNAME=your-email@yourdomain.com
ZOHO_PASSWORD=your-zoho-password

# Sending Configuration
MAX_EMAILS_PER_DAY=50

# CAN-SPAM Compliance
PHYSICAL_ADDRESS=123 Business St, Suite 100, Atlanta, GA 30303
UNSUBSCRIBE_BASE_URL=http://localhost:5001/unsubscribe
COMPANY_NAME=Your Company Name

# From Addresses (comma-separated)
FROM_ADDRESSES=outreach@yourcompany.com,hello@yourcompany.com
```

### 5. Initialize Database

The database will be created automatically when you first run the app. Tables are created via SQLAlchemy on startup.

---

## 🏃 Running the Application

### Start the Flask Server

```bash
python app_main.py
```

The app will be available at: **http://localhost:5001**

### Access the UI

Open your browser and navigate to:

```
http://localhost:5001
```

You should see the Outbound Omega v2 dashboard with the galaxy theme.

---

## 📊 Using the System

### 1. Ingest Leads from Scraper

The existing scraper (in `scraper.py` and `app.py`) can run separately. To integrate scraper results:

**Option A: Use the API endpoint**

```bash
POST http://localhost:5001/api/scraper/ingest
Content-Type: application/json

{
  "leads": [
    {
      "company_name": "Example Builders LLC",
      "website": "https://examplebuilders.com",
      "contact_name": "John Doe",
      "contact_email": "john@examplebuilders.com",
      "phone": "555-123-4567",
      "location": "Atlanta, GA",
      "market_type": "General Contractor",
      "tags": ["commercial", "steel_buildings"],
      "source": "google_search"
    }
  ],
  "search_criteria": {
    "business_type": "construction company",
    "location": "Atlanta",
    "market_type": "General Contractor"
  }
}
```

**Option B: Run scraper separately and import JSON**

If your scraper produces a JSON file, you can POST it to `/api/scraper/ingest`.

### 2. Create a Campaign

1. Go to **Campaigns** in the sidebar
2. Click **+ New Campaign**
3. Fill in:
   - **Name**: e.g., "Atlanta Construction Outreach"
   - **Description**: What this campaign is about
   - **Niche**: e.g., "General Contractors"
   - **Market**: e.g., "Southeast US"
   - **Offer**: Brief description of your offer
4. Save

### 3. Create an Email Sequence

1. Go to **Sequences** in the sidebar
2. Click **+ New Sequence**
3. Configure steps:
   - **Step 1**: Initial outreach (delay: 0 days)
   - **Step 2**: Follow-up 1 (delay: 3 days)
   - **Step 3**: Follow-up 2 (delay: 7 days)
   - etc.
4. Set **default_from_address** (optional)
5. Save

### 4. Add Leads to a Sequence

```bash
POST http://localhost:5001/api/outbound/add-to-sequence
Content-Type: application/json

{
  "lead_ids": [1, 2, 3],
  "sequence_id": 1
}
```

Or use the UI (future feature).

### 5. Run an Outbound Cycle

1. Go to **Outbound** in the sidebar
2. Select **From Address**
3. Check **Dry Run** to test without sending
4. Click **Run Outbound Cycle**

The system will:
- Find leads due for emails
- Generate personalized email content using Anthropic AI
- Send emails via Zoho SMTP
- Update CRM (times contacted, last contacted, status)
- Log activities

### 6. View Dashboard & Leads

- **Dashboard**: See total leads, emails sent today, active campaigns
- **Leads**: Filter by status, market type; view lead details, email history, activities

---

## 🔒 CAN-SPAM Compliance

The system enforces CAN-SPAM compliance:

1. **Physical Address**: Every email includes your configured physical address
2. **Unsubscribe Link**: Every email has a working unsubscribe link
3. **Opt-Out Tracking**: Once a contact opts out, they never receive emails again
4. **Accurate From/Reply-To**: Emails sent from configured addresses
5. **No Deceptive Content**: AI is instructed not to make false claims

### Unsubscribe Flow

1. Contact clicks unsubscribe link: `http://localhost:5001/unsubscribe?token=<token>`
2. System marks contact as `opt_out = True`
3. All active sequences for that contact are marked `unsubscribed`
4. Future outbound cycles skip opted-out contacts

---

## 🎨 Customizing the UI

The UI uses:
- **CSS**: `/static/styles.css` (galaxy theme with blues, purples, animated stars)
- **React**: `/static/app.js` (components for Dashboard, Leads, Campaigns, etc.)

To customize colors, edit the CSS variables in `styles.css`:

```css
:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --accent: #f093fb;
    --dark: #1a1a2e;
    --darker: #0f0f1e;
    /* ... */
}
```

---

## 🧠 How AI Email Generation Works

### AnthropicService (`services/anthropic_service.py`)

When generating an email, the system:

1. **Collects context**:
   - Lead info (company, contact, market type, website)
   - Sequence step (initial vs follow-up)
   - Optional: fetched website homepage (first 2000 chars)
   - Optional: template context (hints for AI)

2. **Builds a prompt** for Claude:
   - "You are writing a {step_type} email..."
   - Recipient information
   - Website context (if available)
   - Instructions (be concise, authentic, no false claims)

3. **Calls Anthropic API**:
   - Model: `claude-3-5-sonnet-20241022` (or configured)
   - Receives subject + body

4. **Adds CAN-SPAM footer** (done by `EmailService`, not AI)

### Fallback

If Anthropic API key is not configured, the system uses placeholder emails.

---

## 📧 Zoho Email Integration

### EmailService (`services/email_service.py`)

The system sends emails via Zoho SMTP:

1. **SMTP Connection**: `smtp.zoho.com:587` (TLS)
2. **Authentication**: Username + password from `.env`
3. **Message Construction**:
   - Multipart (plain text + HTML)
   - From/To/Subject
   - CAN-SPAM footer appended
4. **Send**: Via `smtplib`

### Testing Connection

```python
from services.email_service import EmailService

service = EmailService(...)
if service.test_connection():
    print("Zoho connection successful!")
```

---

## 📁 Project Structure

```
Outbound-Omega/
├── app_main.py              # Main Flask application
├── config.py                # Configuration management
├── models.py                # SQLAlchemy database models
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
│
├── services/
│   ├── anthropic_service.py # AI email generation
│   ├── email_service.py     # Zoho SMTP sending
│   └── outbound_machine.py  # Core outbound logic
│
├── templates/
│   ├── index.html           # Main app entry point
│   └── unsubscribed.html    # Unsubscribe confirmation page
│
├── static/
│   ├── app.js               # React frontend
│   └── styles.css           # Galaxy theme CSS
│
├── scraper.py               # Existing Google Maps scraper
├── app.py                   # Existing scraper Flask app
└── README.md                # Original scraper README
```

---

## 🔧 API Endpoints

### Scraper Integration

- **POST /api/scraper/ingest**: Ingest leads from JSON

### Companies

- **GET /api/companies**: List companies (paginated)
- **GET /api/companies/:id**: Get company details
- **POST /api/companies**: Create company
- **PUT /api/companies/:id**: Update company

### Contacts

- **GET /api/contacts**: List contacts (paginated)
- **GET /api/contacts/:id**: Get contact details

### Leads

- **GET /api/leads**: List leads (with filters: status, campaign_id, market_type)
- **GET /api/leads/:id**: Get lead details (with emails, activities, sequences)
- **PUT /api/leads/:id**: Update lead
- **POST /api/leads/:id/score**: Recalculate lead score
- **POST /api/leads/:id/activities**: Add activity

### Campaigns

- **GET /api/campaigns**: List campaigns
- **GET /api/campaigns/:id**: Get campaign
- **POST /api/campaigns**: Create campaign
- **PUT /api/campaigns/:id**: Update campaign

### Sequences

- **GET /api/sequences**: List email sequences
- **GET /api/sequences/:id**: Get sequence with steps
- **POST /api/sequences**: Create sequence (with steps)
- **POST /api/sequences/:id/steps**: Add step to sequence

### Outbound Machine

- **POST /api/outbound/run**: Run outbound cycle
  ```json
  {
    "from_address": "outreach@yourcompany.com",
    "dry_run": false
  }
  ```
- **POST /api/outbound/add-to-sequence**: Add leads to sequence
  ```json
  {
    "lead_ids": [1, 2, 3],
    "sequence_id": 1
  }
  ```

### Dashboard

- **GET /api/dashboard/stats**: Get dashboard statistics

### Configuration

- **GET /api/config**: Get current configuration

### Unsubscribe

- **GET /unsubscribe?token=:token**: Handle unsubscribe requests

---

## 🐛 Troubleshooting

### "Anthropic API key not configured"

- Check your `.env` file
- Ensure `ANTHROPIC_API_KEY` is set
- Restart the Flask server

### "Zoho SMTP authentication failed"

- Verify `ZOHO_USERNAME` and `ZOHO_PASSWORD`
- Ensure you're using an **app-specific password** if 2FA is enabled
- Test connection with `EmailService.test_connection()`

### "Database errors"

- Delete `outbound_omega.db` and restart to recreate tables
- Check SQLAlchemy logs in console

### "Emails not sending"

- Check daily send limit: `MAX_EMAILS_PER_DAY`
- Verify leads have `status = 'active'` in `lead_sequences`
- Check contact `opt_out` status
- Review logs for errors

---

## 🚀 Next Steps / TODOs

### Immediate

- [ ] Add UI for creating campaigns and sequences (currently API-only)
- [ ] Add "Add to Sequence" button in Leads view
- [ ] Implement lead detail modal/page
- [ ] Add bulk actions (select multiple leads)

### Near-term

- [ ] Reply tracking (IMAP polling or Zoho webhook)
- [ ] Email open tracking (pixel tracking)
- [ ] A/B testing for email variants
- [ ] Lead import from CSV
- [ ] Advanced filtering and search

### Long-term

- [ ] Migrate to PostgreSQL for production
- [ ] Add authentication/user management
- [ ] Multi-tenancy (multiple agencies/teams)
- [ ] Integrate with calendar for meetings
- [ ] SMS outreach (Twilio)
- [ ] Webhooks for integrations (Zapier, n8n)

---

## 📚 Database Schema

### Core Tables

- **companies**: Company information
- **contacts**: Contact details (with opt_out tracking)
- **leads**: Lead records (linking companies + contacts)
- **campaigns**: Campaign definitions
- **email_sequences**: Email sequence definitions
- **email_steps**: Steps within sequences (with delay_days)
- **lead_sequences**: Tracks which leads are in which sequences
- **emails**: Sent email log
- **activities**: Activity log (emails, replies, notes, etc.)

See `models.py` for full schema with relationships.

---

## 🤝 Contributing

This is a local dev project. Feel free to:
- Fork and customize for your own use
- Submit issues or PRs for improvements
- Share feedback!

---

## 📄 License

Educational purposes. Users are responsible for ensuring compliance with applicable laws and CAN-SPAM regulations.

---

## 💬 Support

For questions or issues:
- Check the troubleshooting section
- Review API endpoint documentation
- Open an issue on GitHub

---

**Built with ❤️ and lots of ☕ for agencies that want to own their outbound stack.**
