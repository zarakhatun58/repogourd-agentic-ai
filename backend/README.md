# RepoGuard Agent AI

> **Evidence-first repository security analysis with a reproducible agent execution trail.**

RepoGuard Agent AI helps developers, engineering teams, and security reviewers perform a structured first-pass security assessment of unfamiliar software repositories.

The system combines:

- repository ingestion from ZIP or GitHub
- deterministic source inspection
- eight security detection rules
- structured findings
- source-level evidence
- evidence verification
- persistent agent execution trajectory
- benchmark evaluation
- a Next.js frontend and FastAPI backend

The core principle is:

> **Find the risk. Show the evidence. Expose the execution. Measure the improvement.**

---

## 1. What RepoGuard Does

RepoGuard converts repository security inspection into a repeatable workflow:

```text
Repository
    ↓
Ingestion
    ↓
Analysis Run
    ↓
Repository Inspection
    ↓
Security Scan
    ↓
Findings
    ↓
Source Evidence
    ↓
Verification
    ↓
Agent Trajectory
    ↓
Reviewable Result
```

A finding is designed to be traceable to:

```text
Finding
  ↓
Rule
  ↓
File
  ↓
Line
  ↓
Source evidence
  ↓
Verification
```

RepoGuard is a **first-pass security review assistant**, not a replacement for penetration testing, complete SAST, dependency scanning, runtime security testing, threat modeling, or qualified human security review.

---

# 2. Main Features

## Repository ingestion

Supported ingestion methods:

- GitHub repository URL
- ZIP upload

The GitHub URL must identify an actual repository, for example:

```text
https://github.com/OWNER/REPOSITORY
```

A user/organization URL alone is not sufficient.

## Analysis runs

Each analysis stores:

- repository ID
- status
- agent type
- commit SHA
- start time
- completion time
- error information

Supported statuses include:

```text
queued
running
completed
failed
```

## Security analysis

The deterministic security scanner currently implements eight rules:

| Rule | Severity | Detection |
|---|---|---|
| RG001 | High | Python `eval()` |
| RG002 | High | Python `exec()` |
| RG003 | Medium | Hardcoded password pattern |
| RG004 | Medium | Hardcoded secret pattern |
| RG005 | High | JavaScript/TypeScript `eval()` |
| RG006 | High | Potential `child_process` command execution |
| RG007 | High | `dangerouslySetInnerHTML` |
| RG008 | Medium | Insecure `http://` URL |

Supported source extensions:

```text
.py
.js
.jsx
.ts
.tsx
```

Ignored directories include:

```text
.git
node_modules
.venv
venv
__pycache__
.pytest_cache
dist
build
.next
coverage
```

The scanner is deliberately deterministic and line-based. It reports candidate security-relevant patterns; the analysis workflow separately collects and verifies source evidence.

---

# 3. Evidence-First Findings

Findings contain structured information such as:

```text
rule_id
severity
title
description
file_path
line_start
line_end
status
```

Evidence contains:

```text
evidence_type
file_path
line_start
line_end
content
verification_status
```

Example:

```text
Rule: RG002
Severity: high
Title: Potential use of exec()
File: src/example.py
Line: 18

Evidence:
exec(user_input)

Verification:
verified
```

This makes a finding directly reviewable instead of presenting only an unsupported security claim.

---

# 4. Agent Trajectory

RepoGuard persists observable execution events in `AgentTrajectory`.

The trajectory intentionally records user-facing execution information and **does not store hidden chain-of-thought**.

A successful analysis currently records ten execution events:

```text
1.  analysis_started
2.  repository_inspection_started
3.  repository_inspected
4.  security_scan_started
5.  findings_generated
6.  evidence_collection_started
7.  evidence_collected
8.  verification_started
9.  verification_completed
10. analysis_completed
```

A failed execution records:

```text
analysis_failed
```

The trajectory can expose:

- step number
- event type
- timestamp
- observation
- tool name
- input data
- output data

Important implementation distinction:

> The repository inspection, security scan, evidence collection, and verification are bounded deterministic operations orchestrated by the analysis service. They should not be represented as hidden model reasoning.

---

# 5. Architecture

```text
                         ┌──────────────────────┐
                         │      Next.js UI      │
                         │                      │
                         │ Audits               │
                         │ Repositories         │
                         │ Analysis             │
                         │ Findings             │
                         │ Evidence             │
                         │ Evaluation           │
                         │ Agent Trajectory     │
                         └──────────┬───────────┘
                                    │ HTTP/JSON
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼─────────────────────┐
             ▼                      ▼                     ▼
      Repository Service      Analysis Service       Evaluation
             │                      │
             │                      ▼
             │              Security Scanner
             │                      │
             │             ┌────────┴────────┐
             │             ▼                 ▼
             │         Findings          Evidence
             │                               │
             └────────────────┬──────────────┘
                              ▼
                       Agent Trajectory
                              │
                              ▼
                         PostgreSQL
```

---

# 6. Technology Stack

## Backend

- Python 3.12
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy
- Alembic
- PostgreSQL 17
- psycopg 3
- GitPython
- LangGraph
- HTTPX
- python-dotenv
- pytest

## Frontend

- Next.js
- Node.js 18+
- npm

---

# 7. Project Structure

```text
repoguard-agent-ai/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analysis_routes.py
│   │   │   ├── evaluation_routes.py
│   │   │   ├── finding_routes.py
│   │   │   ├── repository_routes.py
│   │   │   ├── trajectory_routes.py
│   │   │   ├── changelog_routes.py
│   │   │   └── routes.py
│   │   │
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── agent_trajectory_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── evaluation_service.py
│   │   │   └── repository_service.py
│   │   │
│   │   ├── tools/
│   │   │   └── security_tools.py
│   │   │
│   │   └── main.py
│   │
│   ├── storage/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend/
│   ├── app/
│   │   ├── analysis/
│   │   ├── audits/
│   │   ├── evaluation/
│   │   ├── repositories/
│   │   └── trajectories/
│   ├── components/
│   ├── hooks/
│   └── src/
│       ├── lib/
│       └── types/
│
├── README.md
├── REPRODUCTION.md
└── IMPROVEMENT_CHANGELOG.md
```

---

# 8. Backend Dependencies

Recommended `backend/requirements.txt`:

```text
fastapi[standard]>=0.139,<1
pydantic>=2.13,<3
pydantic-settings>=2.0,<3
python-dotenv>=1.0,<2
langgraph>=0.6,<2
psycopg[binary]>=3.2,<4
SQLAlchemy>=2.0,<3
alembic>=1.15,<2
httpx>=0.27,<1
gitpython>=3.1,<4
pytest>=8,<9
```

---

# 9. Environment Configuration

## Local development

Create:

```text
backend/.env
```

Example:

```dotenv
APP_NAME=RepoGuard Agent AI
DATABASE_URL=postgresql+psycopg://repoguard:repoguard@localhost:5432/repoguard
```

Do not commit real credentials.

For production, use a strong database password and provide secrets through the deployment platform or secret manager.

## Docker Compose

Inside Docker Compose, the backend must connect to PostgreSQL using the service name:

```dotenv
DATABASE_URL=postgresql+psycopg://repoguard:CHANGE_ME@postgres:5432/repoguard
```

**Do not use `localhost` for the database host from inside the backend container.**

`localhost` inside the backend container refers to the backend container itself.

---

# 10. Docker Deployment

## Backend Dockerfile

The GitHub ingestion implementation uses GitPython. The container therefore needs the `git` executable.

Use:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /app/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Why `git` is installed

`gitpython` is a Python library, but GitHub repository cloning still requires the Git executable in the runtime container.

---

# 11. Docker Compose

Recommended production-style Compose configuration:

```yaml
services:

  postgres:
    image: postgres:17-alpine
    container_name: repoguard-postgres
    restart: unless-stopped

    environment:
      POSTGRES_DB: repoguard
      POSTGRES_USER: repoguard
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-CHANGE_ME}

    volumes:
      - postgres_data:/var/lib/postgresql/data

    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U repoguard -d repoguard"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build:
      context: ./backend

    container_name: repoguard-backend
    restart: unless-stopped

    environment:
      APP_NAME: RepoGuard Agent AI
      DATABASE_URL: postgresql+psycopg://repoguard:${POSTGRES_PASSWORD:-CHANGE_ME}@postgres:5432/repoguard

    depends_on:
      postgres:
        condition: service_healthy

    ports:
      - "8000:8000"

    volumes:
      - repository_storage:/app/storage

    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
        ]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 10s

volumes:
  postgres_data:
  repository_storage:
```

## Production `.env`

For Docker Compose:

```dotenv
POSTGRES_PASSWORD=REPLACE_WITH_A_LONG_RANDOM_PASSWORD
```

Do not use:

```text
repoguard
```

as a production password.

---

# 12. Important Deployment Correction

The original local-development database URL:

```text
postgresql+psycopg://repoguard:repoguard@localhost:5432/repoguard
```

is correct only when the FastAPI application runs directly on the host.

When FastAPI runs in Docker Compose, use:

```text
postgresql+psycopg://repoguard:YOUR_PASSWORD@postgres:5432/repoguard
```

because `postgres` is the Compose service hostname.

---

# 13. Database Migrations

If Alembic migrations are present in the repository, run them before starting the application:

```powershell
docker compose run --rm backend alembic upgrade head
```

Then:

```powershell
docker compose up -d --build
```

If the project does not yet contain an Alembic migration revision, create and test the initial migration before production deployment.

Do not silently rely on application startup to create production database tables unless that behavior is intentionally implemented and tested.

---

# 14. Local Backend Setup

Windows PowerShell:

```powershell
cd D:\repoguard-agent-ai\backend
```

Create the environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start PostgreSQL.

Then start FastAPI:

```powershell
uvicorn app.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "repoguard-agent-ai"
}
```

---

# 15. Frontend Setup

Open a second terminal:

```powershell
cd D:\repoguard-agent-ai\frontend
```

Install packages:

```powershell
npm install
```

Configure:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start Next.js:

```powershell
npm run dev
```

Open:

```text
http://localhost:3000
```

---

# 16. CORS

The current backend configuration allows:

```text
http://localhost:3000
```

For local development this is appropriate.

For deployment, the frontend origin should be explicitly configured instead of permanently hard-coding localhost.

Recommended application configuration:

```python
import os

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]
```

Then:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Production example:

```dotenv
CORS_ORIGINS=https://your-frontend.example.com
```

Do not use:

```text
*
```

together with credentialed browser requests.

---

# 17. API

## Health

```http
GET /health
```

Expected:

```json
{
  "status": "ok",
  "service": "repoguard-agent-ai"
}
```

## Audits

```http
POST /audits
GET /audits
GET /audits/{audit_id}
```

## Repositories

```http
POST /repositories/github
POST /repositories/upload
GET /repositories
GET /repositories/{repository_id}
```

### GitHub request

```json
{
  "url": "https://github.com/OWNER/REPOSITORY"
}
```

### ZIP upload

```text
POST /repositories/upload
Content-Type: multipart/form-data

file=<repository.zip>
```

## Analyses

```http
POST /analyses
GET /analyses
GET /analyses/{analysis_id}
POST /analyses/{analysis_id}/run
GET /analyses/{analysis_id}/findings
GET /analyses/{analysis_id}/trajectory
```

### Create analysis

```json
{
  "repository_id": "REPOSITORY_UUID",
  "agent_type": "repoguard-agent"
}
```

## Findings

```http
GET /findings/{finding_id}/evidence
```

## Evaluations

```http
GET /evaluations
POST /evaluations/run
GET /evaluations/{evaluation_id}
GET /evaluations/{evaluation_id}/cases
GET /evaluations/{evaluation_id}/metrics
```

---

# 18. End-to-End API Flow

```text
1. POST /repositories/github
          ↓
2. Receive repository_id
          ↓
3. POST /analyses
          ↓
4. Receive analysis_id
          ↓
5. POST /analyses/{analysis_id}/run
          ↓
6. GET /analyses/{analysis_id}
          ↓
7. GET /analyses/{analysis_id}/findings
          ↓
8. GET /findings/{finding_id}/evidence
          ↓
9. GET /analyses/{analysis_id}/trajectory
```

Every UUID used in the URLs must be a real UUID returned by the preceding API operation.

---

# 19. Analysis Execution Workflow

The analysis service orchestrates:

```text
Analysis initialization
        ↓
Repository inspection
        ↓
Security analysis
        ↓
Finding creation
        ↓
Evidence collection
        ↓
Verification
        ↓
Final result
```

The current implementation records ten observable trajectory events.

### Repository inspection

The inspection stage:

- enumerates repository files
- ignores vendor/generated directories
- selects supported source extensions
- sorts the resulting source-file list

### Security scanner

The security scanner accepts:

```text
workspace
relative source-file paths
```

and returns:

```text
findings
files_scanned
rules_executed
```

The scanner does not directly create database records.

### Evidence collection

The evidence stage reads the cited source lines again and creates `Evidence` records.

### Verification

The verification stage confirms that:

- the file exists
- the cited line exists
- collected evidence matches the current source line

Verified evidence is marked:

```text
verified
```

Rejected evidence is marked:

```text
rejected
```

---

# 20. Security Scanner Contract

The scanner returns structured results equivalent to:

```python
{
    "findings": [
        {
            "rule_id": "RG002",
            "severity": "high",
            "title": "Potential use of exec()",
            "description": "...",
            "file_path": "src/example.py",
            "line_start": 18,
            "line_end": 18,
            "matched_text": "exec(user_input)"
        }
    ],
    "files_scanned": 10,
    "rules_executed": 80
}
```

The scanner is intentionally bounded and deterministic.

It does not:

- create database records
- collect evidence
- verify findings
- make final acceptance decisions
- expose hidden reasoning

---

# 21. Important Security Scanner Limitation

The current rules are pattern-based.

For example, RG003 uses a pattern equivalent to:

```text
password =
```

and RG004 uses:

```text
secret =
```

Therefore the scanner should be described as detecting **candidate patterns**, not proving that a password or secret is actually exploitable.

Likewise:

```text
eval(
child_process
dangerouslySetInnerHTML
http://
```

are security-relevant signals, not automatic proof of a vulnerability.

This distinction should remain in the product documentation and presentation.

---

# 22. Evaluation

RepoGuard includes a repeatable benchmark.

Current documented benchmark configuration:

```text
Benchmark version: v1
Case count: 10
Primary metric: F1
```

Baseline:

```text
RG001
RG002
RG005
```

Advanced implementation:

```text
RG001–RG008
```

Configured evaluation model:

```json
{
  "case_count": 10,
  "baseline": "three-rule deterministic detector (RG001, RG002, RG005)",
  "advanced": "full RepoGuard rule detector (RG001-RG008)",
  "human_review_rate_per_hour": 60,
  "agent_compute_cost_per_case": 0.02
}
```

---

# 23. Reported Benchmark Result

The documented completed benchmark reports:

| Metric | Baseline | RepoGuard | Improvement |
|---|---:|---:|---:|
| F1 | 53.33% | 100% | +46.67 pp |
| Human time | 54 min | 21 min | 33 min less |
| Cost | $54.00 | $21.20 | $32.80 less |
| Critical issue detection | 60% | 100% | +40 pp |
| Evidence-supported findings | 100% | 100% | Maintained |
| False positives | 0% | 0% | Maintained |

Human-time reduction:

```text
54 → 21 minutes
≈ 61.1% less
```

Primary benchmark improvement:

```text
53.33% → 100%
+46.67 percentage points
```

These numbers should be presented as the result of the configured benchmark, not as a universal guarantee for arbitrary repositories.

---

# 24. Benchmark Reproduction

Run:

```http
POST /evaluations/run
```

Then:

```http
GET /evaluations/EVALUATION_UUID
```

Retrieve:

```http
GET /evaluations/EVALUATION_UUID/metrics
```

and:

```http
GET /evaluations/EVALUATION_UUID/cases
```

The evaluation should expose the benchmark version, metrics, cases, and configuration recorded by the backend.

---

# 25. Clean-Room Reproduction

A reviewer should be able to:

1. install backend dependencies
2. configure PostgreSQL
3. run database migrations
4. start FastAPI
5. install frontend dependencies
6. start Next.js
7. ingest a public or synthetic repository
8. create an analysis
9. execute the analysis
10. inspect findings
11. inspect evidence
12. inspect trajectory
13. run the benchmark evaluation

For Docker:

```powershell
docker compose up -d --build
```

Check services:

```powershell
docker compose ps
```

Check backend:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

View backend logs:

```powershell
docker compose logs -f backend
```

View PostgreSQL logs:

```powershell
docker compose logs -f postgres
```

Stop:

```powershell
docker compose down
```

Stop and remove persistent database data:

```powershell
docker compose down -v
```

**Warning:** `docker compose down -v` deletes the PostgreSQL and repository-storage volumes defined by the Compose project.

---

# 26. Deployment Checklist

## Backend

- [ ] Python 3.12 runtime is available
- [ ] `requirements.txt` installs successfully
- [ ] Git executable is installed in the runtime container
- [ ] PostgreSQL is reachable
- [ ] `DATABASE_URL` uses the correct hostname
- [ ] database migrations have been applied
- [ ] `/health` returns HTTP 200
- [ ] repository storage is persistent
- [ ] GitHub ingestion works
- [ ] ZIP ingestion works
- [ ] analysis creation works
- [ ] analysis execution works
- [ ] findings are generated
- [ ] evidence is generated
- [ ] evidence verification works
- [ ] trajectory is persisted
- [ ] failed analyses record failure information

## Frontend

- [ ] `NEXT_PUBLIC_API_URL` points to the real backend
- [ ] repository page loads
- [ ] analysis page loads
- [ ] findings page loads
- [ ] evidence loads
- [ ] evaluation page loads
- [ ] trajectory page loads
- [ ] trajectory requests contain a real analysis UUID
- [ ] no `/analyses/undefined/trajectory` requests occur
- [ ] production API URL is not localhost

## Security

- [ ] production database password is strong
- [ ] secrets are not committed
- [ ] `.env` is not committed
- [ ] CORS is restricted to the deployed frontend origin
- [ ] PostgreSQL is not unnecessarily exposed to the public Internet
- [ ] repository storage has sufficient disk space
- [ ] uploaded repositories are treated as untrusted input
- [ ] only approved/public/synthetic repositories are used for demonstrations
- [ ] application logs do not expose credentials

---

# 27. Recommended `.gitignore`

At minimum:

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Environment
.env
.env.*
!.env.example

# Test/cache
.pytest_cache/
.coverage
htmlcov/

# Node
node_modules/
.next/
out/

# Application storage
backend/storage/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

# 28. Environment Example

Commit an example file, not the real `.env`:

```dotenv
APP_NAME=RepoGuard Agent AI
DATABASE_URL=postgresql+psycopg://repoguard:CHANGE_ME@localhost:5432/repoguard
CORS_ORIGINS=http://localhost:3000
```

Production Docker Compose:

```dotenv
POSTGRES_PASSWORD=CHANGE_ME
```

Never commit:

```dotenv
POSTGRES_PASSWORD=<real password>
DATABASE_URL=<real production credentials>
```

---

# 29. Failure Handling

The analysis service explicitly handles failures.

A failed analysis records:

```text
status = failed
completed_at = timestamp
error_message = failure description
```

and adds:

```text
analysis_failed
```

to the trajectory.

This prevents failed runs from silently disappearing.

---

# 30. Engineering Decisions

## Explicit repository inspection

The agent workflow inspects the repository before running security rules.

This provides:

- workspace context
- file count
- supported source files

## Bounded security scanner

Security detection is isolated in:

```text
repoguard_security_scanner
```

The scanner returns structured candidate findings instead of directly mutating database state.

## Separate evidence stage

Detection and evidence collection are intentionally separated:

```text
Detection
   ↓
Evidence collection
   ↓
Verification
```

This makes the result easier to inspect.

## Persistent trajectory

Major execution stages are stored as database records so the workflow remains inspectable after execution.

## Human-reviewable output

The final workflow is:

```text
Agent performs first-pass analysis
             ↓
Evidence is attached
             ↓
Evidence is verified
             ↓
Human reviews the result
             ↓
Engineering decision
```

---

# 31. Improvement Changelog

## Baseline

Three deterministic rules:

```text
RG001
RG002
RG005
```

Reported benchmark:

```text
F1: 53.33%
Critical detection: 60%
Human time: 54 min
Cost: $54
```

## Iteration 1 — Rule expansion

Expanded coverage to:

```text
RG001–RG008
```

Added:

- hardcoded password detection
- hardcoded secret detection
- command execution detection
- unsafe HTML injection detection
- insecure HTTP detection

Reported result:

```text
F1: 100%
Critical detection: 100%
```

## Iteration 2 — Evidence

Added source-level evidence records and verification status.

Reported evidence support:

```text
100%
```

## Iteration 3 — Trajectory

Added persistent agent execution trajectory.

The workflow now exposes observable execution stages without exposing hidden chain-of-thought.

## Final integrated workflow

```text
Repository ingestion
+
Analysis run management
+
Repository inspection
+
8-rule scanner
+
Structured findings
+
Source evidence
+
Verification
+
Persistent trajectory
+
Benchmark evaluation
```

---

# 32. Limitations

RepoGuard is a deterministic pattern-based first-pass detector.

It does not replace:

- penetration testing
- comprehensive SAST
- dependency vulnerability databases
- runtime security testing
- threat modeling
- manual security review

Pattern-based detection can produce false negatives when dangerous behavior is expressed outside the implemented rules.

A detected pattern also does not automatically prove exploitability.

The correct interpretation is:

> **RepoGuard identifies security-relevant signals and provides evidence so a qualified reviewer can verify them.**

---

# 33. Safety

RepoGuard analyzes repositories and does not automatically modify or deploy analyzed source code.

Do not commit:

- passwords
- API keys
- tokens
- private credentials
- production database credentials
- private repository credentials

Use public, synthetic, or otherwise approved repositories for demonstrations and benchmark evaluation.

---

# 34. Frontend Views

The frontend is intended to provide:

```text
Audits
Repositories
Analysis
Findings
Evidence
Evaluation
Agent Trajectory
Changelog
```

The Agent Trajectory view consumes:

```http
GET /analyses/{analysis_id}/trajectory
```

and displays the persisted execution information.

---

# 35. Verification Commands

Backend unit tests:

```powershell
cd backend
pytest
```

Frontend build:

```powershell
cd frontend
npm run build
```

Frontend production start:

```powershell
npm run start
```

Backend health:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Docker status:

```powershell
docker compose ps
```

Docker backend logs:

```powershell
docker compose logs --tail=200 backend
```

---

# 36. Production Deployment Sequence

Recommended order:

```text
1. Configure production secrets
        ↓
2. Configure PostgreSQL
        ↓
3. Build backend image
        ↓
4. Start PostgreSQL
        ↓
5. Wait for PostgreSQL health
        ↓
6. Apply Alembic migrations
        ↓
7. Start backend
        ↓
8. Verify /health
        ↓
9. Deploy frontend
        ↓
10. Configure production API URL
        ↓
11. Configure CORS
        ↓
12. Run a smoke-test repository analysis
        ↓
13. Verify findings
        ↓
14. Verify evidence
        ↓
15. Verify trajectory
        ↓
16. Run benchmark evaluation
```

---

# 37. Minimal Smoke Test

After deployment:

### 1. Health

```http
GET /health
```

Expected:

```json
{
  "status": "ok",
  "service": "repoguard-agent-ai"
}
```

### 2. Repository

Ingest a small public or synthetic repository.

Confirm a `repository_id` is returned.

### 3. Analysis

Create:

```json
{
  "repository_id": "REAL_REPOSITORY_UUID",
  "agent_type": "repoguard-agent"
}
```

Confirm an `analysis_id` is returned.

### 4. Run

```http
POST /analyses/REAL_ANALYSIS_UUID/run
```

### 5. Findings

```http
GET /analyses/REAL_ANALYSIS_UUID/findings
```

### 6. Evidence

For each finding:

```http
GET /findings/REAL_FINDING_UUID/evidence
```

### 7. Trajectory

```http
GET /analyses/REAL_ANALYSIS_UUID/trajectory
```

Confirm the successful execution events are present.

---

# 38. What Success Looks Like

A successful end-to-end run should provide:

```text
Repository
    ✓ persisted

Analysis
    ✓ created
    ✓ executed
    ✓ completed

Findings
    ✓ generated
    ✓ linked to repository source

Evidence
    ✓ collected
    ✓ verified

Trajectory
    ✓ persisted
    ✓ visible in frontend

Evaluation
    ✓ benchmark executable
    ✓ metrics retrievable
```

---

# 39. Key Insight

## Evidence beats confidence.

A useful security-analysis system should not only produce a conclusion.

It should make the conclusion inspectable:

```text
Finding
+
Evidence
+
Execution context
+
Reproducible evaluation
```

For security workflows, this distinction matters because a reviewer must be able to understand and verify what happened.

The strongest contribution of RepoGuard is therefore not simply increasing rule count.

It is the combination of:

> **broader detection + evidence + observable execution + reproducible evaluation**

---

# 40. Submission Summary

## Problem

Developers and security reviewers need a faster and more consistent first-pass security review workflow for unfamiliar repositories.

## Bottleneck

Manual inspection requires repeatedly searching source files, identifying security-sensitive patterns, collecting evidence, and validating findings.

## Solution

RepoGuard provides:

- repository ingestion
- analysis run management
- deterministic security scanning
- structured findings
- source evidence
- verification
- persistent agent trajectory
- benchmark evaluation

## Reported measured result

```text
F1
53.33% → 100%

Critical detection
60% → 100%

Human time
54 min → 21 min

Cost
$54.00 → $21.20

Evidence-supported findings
100% → 100%
```

## Main contribution

> **An evidence-first, observable, reproducible repository security-analysis workflow.**

## Final principle

> **Find the risk. Show the evidence. Expose the execution. Measure the improvement.**

---

# 41. Final Pre-Deployment Gate

Do not consider a deployment complete until all of the following pass:

```text
[ ] PostgreSQL healthy
[ ] Database migrations applied
[ ] Backend starts
[ ] /health = 200
[ ] Git executable available to backend
[ ] Repository storage persistent
[ ] GitHub ingestion tested
[ ] ZIP ingestion tested
[ ] Analysis creation tested
[ ] Analysis execution tested
[ ] Findings tested
[ ] Evidence tested
[ ] Verification tested
[ ] Trajectory tested
[ ] Failure path tested
[ ] Evaluation tested
[ ] Frontend production build passes
[ ] Frontend points to production API
[ ] CORS configured for production frontend
[ ] Production secrets are outside source control
[ ] PostgreSQL is not publicly exposed unnecessarily
[ ] Smoke test completed
```

**RepoGuard is ready for deployment when this gate passes in the actual target environment.**
