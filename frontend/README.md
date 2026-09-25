# RepoGuard AI

Evidence-backed AI software engineering auditor. RepoGuard analyzes codebases using specialized AI agents and deterministic engineering tools, then produces a trustworthy engineering audit where every finding is backed by verifiable file and line evidence.

> Evidence > AI opinion.

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The dev server runs automatically. Open the app in your browser to view it.

## Environment Variables

Create a `.env` file (or use the defaults):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEMO_MODE=true
NEXT_PUBLIC_SCRAPE_TARGET_URL=http://127.0.0.1:8100
```

| Variable                        | Description                                                                          | Default                 |
| ------------------------------- | ------------------------------------------------------------------------------------ | ----------------------- |
| `NEXT_PUBLIC_API_URL`           | Base URL of the FastAPI backend                                                      | `http://localhost:8000` |
| `NEXT_PUBLIC_DEMO_MODE`         | When `true`, the app runs on built-in demo data. Set to `false` to use the real API. | `true`                  |
| `NEXT_PUBLIC_SCRAPE_TARGET_URL` | Base URL used by the Web Scraping page to generate scraping targets                  | `http://127.0.0.1:8100` |

No secrets, API keys, or tokens are stored in the frontend.

## Demo Mode

When `NEXT_PUBLIC_DEMO_MODE=true` (the default), the app displays realistic demo data with a visible "Demo data" indicator. This lets the app run without a backend.

Set `NEXT_PUBLIC_DEMO_MODE=false` to connect to the real FastAPI backend. All API calls go through the isolated service layer in `src/lib/api.ts`.

## Web Scraping & Browser Automation

RepoGuard includes a dedicated Web Scraping dashboard at `/scraping` for controlled browser automation and extraction.

The scraping interface provides:

* Playwright-based browser execution
* Configurable scraping target URLs
* Concurrent scraping jobs
* Worker-level execution telemetry
* Browser session tracking
* HTTP status and latency metrics
* Retry and failure tracking
* Structured extraction results
* Live job progress
* Scraping event history
* Persisted scraping records
* Configurable timeout and concurrency settings
* Controlled proxy configuration support
* Challenge/block detection telemetry

The default development scraping target is:

```text
http://127.0.0.1:8100
```

This is used by the local benchmark target and is not a production Render URL.

For production deployments, `NEXT_PUBLIC_SCRAPE_TARGET_URL` should point only to an authorized, publicly reachable scraping target.

## API Integration Points

The frontend talks to the backend exclusively through `src/lib/api.ts`. Expected endpoints:

| Method | Endpoint                     | Purpose                             |
| ------ | ---------------------------- | ----------------------------------- |
| GET    | `/health`                    | Backend health check                |
| POST   | `/api/audits`                | Create a new audit                  |
| GET    | `/api/audits`                | List all audits                     |
| GET    | `/api/audits/:id`            | Get audit detail                    |
| GET    | `/api/audits/:id/findings`   | Get findings for an audit           |
| GET    | `/api/audits/:id/evidence`   | Get evidence for a finding          |
| GET    | `/api/audits/:id/agents`     | Get agent runs for an audit         |
| GET    | `/api/repositories`          | List repositories                   |
| GET    | `/api/evaluations`           | List evaluations                    |
| GET    | `/api/evaluations/:id`       | Get evaluation detail               |
| GET    | `/api/changelog`             | Get improvement changelog           |
| GET    | `/api/trajectories/:auditId` | Get agent trajectories              |
| POST   | `/scraping/jobs`             | Create a scraping job               |
| GET    | `/scraping/jobs`             | List scraping jobs                  |
| GET    | `/scraping/jobs/:id`         | Get scraping job status and metrics |
| GET    | `/scraping/jobs/:id/records` | Get persisted scraping records      |
| GET    | `/scraping/jobs/:id/events`  | Get scraping execution events       |

TypeScript interfaces for request/response shapes live in `src/types/`.

## Project Structure

```text
app/                         Next.js App Router pages

  page.tsx                   Dashboard
  new-audit/                 Start a repository audit
  audits/                    Audits list + report detail
  analysis/[auditId]/        Real-time agent workflow
  architecture/[auditId]/    Architecture analysis
  testing/[auditId]/         Testing analysis
  dependencies/[auditId]/    Dependency analysis
  evaluation/                Benchmark evaluation
  changelog/                 Improvement changelog
  trajectories/              Agent trajectory viewer
  repositories/              Repository management
  scraping/                  Web scraping & browser automation
  settings/                  Settings

components/                  Shared UI components

  ui/                        shadcn/ui primitives
  app-shell.tsx              Sidebar + header layout
  sidebar.tsx                Desktop navigation
  mobile-nav.tsx             Mobile drawer navigation
  score-display.tsx          Score rings and bars
  severity-badge.tsx         Severity / risk badges
  verification-badge.tsx     Evidence verification badge
  state-views.tsx            Loading / error / empty states
  stepper.tsx                Audit progress stepper
  code-block.tsx             Syntax-highlighted code display

src/

  lib/api.ts                 Typed API service layer
  lib/demo.ts                Demo/mock data (explicitly separated)
  types/                     TypeScript type definitions
  hooks/use-health.ts        Backend health check hook
```

## Tech Stack

* Next.js (App Router)
* TypeScript (strict, no `any`)
* Tailwind CSS
* shadcn/ui + Radix UI
* Lucide React icons
* Recharts (evaluation charts)
* Zod (input validation)
* next-themes (dark/light mode)
* Playwright (browser automation)
* FastAPI (scraping API integration)
* PostgreSQL (scraping job and record persistence)

````

One small correction from your original README: I used the actual scraping endpoints under `/scraping/...`, rather than `/api/scraping/...`, because your FastAPI scraping router currently uses the `/scraping` prefix.

After saving it, run:

```powershell
npm run build
````

If the build passes, then you're ready to commit the frontend changes.
