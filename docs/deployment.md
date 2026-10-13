# Deployment guide

Serve `frontend/` as static files and route `/api/v1/*` to the FastAPI host, or configure an API base URL and rebuild the static app. Deploy the Python backend to Render/Railway or similar with Python 3.12+, persistent PostgreSQL, HTTPS, `DATABASE_URL`, `ADMIN_API_KEY`, and a strict `CORS_ORIGINS` allowlist. Install `backend/requirements.txt`; start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT` from `backend/`. The health endpoint is `/api/v1/health`.

Current tables initialize on app start for the starter SQLite mode. Formal Alembic migrations, managed admin identities, integration worker, retention/deletion jobs, monitoring and backup restore drills are production prerequisites. Back up the PostgreSQL database and test restoration. Do not enable real lead delivery until adapters and credentials are verified.
