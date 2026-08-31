# REPRODUCTION.md

# RepoGuard Agent AI — Reproduction Guide

This document explains how to reproduce the RepoGuard Agent AI system locally, ingest a repository, run an analysis, inspect findings and evidence, view the agent execution trajectory, and run the benchmark evaluation.

The goal is that an evaluator can start from a clean checkout and verify the main product workflow without relying on hidden steps.

---

## 1. What this guide reproduces

RepoGuard Agent AI is a repository-security analysis application with:

- Repository ingestion from ZIP upload
- GitHub repository ingestion by URL
- Persistent repository records
- Analysis-run creation and execution
- Deterministic security scanning
- Security findings with file/line locations
- Source-code evidence attached to findings
- Agent execution trajectory
- Evaluation/benchmark results
- A Next.js frontend for interacting with the backend

The core analysis workflow is:

```text
Repository
   ↓
Ingest repository
   ↓
Create analysis
   ↓
Run analysis
   ↓
Inspect repository workspace
   ↓
Run RepoGuard security rules
   ↓
Create findings
   ↓
Collect source evidence
   ↓
Complete analysis
   ↓
View trajectory + findings + evidence
```

---

# 2. Requirements

## Backend

Recommended environment:

- Python 3.11+
- Git
- PostgreSQL
- `pip`
- A virtual environment

## Frontend

Recommended environment:

- Node.js 18+
- npm

## Operating system

The application can be developed on Windows, macOS, or Linux.

The commands below use a Windows PowerShell style where useful because the reference development environment is Windows.

---

# 3. Expected project structure

The project should contain a backend and frontend similar to:

```text
repoguard-agent-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── storage/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── README.md
├── REPRODUCTION.md
└── IMPROVEMENT_CHANGELOG.md
```

The exact file list may vary slightly by environment.

---

# 4. Clone/open the project

If the project is already available locally, open its root directory.

Example:

```powershell
cd D:\repoguard-agent-ai
```

Confirm the project contains the backend and frontend:

```powershell
Get-ChildItem
```

Expected major directories:

```text
backend
frontend
```

---

# 5. Configure PostgreSQL

Create a PostgreSQL database for the application.

For example:

```text
Database: repoguard
User: postgres
Host: localhost
Port: 5432
```

The actual database name, username, password, and connection string should match the values configured by the project.

Set the backend database environment variable if the application expects one.

A typical example is:

```text
DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/repoguard
```

Do not commit real passwords or credentials to source control.

---

# 6. Backend setup

Open a terminal:

```powershell
cd D:\repoguard-agent-ai\backend
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the appropriate local execution-policy configuration or activate the environment using another supported shell.

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

# 7. Verify backend imports

From the `backend` directory:

```powershell
python -c "from app.main import app; print(app.title)"
```

Expected result:

```text
RepoGuard Agent AI
```

This verifies that the FastAPI application can be imported.

---

# 8. Start the backend

From:

```text
D:\repoguard-agent-ai\backend
```

run:

```powershell
uvicorn app.main:app --reload --port 8000
```

The API should become available at:

```text
http://localhost:8000
```

FastAPI documentation should be available at:

```text
http://localhost:8000/docs
```

---

# 9. Verify backend health

Run:

```powershell
Invoke-WebRequest http://localhost:8000/health
```

Or open the endpoint in a browser:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "repoguard-agent-ai"
}
```

The exact JSON may contain additional fields if the implementation has been extended.

---

# 10. Verify registered analysis routes

Because FastAPI's route table contains non-route entries such as included routers, do not inspect every `app.routes` item assuming it has a `.path` attribute.

Use:

```powershell
python -c "from app.main import app; print('\n'.join(f'{r.path} {sorted(r.methods)}' for r in app.routes if hasattr(r, 'path') and 'analys' in r.path))"
```

Expected analysis endpoints include routes equivalent to:

```text
POST /analyses
GET /analyses
GET /analyses/{analysis_id}
POST /analyses/{analysis_id}/run
GET /analyses/{analysis_id}/findings
GET /analyses/{analysis_id}/trajectory
```

The exact ordering printed by FastAPI is not important.

---

# 11. Backend API workflow

The reproducible workflow should be performed in this order:

```text
1. Ingest repository
2. Confirm repository ID
3. Create analysis using repository ID
4. Confirm analysis ID
5. Run analysis using analysis ID
6. Get analysis
7. Get findings
8. Get evidence for findings
9. Get trajectory
```

The most important relationship is:

```text
repository_id
      ↓
analysis_id
      ↓
trajectory / findings / evidence
```

Do not replace an actual ID with the literal string:

```text
undefined
```

---

# 12. Ingest a repository by ZIP

ZIP upload is one supported ingestion path.

Use the frontend repository upload workflow or the backend endpoint exposed for repository upload.

The backend endpoint is:

```text
POST /repositories/upload
```

It expects a multipart file upload.

Example with PowerShell/curl tooling may vary by Windows installation. The simplest reproducible method is to use the API documentation at:

```text
http://localhost:8000/docs
```

Select:

```text
POST /repositories/upload
```

Choose a ZIP file containing a repository and execute the request.

The response should contain a repository object including an `id`.

Save that ID.

Example:

```json
{
  "id": "REPOSITORY-UUID",
  ...
}
```

---

# 13. Ingest a GitHub repository

The backend also supports GitHub URL ingestion:

```text
POST /repositories/github
```

The request body is JSON:

```json
{
  "url": "https://github.com/OWNER/REPOSITORY"
}
```

Important:

Use the full repository URL.

Correct:

```text
https://github.com/RellIGaming/REPOSITORY
```

Incorrect:

```text
https://github.com/RellIGaming
```

The second value points to a GitHub user/organization rather than a repository and can produce:

```text
git clone ... remote: Not Found
fatal: repository ... not found
```

For a private repository, authentication/permissions must also be configured appropriately.

---

# 14. Confirm repository ingestion

After ingestion, retrieve the repository:

```text
GET /repositories/{repository_id}
```

Confirm that the repository has a usable workspace.

The analysis service requires a repository workspace before analysis can be created.

A repository without a workspace should not be treated as successfully ingested.

---

# 15. Create an analysis

Use:

```text
POST /analyses
```

The request should reference the repository ID.

Conceptually:

```json
{
  "repository_id": "REPOSITORY-UUID",
  "agent_type": "repoguard-agent"
}
```

The service creates an `AnalysisRun`.

A successful response should contain an analysis ID.

Example:

```json
{
  "id": "ANALYSIS-UUID",
  "repository_id": "REPOSITORY-UUID",
  "status": "queued",
  "agent_type": "repoguard-agent",
  "commit_sha": "...",
  ...
}
```

Save the returned analysis ID.

---

# 16. Run the analysis

Execute:

```text
POST /analyses/{analysis_id}/run
```

Replace `{analysis_id}` with the real UUID.

Example:

```text
POST /analyses/e4309a38-1b94-49a2-b677-65f5de8a24b5/run
```

The analysis service performs the following stages:

1. Mark analysis as running
2. Record trajectory step 1
3. Inspect repository
4. Record repository inspection
5. Start security scan
6. Scan supported source files
7. Generate findings
8. Collect evidence
9. Mark analysis completed
10. Record completion trajectory

If an exception occurs, the analysis is marked failed and an `analysis_failed` trajectory event is recorded.

---

# 17. Supported source files

The deterministic scanner currently supports:

```text
.py
.js
.jsx
.ts
.tsx
```

It ignores common generated/dependency directories such as:

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

This prevents dependency and generated output from being treated as normal source input.

---

# 18. Security rules

The current scanner contains eight RepoGuard rules:

| Rule | Severity | Purpose |
|---|---|---|
| RG001 | High | Potential Python `eval()` |
| RG002 | High | Potential Python `exec()` |
| RG003 | Medium | Hardcoded password |
| RG004 | Medium | Hardcoded secret |
| RG005 | High | Potential JavaScript/TypeScript `eval()` |
| RG006 | High | Potential command execution via `child_process` |
| RG007 | High | Potential unsafe HTML injection through `dangerouslySetInnerHTML` |
| RG008 | Medium | Insecure `http://` URL |

The scanner records the matching file and line.

---

# 19. Reproduce a finding

To make a simple reproducible test case, create a supported source file.

For example:

```python
# reproduction_eval.py

user_input = "1 + 1"
result = eval(user_input)
print(result)
```

The scanner should detect the:

```text
RG001
```

rule.

A JavaScript example:

```javascript
// reproduction_js.js

const value = eval(userInput);
console.log(value);
```

should trigger:

```text
RG005
```

A command execution example:

```javascript
const child_process = require("child_process");
```

should trigger:

```text
RG006
```

An unsafe HTML example:

```jsx
<div dangerouslySetInnerHTML={{ __html: content }} />
```

should trigger:

```text
RG007
```

---

# 20. Get analysis details

After running an analysis:

```text
GET /analyses/{analysis_id}
```

A completed analysis should report a status similar to:

```json
{
  "status": "completed"
}
```

The response may also contain:

```text
repository_id
agent_type
commit_sha
started_at
completed_at
error_message
created_at
```

---

# 21. Get findings

Use:

```text
GET /analyses/{analysis_id}/findings
```

The result should contain findings generated by the scanner.

A finding should identify information such as:

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

The exact response schema is defined by the backend finding schema.

---

# 22. Get evidence

Findings have associated source evidence.

Use:

```text
GET /findings/{finding_id}/evidence
```

Evidence should identify the relevant source location and content.

The scanner currently creates evidence with:

```text
evidence_type = source_code
verification_status = verified
```

and records:

```text
file_path
line_start
line_end
content
```

This is important for the evidence-first security-report workflow.

---

# 23. Get agent trajectory

The trajectory endpoint is:

```text
GET /analyses/{analysis_id}/trajectory
```

This must use the real analysis UUID.

Correct:

```text
GET /analyses/e4309a38-1b94-49a2-b677-65f5de8a24b5/trajectory
```

Incorrect:

```text
GET /analyses/undefined/trajectory
```

The latter causes FastAPI validation to reject the request with:

```text
422 Unprocessable Content
```

because `undefined` is not a valid UUID.

---

# 24. Expected trajectory

A successful analysis should record seven primary steps similar to:

```text
1: analysis_started
2: repository_inspection_started
3: repository_inspected
4: security_scan_started
5: findings_generated
6: evidence_collected
7: analysis_completed
```

Example observations:

```text
RepoGuard agent analysis started.

Agent is inspecting the repository workspace.

Repository inspection completed. X files found, including Y supported source files.

Agent started deterministic security analysis across supported source files.

Security analysis generated N finding(s).

Source evidence was collected for N finding(s).

RepoGuard agent completed the analysis successfully.
```

The trajectory is intentionally user-facing execution information rather than hidden chain-of-thought.

It can contain:

```text
event type
tool name
input data
output data
observation
timestamp
step number
```

---

# 25. Verify trajectory directly from PostgreSQL

For a backend-level verification, the project can inspect persisted trajectory rows.

Example:

```powershell
python -c "from app.db.database import SessionLocal; from app.models.agent_trajectory import AgentTrajectory; db=SessionLocal(); rows=db.query(AgentTrajectory).order_by(AgentTrajectory.created_at.desc()).limit(20).all(); print('\n'.join(f'{r.step_number}: {r.event_type} | {r.tool_name} | {r.observation}' for r in reversed(rows))); db.close()"
```

For one analysis only, filter by its UUID:

```powershell
python -c "from app.db.database import SessionLocal; from app.models.agent_trajectory import AgentTrajectory; db=SessionLocal(); analysis_id='ANALYSIS-UUID'; rows=db.query(AgentTrajectory).filter(AgentTrajectory.analysis_run_id==analysis_id).order_by(AgentTrajectory.step_number.asc()).all(); print('\n'.join(f'{r.step_number}: {r.event_type} | {r.tool_name} | {r.observation}' for r in rows)); db.close()"
```

Expected successful sequence:

```text
1: analysis_started
2: repository_inspection_started
3: repository_inspected
4: security_scan_started
5: findings_generated
6: evidence_collected
7: analysis_completed
```

---

# 26. Frontend setup

Open another terminal:

```powershell
cd D:\repoguard-agent-ai\frontend
```

Install dependencies:

```powershell
npm install
```

Configure the backend URL if the frontend uses environment variables.

Typical value:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If demo mode is configurable, use the project's environment configuration to disable demo behavior when validating the live backend.

For example:

```text
NEXT_PUBLIC_DEMO_MODE=false
```

The exact environment-file convention should match the existing frontend configuration.

---

# 27. Start the frontend

From:

```text
D:\repoguard-agent-ai\frontend
```

run:

```powershell
npm run dev
```

The Next.js frontend should normally become available at:

```text
http://localhost:3000
```

The frontend communicates with:

```text
http://localhost:8000
```

when configured with the backend API URL above.

---

# 28. Frontend trajectory page

The frontend contains an analysis-specific trajectory route:

```text
/trajectories/{analysisId}
```

The trajectory page should load:

```text
GET /analyses/{analysisId}/trajectory
```

The page should display:

- Agent Trajectory heading
- Analysis ID
- Number of execution steps
- Duration
- Step number
- Event type
- Timestamp
- Observation
- Tool name where available
- Input where available
- Output where available

A successful run should display the seven-step execution trace.

---

# 29. Important frontend routing rule

The frontend must not call:

```text
/analyses/undefined/trajectory
```

If the browser developer console shows:

```text
GET /analyses/undefined/trajectory
422
```

the problem is not the trajectory backend implementation.

It means the frontend page was opened without a valid `analysisId`, or a navigation link is passing the wrong parameter.

Use the analysis-specific route:

```text
/trajectories/<REAL_ANALYSIS_UUID>
```

For example:

```text
/trajectories/e4309a38-1b94-49a2-b677-65f5de8a24b5
```

---

# 30. API client trajectory method

The frontend API client should call:

```typescript
async getTrajectories(analysisId: string): Promise<Trajectory[]> {
  return request<Trajectory[]>(
    `/analyses/${analysisId}/trajectory`
  );
}
```

The important requirement is that `analysisId` must be the actual route parameter.

Do not silently substitute:

```text
undefined
```

or an empty string.

---

# 31. Frontend trajectory data model

The backend trajectory response uses fields equivalent to:

```typescript
type Trajectory = {
  id: string;
  analysis_run_id: string;
  step_number: number;
  event_type: string;
  tool_name: string | null;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  observation: string | null;
  created_at: string;
};
```

The frontend should render the backend field names directly or through a clearly defined mapping layer.

---

# 32. Run the evaluation benchmark

The backend exposes:

```text
POST /evaluations/run
```

Run it from the FastAPI documentation:

```text
http://localhost:8000/docs
```

or through the frontend evaluation workflow.

A successful evaluation returns an evaluation ID.

Then retrieve:

```text
GET /evaluations/{evaluation_id}
```

The detailed response contains:

```text
evaluation summary
metrics
cases
```

---

# 33. Evaluation response verification

A completed benchmark response should contain fields similar to:

```json
{
  "status": "completed",
  "benchmark_version": "v1",
  "primary_metric": "f1"
}
```

The detailed response should include metric records such as:

```text
human_time
false_positives
cost_per_task
critical_detection
evidence_supported
primary_outcome
```

and benchmark cases.

---

# 34. Reference benchmark result

A successful reference run produced:

```text
Status: completed
Benchmark version: v1
Primary metric: f1

Baseline overall: 53.33
Advanced overall: 100

Human time baseline: 54
Human time advanced: 21

Cost baseline: 54
Cost advanced: 21.2
```

Configuration from that run:

```text
case_count: 10

baseline:
three-rule deterministic detector (RG001, RG002, RG005)

advanced:
full RepoGuard rule detector (RG001-RG008)

human_review_rate_per_hour:
60

agent_compute_cost_per_case:
0.02
```

These values are a reference recorded evaluation result, not a guarantee that every future run will produce identical values if the benchmark data or implementation changes.

---

# 35. Reference metric result

The reference evaluation contained:

| Metric | Baseline | Advanced | Direction |
|---|---:|---:|---|
| Human time per task | 5.4 min | 2.1 min | Lower is better |
| False positives | 0% | 0% | Lower is better |
| Cost per task | $5.40 | $2.12 | Lower is better |
| Critical issue detection | 60% | 100% | Higher is better |
| Evidence-supported findings | 100% | 100% | Higher is better |
| Primary outcome | 53.33% | 100% | Higher is better |

The reference run therefore demonstrates:

```text
Primary outcome: 53.33% → 100%
Critical detection: 60% → 100%
Human time: 5.4 min → 2.1 min per task
Cost: $5.40 → $2.12 per task
Evidence-supported findings: 100% → 100%
False positives: 0% → 0%
```

---

# 36. Verify evaluation cases

The detailed evaluation endpoint should expose benchmark cases.

A case contains information equivalent to:

```text
case_id
case_name
description
status
baseline_score
advanced_score
improvement
baseline_tp
baseline_fp
baseline_fn
advanced_tp
advanced_fp
advanced_fn
expected_rules
baseline_rules
advanced_rules
created_at
```

The reference benchmark included ten cases.

The advanced detector was configured to use all eight RepoGuard rules.

---

# 37. Useful direct API checks

After the backend is running, verify these endpoints:

```text
GET  /health

GET  /repositories
GET  /repositories/{repository_id}

POST /repositories/upload
POST /repositories/github

GET  /analyses
POST /analyses
GET  /analyses/{analysis_id}
POST /analyses/{analysis_id}/run

GET /analyses/{analysis_id}/findings
GET /findings/{finding_id}/evidence

GET /analyses/{analysis_id}/trajectory

GET  /evaluations
POST /evaluations/run
GET  /evaluations/{evaluation_id}
GET  /evaluations/{evaluation_id}/cases
GET  /evaluations/{evaluation_id}/metrics
```

The final route list should be confirmed against the running FastAPI application because routes can evolve.

---

# 38. Common failure: 404 on POST /analyses

If the server logs:

```text
POST /analyses HTTP/1.1" 404 Not Found
```

check that the analysis router is included in `app.main`.

The FastAPI application should include the analysis router:

```python
app.include_router(analysis_router)
```

Also confirm the analysis router defines:

```text
POST /analyses
```

Restart Uvicorn after changing backend code.

---

# 39. Common failure: 404 on evaluation detail

If:

```text
GET /evaluations/{id}
```

returns 404, first confirm that the evaluation ID actually exists.

The route should return:

```text
404 Evaluation not found
```

when the UUID is valid but no evaluation exists.

Do not confuse this with an invalid route.

---

# 40. Common failure: 422 on trajectory

If the server logs:

```text
GET /analyses/undefined/trajectory HTTP/1.1" 422
```

the frontend has passed an invalid analysis ID.

Fix the frontend navigation/route parameter.

Use:

```text
/trajectories/<analysisId>
```

where `<analysisId>` is the real UUID returned by:

```text
POST /analyses
```

Do not modify the backend UUID parameter to accept `"undefined"`.

---

# 41. Common failure: empty repository scan

A trajectory can report:

```text
Repository inspection completed. 0 files found, including 0 supported source files.
```

while a previous run may have generated findings.

This means the specific analysis inspected an empty or incorrect workspace.

Verify:

1. The repository ingestion completed successfully.
2. `Repository.workspace_path` points to the expected directory.
3. The directory exists.
4. The repository actually contains supported source files.
5. The analysis references the correct repository.
6. Generated/dependency directories are not the only contents.

Run:

```powershell
Get-ChildItem <workspace> -Recurse -File
```

to inspect the workspace.

---

# 42. Common failure: GitHub ingestion returns 404

If Git reports:

```text
remote: Not Found
fatal: repository ... not found
```

verify the URL.

For example:

```text
https://github.com/RellIGaming
```

is not a repository URL by itself.

Use:

```text
https://github.com/RellIGaming/<repository-name>
```

Also verify:

- repository exists
- repository is accessible
- URL is correct
- authentication is configured if private
- Git is installed and available on PATH

---

# 43. Common failure: CORS

The backend enables CORS for the frontend development origin:

```text
http://localhost:3000
```

If the frontend runs on another origin, update the backend CORS configuration accordingly.

After changing CORS configuration, restart the backend.

---

# 44. Common failure: frontend API URL

If browser requests are going to the wrong backend, verify:

```text
NEXT_PUBLIC_API_URL
```

The development value should normally point to:

```text
http://localhost:8000
```

Restart the Next.js development server after changing environment variables.

---

# 45. End-to-end verification checklist

Use this checklist for a final reproduction.

## Backend

- [ ] PostgreSQL is running
- [ ] Python environment is active
- [ ] Backend dependencies installed
- [ ] `python -c "from app.main import app; print(app.title)"` succeeds
- [ ] Uvicorn starts without import errors
- [ ] `/health` returns HTTP 200
- [ ] `/docs` loads

## Repository

- [ ] ZIP upload works
- [ ] GitHub repository ingestion works
- [ ] Repository receives an ID
- [ ] Repository has a valid workspace
- [ ] Repository details can be retrieved

## Analysis

- [ ] `POST /analyses` returns 201
- [ ] Analysis receives an ID
- [ ] Analysis starts successfully
- [ ] Analysis reaches `completed`
- [ ] Findings are persisted
- [ ] Evidence is persisted

## Trajectory

- [ ] `/analyses/{analysis_id}/trajectory` returns 200
- [ ] Real UUID is passed
- [ ] No `/undefined/trajectory` request occurs
- [ ] Seven primary execution steps are visible
- [ ] Tool names are displayed where present
- [ ] Inputs/outputs are displayed where present
- [ ] Hidden chain-of-thought is not displayed

## Evaluation

- [ ] `POST /evaluations/run` succeeds
- [ ] Evaluation status is `completed`
- [ ] Detail endpoint returns metrics
- [ ] Detail endpoint returns cases
- [ ] Baseline and advanced results are visible
- [ ] Reference benchmark can be explained

## Frontend

- [ ] `npm install` succeeds
- [ ] Next.js starts
- [ ] Frontend reaches backend
- [ ] Repository workflow works
- [ ] Analysis workflow works
- [ ] Findings page works
- [ ] Evidence page works
- [ ] Trajectory page works
- [ ] Evaluation page works

---

# 46. Minimal evaluator path

If an evaluator has limited time, the shortest meaningful reproduction is:

### Step 1

Start PostgreSQL.

### Step 2

Start backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

### Step 3

Verify:

```text
http://localhost:8000/health
```

### Step 4

Open:

```text
http://localhost:8000/docs
```

### Step 5

Upload a repository through:

```text
POST /repositories/upload
```

### Step 6

Create an analysis using the returned repository ID:

```text
POST /analyses
```

### Step 7

Run it:

```text
POST /analyses/{analysis_id}/run
```

### Step 8

Inspect:

```text
GET /analyses/{analysis_id}
GET /analyses/{analysis_id}/findings
GET /analyses/{analysis_id}/trajectory
```

### Step 9

For a finding, inspect:

```text
GET /findings/{finding_id}/evidence
```

### Step 10

Run the benchmark:

```text
POST /evaluations/run
```

Then inspect:

```text
GET /evaluations/{evaluation_id}
```

This path verifies the central product story end-to-end.

---

# 47. Evidence of reproducibility

A successful reproduction should leave persistent database records for:

```text
repository
analysis_run
finding
evidence
agent_trajectory
evaluation
evaluation_metric
evaluation_case
```

The analysis trajectory provides an additional audit trail for the execution.

A reviewer can therefore verify not only the final finding but also the sequence of user-facing execution events that produced it.

---

# 48. Reproducibility principle

The system should be evaluated using actual API responses and persisted data rather than screenshots alone.

The most useful evidence is:

```text
API request
    ↓
HTTP response
    ↓
database record
    ↓
frontend presentation
```

For example:

```text
POST /analyses
        ↓
analysis UUID
        ↓
POST /analyses/{id}/run
        ↓
completed analysis
        ↓
GET /analyses/{id}/findings
        ↓
GET /findings/{finding_id}/evidence
        ↓
GET /analyses/{id}/trajectory
```

This makes the workflow independently inspectable.

---

# 49. Reference successful trajectory

A reference successful analysis produced:

```text
1: analysis_started | None
   RepoGuard agent analysis started.

2: repository_inspection_started | filesystem_scanner
   Agent is inspecting the repository workspace.

3: repository_inspected | filesystem_scanner
   Repository inspection completed.

4: security_scan_started | repoguard_security_scanner
   Agent started deterministic security analysis across supported source files.

5: findings_generated | repoguard_security_scanner
   Security analysis generated finding(s).

6: evidence_collected | source_evidence_collector
   Source evidence was collected for finding(s).

7: analysis_completed | None
   RepoGuard agent completed the analysis successfully.
```

The exact finding count depends on the repository being analyzed.

---

# 50. Reference successful evaluation

The recorded reference evaluation was:

```text
Evaluation ID:
e4309a38-1b94-49a2-b677-65f5de8a24b5

Status:
completed

Benchmark:
v1

Primary metric:
f1

Baseline overall:
53.33

Advanced overall:
100
```

Reference metrics:

```text
Human time:
5.4 min/task → 2.1 min/task

False positives:
0% → 0%

Cost:
$5.40/task → $2.12/task

Critical detection:
60% → 100%

Evidence-supported:
100% → 100%

Primary outcome:
53.33% → 100%
```

---

# 51. What counts as a successful reproduction

A reproduction is considered successful when the evaluator can independently verify:

1. The backend starts.
2. The health endpoint responds.
3. A repository can be ingested.
4. An analysis can be created.
5. The analysis can be executed.
6. Security findings can be generated.
7. Evidence is attached to findings.
8. The execution trajectory is persisted and returned through the API.
9. The frontend can display the trajectory using a real analysis ID.
10. The benchmark evaluation can be executed and inspected.
11. The documented reference results can be explained from the application data.

---

# 52. Final evaluator command set

For a quick backend sanity check:

```powershell
cd D:\repoguard-agent-ai\backend
.\.venv\Scripts\Activate.ps1
python -c "from app.main import app; print(app.title)"
uvicorn app.main:app --reload --port 8000
```

Then open:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

For frontend:

```powershell
cd D:\repoguard-agent-ai\frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

---

# 53. Final notes

- Use real UUIDs returned by the API.
- Do not call `/analyses/undefined/...`.
- Use complete GitHub repository URLs.
- Keep backend and frontend running on their configured ports.
- Do not commit credentials.
- Use `/docs` as the authoritative interactive API surface for the currently running backend.
- Use the database records and API responses as the primary reproducibility evidence.
- The deterministic scanner is intentionally simple and pattern-based; this guide documents the implemented behavior rather than claiming broader semantic security analysis than the current implementation provides.

---

# 54. Reproduction summary

```text
START
  │
  ├── PostgreSQL
  │
  ├── FastAPI backend :8000
  │
  ├── Next.js frontend :3000
  │
  ├── Repository ingestion
  │      ├── ZIP
  │      └── GitHub URL
  │
  ├── POST /analyses
  │
  ├── POST /analyses/{id}/run
  │
  ├── Security rules RG001-RG008
  │
  ├── Findings
  │
  ├── Evidence
  │
  ├── Agent trajectory
  │      └── 7 primary steps
  │
  └── Evaluation
         ├── baseline
         └── advanced

END
```

The complete workflow is therefore reproducible from repository ingestion through analysis, evidence, trajectory, frontend presentation, and benchmark evaluation.
