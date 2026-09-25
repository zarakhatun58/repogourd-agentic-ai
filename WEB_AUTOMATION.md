# RepoGuard AI — Web Automation Extension

This extension adds an authorized browser-automation and data-extraction workflow to the existing RepoGuard application.

## Demonstrated Engineering Capabilities

- Python + FastAPI
- Playwright + Chromium browser automation
- asyncio-based bounded concurrency
- Isolated browser contexts per record
- Configurable viewport, locale, and timezone
- Optional configured proxy endpoint
- Retries and timeouts
- Structured CSS-selector extraction
- PostgreSQL persistence
- Observable job events
- React/Next.js monitoring dashboard
- Throughput and success metrics
- Structured JSON runtime telemetry
- Worker and session tracking

## Architecture

```text
Next.js Frontend
       |
       v
FastAPI Scraping API
       |
       v
Scrape Manager
       |
       v
Bounded Worker Pool
       |
       v
Playwright + Chromium
       |
       v
Authorized Target
       |
       v
PostgreSQL