# Architecture

Static HTML/CSS/JavaScript customer UI calls a versioned FastAPI service. The API validates inputs and runs deterministic Python calculation logic. SQLite stores calculation snapshots and lead records locally; set `DATABASE_URL` for PostgreSQL in production. Admin routes require `X-Admin-Key` matching `ADMIN_API_KEY`. This is a single-operator starter gate, not a full multi-user identity system.

The local version reports third-party integrations as unconfigured. The lead record is the durable primary record, but external delivery adapters and a background outbox worker remain to be implemented before enabling delivery. Never advertise a saved lead as delivered to Sheets or WhatsApp.
