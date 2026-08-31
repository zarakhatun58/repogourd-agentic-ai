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

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEMO_MODE=true
```

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend | `http://localhost:8000` |
| `NEXT_PUBLIC_DEMO_MODE` | When `true`, the app runs on built-in demo data. Set to `false` to use the real API. | `true` |

No secrets, API keys, or tokens are stored in the frontend.

## Demo Mode

When `NEXT_PUBLIC_DEMO_MODE=true` (the default), the app displays realistic demo data with a visible "Demo data" indicator. This lets the app run without a backend.

Set `NEXT_PUBLIC_DEMO_MODE=false` to connect to the real FastAPI backend. All API calls go through the isolated service layer in `src/lib/api.ts`.

## API Integration Points

The frontend talks to the backend exclusively through `src/lib/api.ts`. Expected endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend health check |
| POST | `/api/audits` | Create a new audit |
| GET | `/api/audits` | List all audits |
| GET | `/api/audits/:id` | Get audit detail |
| GET | `/api/audits/:id/findings` | Get findings for an audit |
| GET | `/api/audits/:id/evidence` | Get evidence for a finding |
| GET | `/api/audits/:id/agents` | Get agent runs for an audit |
| GET | `/api/repositories` | List repositories |
| GET | `/api/evaluations` | List evaluations |
| GET | `/api/evaluations/:id` | Get evaluation detail |
| GET | `/api/changelog` | Get improvement changelog |
| GET | `/api/trajectories/:auditId` | Get agent trajectories |

TypeScript interfaces for all request/response shapes live in `src/types/`.

## Project Structure

```
app/                        Next.js App Router pages
  page.tsx                  Dashboard
  new-audit/                Start a repository audit
  audits/                   Audits list + report detail
  analysis/[auditId]/       Real-time agent workflow
  architecture/[auditId]/   Architecture analysis
  testing/[auditId]/        Testing analysis
  dependencies/[auditId]/   Dependency analysis
  evaluation/               Benchmark evaluation (baseline vs advanced)
  changelog/                Improvement changelog
  trajectories/             Agent trajectory viewer
  repositories/             Repository management
  settings/                 Settings
components/                 Shared UI components
  ui/                       shadcn/ui primitives
  app-shell.tsx             Sidebar + header layout
  sidebar.tsx               Desktop navigation
  mobile-nav.tsx            Mobile drawer navigation
  score-display.tsx         Score rings and bars
  severity-badge.tsx        Severity / risk badges
  verification-badge.tsx    Evidence verification badge
  state-views.tsx           Loading / error / empty states
  stepper.tsx               Audit progress stepper
  code-block.tsx            Syntax-highlighted code display
src/
  lib/api.ts                Typed API service layer
  lib/demo.ts               Demo/mock data (explicitly separated)
  types/                    TypeScript type definitions
  hooks/use-health.ts       Backend health check hook
```

## Tech Stack

- Next.js (App Router)
- TypeScript (strict, no `any`)
- Tailwind CSS
- shadcn/ui + Radix UI
- Lucide React icons
- Recharts (evaluation charts)
- Zod (input validation)
- next-themes (dark/light mode)
