# 3S Calculator

A bilingual solar savings and lead-capture application for 3S Solutions. The browser app runs without a build step; the FastAPI backend is the calculation source of truth and stores calculations/leads in SQLite locally.

## Run locally

Requirements: Python 3.12+ and Node.js 20+ (only needed if you later add frontend tooling).

Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

macOS/Linux:

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Serve the `frontend` directory with any static file server. The no-build interface reads its API URL from `frontend/config.js`; its default is `http://127.0.0.1:8000/api/v1` for local use. For deployment, change that value to your Render backend URL ending in `/api/v1`.

SQLite database is created automatically at `backend/3s_calculator.db`. API docs: `http://127.0.0.1:8000/docs`. The local setup starts without third-party credentials.

## Features

- English/Telugu landing and customer-type calculator flows.
- Lead-first customer journey: name, phone, location and contact consent are saved before the customer enters bill details; the calculation is linked to that lead afterward.
- Residential, commercial, and industrial estimate endpoints with documented assumptions, scenario projections and confidence notes.
- SQLite calculation/lead persistence, consent capture, lead listing, single-operator admin gate, CSV export and PDF report endpoint.
- Honest unconfigured status for Google Sheets, WhatsApp and Pabbly. Actual provider adapters and durable delivery processing require further implementation and have not been represented as delivered.
- Responsive customer experience using the supplied logo.

## Configuration

Copy `.env.example` to `.env` and set `ADMIN_API_KEY` before exposing admin routes. Production also requires `DATABASE_URL`, `CORS_ORIGINS`, `APP_BASE_URL`, and provider credentials. Never commit secrets. Google Sheets needs a service account with Editor access to the target spreadsheet. WhatsApp needs an approved Cloud API sender, access token, recipient, and approved template if the 24-hour customer-service window does not apply. See `docs/`.

The included yield, tariff proxy, costs, self-consumption, escalation, degradation, maintenance, and emissions factor are illustrative planning assumptions, not official tariffs, quotations, site forecasts, or current incentive determinations. No subsidy is deducted. Confirm utility rules, current MNRE scheme terms and site conditions before making a decision.

## Admin account

There is no default password or seeded administrator. Copy the root `.env.example` to `.env`, set `ADMIN_API_KEY` to a long random secret, and start the backend from its folder. Open `frontend/admin.html`, then enter the same key to view/update leads and export CSV. It is held in session storage and sent as `X-Admin-Key`. Replace this simple single-operator gate with managed user accounts, sessions, MFA and role-based access before production use.

## Deployment

For Vercel + Render: import the repository into Vercel and set the project root to `frontend`. Before deploying, set `frontend/config.js` to `window.API_BASE = 'https://YOUR-SERVICE.onrender.com/api/v1';`. Deploy the `backend` directory as a Render Web Service with build command `pip install -r requirements.txt` and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. In Render environment settings, set `ADMIN_API_KEY` to a long random secret, `DATABASE_URL` to a persistent PostgreSQL database URL, and `CORS_ORIGINS` to the exact Vercel production origin (for example `https://your-project.vercel.app`, without a trailing slash). For Supabase from Render, use the Supabase Session pooler connection string. Open the admin page at `https://your-project.vercel.app/admin.html` and enter the same secret. Keep the key in Render environment settings and the admin password field only; never put it in `config.js` or frontend source. Verify `/api/v1/health`, then keep database backups and configure retention/deletion per company policy.

## Known gaps

This first runnable implementation is a deliberately conservative foundation, not a claim of production readiness. Official current AP/Telangana tariff datasets, verified subsidy rules, commercial/industrial incentives, actual Sheets/WhatsApp/SMTP delivery, role-based admin accounts, uploads, advanced billing components, and Telugu-capable branded PDF typography need business credentials and review. All estimates disclose their assumptions and are not engineering proposals.
