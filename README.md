# Myntra Data Collector & Report Builder

A production-oriented FastAPI + HTML/CSS/JavaScript application for collecting **publicly accessible** Myntra product information selected by the user, storing it in a database, and exporting Excel/PDF reports.

## 1. Deployment status

This repository is prepared for:

- Docker / Docker Compose
- Render using `render.yaml`
- Railway/other Docker-capable hosts
- Traditional VPS/container deployment
- Local Windows/Linux/macOS development

The application listens on `0.0.0.0` and honors the hosting platform's `PORT` environment variable.

## 2. Responsible collection

This project deliberately does **not** bypass CAPTCHA, authentication, paywalls, robots restrictions, access controls, or anti-bot protections. If Myntra returns 401/403/429 or otherwise limits automated access, the job stops and reports that automated collection is unavailable.

The collector never invents missing prices, ratings, review counts, product IDs, sellers, or rating distributions. Missing fields are represented as `Not Available`/null as appropriate.

Always review Myntra's current Terms of Use, robots.txt, applicable law, and your organization's rules before collecting data.

## 3. Production architecture

```text
Browser
   |
   v
FastAPI application
   |
   +---- Public Myntra pages (polite requests)
   |
   +---- PostgreSQL (recommended production database)
   |
   +---- Excel/PDF exporters
   |
   +---- Persistent data/export storage
```

SQLite remains supported for local development. PostgreSQL is recommended for deployed environments.

## 4. Deploy with Docker

### Build

```bash
docker build -t myntra-data-collector .
```

### Run with PostgreSQL

Set your managed PostgreSQL connection string:

```bash
docker run -d \
  --name myntra-data-collector \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/DATABASE" \
  -e ENVIRONMENT=production \
  -e REQUEST_DELAY=1.2 \
  myntra-data-collector
```

The application automatically converts `postgresql://` / `postgres://` URLs to the `psycopg` SQLAlchemy driver.

Open:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

## 5. Docker Compose

Copy `.env.example` to `.env` and run:

```bash
docker compose up -d --build
```

The default Compose configuration persists SQLite data and generated exports in Docker volumes.

For a serious production installation, use managed PostgreSQL rather than the Compose SQLite volume.

## 6. Render deployment

The repository includes `render.yaml` and a production Dockerfile.

1. Push this folder to GitHub/GitLab.
2. Create a new Blueprint/Web Service on Render.
3. Select the repository.
4. Render will detect `render.yaml`.
5. Set `DATABASE_URL` to a managed PostgreSQL connection string.
6. Deploy.
7. Verify `/health`.
8. Open the generated service URL.

The service is configured to use one Uvicorn worker intentionally because the collection job state is currently held in-process. Do not increase worker count until the job system is moved to shared Redis/database-backed task state.

## 7. Railway / other Docker hosts

Use the included `Dockerfile`.

Required environment variables:

```text
DATABASE_URL=<managed PostgreSQL URL>
ENVIRONMENT=production
PORT=<provided automatically by platform>
MYNTRA_BASE_URL=https://www.myntra.com
REQUEST_DELAY=1.2
REQUEST_TIMEOUT=20
MAX_RETRIES=2
MAX_CONCURRENCY=2
CORS_ORIGINS=*
```

The platform should expose the container's HTTP port using its normal `$PORT` mechanism.

## 8. PostgreSQL production recommendation

Use a managed PostgreSQL database for deployed applications. The current SQLAlchemy models create the required tables automatically on startup:

- `collections`
- `products`
- `collection_products`

For larger production deployments, replace automatic startup table creation with a migration tool such as Alembic and add scheduled backups.

## 9. Persistent exports

Excel/PDF files are written to `exports/`.

A container filesystem may be ephemeral on cloud platforms. For long-term retention, add an object-storage adapter (S3-compatible storage, Cloudflare R2, etc.) and upload completed reports there. The current application is deployment-ready for generating/downloading reports during the running instance, but it does not yet implement object-storage retention.

## 10. Production environment

Copy `.env.example` to `.env` locally. Do **not** commit `.env`.

Important variables:

```text
ENVIRONMENT=production
DATABASE_URL=...
MYNTRA_BASE_URL=https://www.myntra.com
REQUEST_DELAY=1.2
REQUEST_TIMEOUT=20
MAX_RETRIES=2
MAX_CONCURRENCY=2
CORS_ORIGINS=*
```

If the frontend is hosted separately, replace `CORS_ORIGINS=*` with the exact frontend origin, for example:

```text
CORS_ORIGINS=https://your-frontend.example.com
```

## 11. Local development

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Or double-click `start.bat`.

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## 12. Static HTML mode

`frontend/index.html` can be opened directly. It defaults to:

```text
http://localhost:8000/api
```

Start the backend first. If the backend is unavailable, the UI reports the failure rather than pretending that collection succeeded.

## 13. API

- `GET /api/categories`
- `GET /api/categories/{category}/segments`
- `GET /api/categories/{category}/segments/{segment}/products`
- `POST /api/collection/start`
- `GET /api/collection/{job_id}`
- `GET /api/collection/{job_id}/products`
- `POST /api/collection/{job_id}/export/excel`
- `GET /api/collection/{job_id}/export/excel/download`
- `POST /api/collection/{job_id}/export/pdf`
- `GET /api/collection/{job_id}/export/pdf/download`
- `GET /health`

## 14. Production limitations to understand

### Background jobs

The current collector uses FastAPI's in-process background task mechanism. It is reliable for a single application process but is not a distributed job queue. The deployment therefore uses one Uvicorn worker.

For a high-volume production service, move jobs to Redis + Celery/RQ/Arq or another shared queue and store progress in PostgreSQL.

### Myntra HTML changes

Public page structure can change. The scraper should be regression-tested whenever the source HTML changes.

### Cloud storage

Cloud hosts can remove local container files during redeploys. Use object storage if exported reports need long-term retention.

### Anti-bot/access restrictions

The application does not attempt to evade restrictions. If access is blocked, the collection stops.

## 15. Final deployment checklist

- [ ] PostgreSQL database configured
- [ ] `DATABASE_URL` set as a platform secret/environment variable
- [ ] `ENVIRONMENT=production`
- [ ] `PORT` supplied by platform
- [ ] `CORS_ORIGINS` restricted if frontend is separate
- [ ] `/health` returns HTTP 200
- [ ] Frontend loads
- [ ] Category discovery works
- [ ] Collection job starts
- [ ] Real product data appears
- [ ] Missing fields remain unavailable rather than invented
- [ ] Excel export downloads
- [ ] PDF export downloads
- [ ] Database backups configured
- [ ] Persistent/object storage configured if report retention is required
- [ ] Current Myntra Terms/robots requirements reviewed

## 16. Testing

Syntax check:

```bash
python -m compileall backend
```

Container health check:

```bash
docker compose up -d --build
curl http://localhost:8000/health
```

Do not claim a live Myntra collection succeeded unless it actually returned source data.
