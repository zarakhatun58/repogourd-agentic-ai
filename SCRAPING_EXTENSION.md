# RepoGuard AI — Web Automation Extension

This extension adds an authorized browser-automation/data-extraction workflow to the existing RepoGuard application.

## Demonstrated engineering capabilities

- Python + FastAPI
- Playwright/Chromium browser automation
- asyncio-based bounded concurrency
- isolated browser contexts per record
- configurable viewport/locale/timezone
- optional configured proxy endpoint
- retries/timeouts can be extended at the service layer
- structured CSS-selector extraction
- PostgreSQL persistence
- observable job events
- React/Next.js monitoring dashboard
- throughput and success metrics

## Responsible demo boundary

The default demo target is a local FastAPI site at `127.0.0.1:8100`. The API enforces `SCRAPER_ALLOWED_HOSTS` so the benchmark does not accidentally run against an unauthorized third-party site.

This module does not implement CAPTCHA solving, anti-bot bypass, fingerprint spoofing for evasion, or techniques intended to circumvent Cloudflare, DataDome, Kasada, Akamai, or similar access controls.

## Setup

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
alembic upgrade head
uvicorn app.main:app --reload
```

Local target in another terminal:

```bash
cd backend
uvicorn scripts.demo_target:app --host 127.0.0.1 --port 8100
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `/scraping`.

## Benchmark

The included benchmark sends 100 requests to the local authorized target with five bounded workers:

```bash
cd backend
python scripts/run_benchmark.py
```

The dashboard shows processed records, successful/failed records, throughput, structured JSON, and execution events.

## Searchlook Loom wording

A truthful description is:

> "I extended RepoGuard with a Python Playwright browser-automation engine. It uses asyncio with bounded concurrency, isolated browser contexts, configurable session/browser profiles, optional proxy configuration, structured extraction, PostgreSQL persistence, and an observable execution dashboard. For the live benchmark I'm using a local authorized target so the batch run demonstrates concurrency and data throughput without generating uncontrolled traffic to a third-party service."

Do not describe this demo as a Cloudflare/DataDome/Kasada/Akamai bypass system.
