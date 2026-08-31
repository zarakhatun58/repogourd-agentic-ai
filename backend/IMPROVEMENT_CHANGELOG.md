# Improvement Changelog

This document records the major improvements made to RepoGuard Agent AI from the initial deterministic prototype to the current evidence-first, agent-trajectory-enabled security analysis system.

The purpose is to make the improvement process reproducible and easy for an evaluator to verify. Each change explains what was improved, why it matters to the user, and how the result can be demonstrated.

---

## 1. Executive Summary

RepoGuard Agent AI was improved in several connected areas:

- repository ingestion was made usable for both ZIP uploads and GitHub URLs;
- repository analysis became a persisted analysis-run workflow;
- security detection was expanded from a small baseline rule set to a broader RG001-RG008 rule set;
- findings were linked to source-code evidence;
- agent execution trajectory was persisted and exposed through an API;
- the frontend was connected to the trajectory API and now displays the seven execution steps;
- evaluation became a persisted benchmark with case-level and metric-level results;
- API responses were aligned with the frontend data model;
- error handling and route verification were strengthened;
- documentation was expanded with a clear problem/value story, endpoint documentation, reproducibility instructions, and this improvement changelog.

The current implementation demonstrates a complete path:

**Repository → Analysis → Agent trajectory → Security findings → Evidence → Evaluation → User-facing report**

---

# 2. Before vs. After

| Area | Earlier State | Improved State |
|---|---|---|
| Repository input | ZIP workflow available; GitHub URL ingestion initially failed for malformed URLs | ZIP and GitHub ingestion supported; GitHub URL handling was corrected and verified |
| Analysis | Basic analysis workflow | Persisted analysis runs with queued/running/completed/failed states |
| Detection | Three-rule baseline concept | Full deterministic RG001-RG008 detector |
| Findings | Detection output | Persisted findings with severity, rule ID, location, and status |
| Evidence | Limited evidence representation | Source-code evidence linked to findings and marked verified |
| Agent transparency | No complete persisted execution trace | Seven-step persisted agent trajectory |
| Trajectory API | Backend support existed but frontend integration was incomplete | API exposed and frontend route connected |
| Trajectory UI | Frontend requested `/undefined/trajectory` | Dynamic `/trajectories/[analysisId]` page displays real API data |
| Evaluation | Prototype benchmark | Persisted evaluation, metrics, and per-case results |
| API documentation | Limited | Endpoint-by-endpoint API documentation |
| Reproducibility | Scattered setup information | Dedicated reproducibility documentation |
| Improvement evidence | Not centrally documented | This changelog + evaluation output |

---

# 3. Repository Ingestion Improvements

## 3.1 ZIP Upload

### Improvement

Repository ZIP upload was implemented and verified as a working ingestion path.

### User value

A user can provide a local repository without configuring GitHub authentication or exposing a public URL.

### Result

The uploaded repository is extracted into the backend repository workspace and can subsequently be analyzed by RepoGuard.

---

## 3.2 GitHub URL Ingestion

### Initial problem

GitHub ingestion returned a `400 Bad Request` because an incomplete URL such as:

`https://github.com/RellIGaming`

was being interpreted as a repository clone target.

Git returned:

`remote: Not Found`

### Improvement

The GitHub repository URL handling was corrected so that a valid repository URL can be passed to the ingestion endpoint.

### Verification

The GitHub ingestion workflow was subsequently confirmed as working.

### User value

Users can provide a GitHub repository URL rather than manually downloading and uploading a ZIP archive.

---

# 4. Analysis Workflow Improvements

## 4.1 Persisted Analysis Runs

Analysis runs are represented by the `AnalysisRun` model.

Important persisted fields include:

- `id`
- `repository_id`
- `status`
- `agent_type`
- `commit_sha`
- `started_at`
- `completed_at`
- `error_message`
- `created_at`

### Improvement

The workflow now represents analysis as an explicit lifecycle instead of an untracked scanner execution.

Typical states include:

- `queued`
- `running`
- `completed`
- `failed`

### User value

Users can identify a specific analysis, inspect its state, and connect findings and trajectory information to that run.

---

# 5. Security Detection Improvements

## 5.1 Baseline Detector

The benchmark baseline uses a three-rule deterministic detector:

- RG001
- RG002
- RG005

This provides a deliberately smaller comparison point.

---

## 5.2 Full RepoGuard Detector

The advanced detector expanded coverage to RG001-RG008.

### RG001 — Python dynamic execution

Detects potential `eval()` use in Python source.

### RG002 — Python command execution

Detects potential `exec()` use in Python source.

### RG003 — Hardcoded password

Detects a possible `password =` assignment in supported source files.

### RG004 — Hardcoded secret

Detects a possible `secret =` assignment in supported source files.

### RG005 — JavaScript dynamic execution

Detects potential JavaScript/TypeScript `eval()` use.

### RG006 — Command execution

Detects potential use of `child_process` APIs.

### RG007 — Unsafe HTML injection

Detects `dangerouslySetInnerHTML`.

### RG008 — Insecure HTTP URL

Detects `http://` URLs in supported JavaScript/TypeScript source.

### User value

The broader rule set improves coverage beyond the original three-rule baseline and makes the advanced detector useful across multiple common application-security patterns.

---

# 6. Supported Source Languages

The scanner supports:

- Python
- JavaScript
- TypeScript
- JSX
- TSX

Supported extensions:

- `.py`
- `.js`
- `.jsx`
- `.ts`
- `.tsx`

### Repository filtering

The scanner ignores common generated, dependency, cache, and version-control directories, including:

- `.git`
- `node_modules`
- `.venv`
- `venv`
- `__pycache__`
- `.pytest_cache`
- `dist`
- `build`
- `.next`
- `coverage`

### User value

The scanner focuses on relevant source files and avoids wasting analysis effort on common dependency and build directories.

---

# 7. Findings Improvements

Each detected issue is persisted as a `Finding`.

A finding records information such as:

- analysis run
- rule ID
- severity
- title
- description
- file path
- starting line
- ending line
- status

### Improvement

The system moved from simply identifying a pattern to creating a structured security finding that can be displayed, queried, and connected to evidence.

### User value

A security result becomes actionable rather than being just a raw scanner message.

---

# 8. Evidence-First Improvements

## 8.1 Source Evidence

For each generated finding, RepoGuard creates an `Evidence` record containing:

- finding ID
- evidence type
- source file path
- line range
- source-code content
- verification status

The current scanner uses:

`evidence_type = "source_code"`

and marks generated source evidence as:

`verification_status = "verified"`

### User value

A user can see exactly where the reported issue came from instead of receiving an unsupported security claim.

---

## 8.2 Evidence Association

The analysis workflow counts collected evidence and records that information in the agent trajectory.

Example trajectory output:

- findings generated
- evidence collected
- verified evidence count

### Improvement

The workflow explicitly connects:

**Finding → Source location → Evidence**

This supports the evidence-first reporting goal.

---

# 9. Agent Trajectory Improvements

## 9.1 Persisted Trajectory Model

Agent execution steps are persisted in the `agent_trajectories` table.

Each trajectory record contains:

- `analysis_run_id`
- `step_number`
- `event_type`
- `tool_name`
- `input_data`
- `output_data`
- `observation`
- `created_at`

---

## 9.2 Seven-Step Execution Trace

The current analysis workflow records seven user-facing execution steps.

### Step 1 — Analysis started

Event:

`analysis_started`

Observation:

`RepoGuard agent analysis started.`

---

### Step 2 — Repository inspection started

Event:

`repository_inspection_started`

Tool:

`filesystem_scanner`

The agent records that it is inspecting the repository workspace.

---

### Step 3 — Repository inspected

Event:

`repository_inspected`

Tool:

`filesystem_scanner`

The output includes:

- total file count
- supported source-file count
- supported extensions

---

### Step 4 — Security scan started

Event:

`security_scan_started`

Tool:

`repoguard_security_scanner`

The output identifies the supported languages and rule count.

---

### Step 5 — Findings generated

Event:

`findings_generated`

Tool:

`repoguard_security_scanner`

The output contains the number of generated findings.

---

### Step 6 — Evidence collected

Event:

`evidence_collected`

Tool:

`source_evidence_collector`

The output contains:

- evidence count
- verified evidence count

---

### Step 7 — Analysis completed

Event:

`analysis_completed`

The output contains:

- findings count
- evidence count
- final analysis status

---

## 9.3 Failure Trajectory

When execution fails, the workflow records a failure trajectory event:

`analysis_failed`

with:

- failed status
- error message
- failure observation

### User value

The trajectory makes execution understandable without exposing hidden chain-of-thought.

The frontend intentionally displays user-facing execution information such as:

- tools
- observations
- inputs
- outputs
- analysis decisions

It does not display hidden chain-of-thought.

---

# 10. Agent Trajectory API Improvement

The backend exposes the analysis trajectory through:

`GET /analyses/{analysis_id}/trajectory`

### Improvement

The API already existed on the backend, but the frontend initially did not provide the correct dynamic route integration.

The frontend API client now calls:

`/analyses/${analysisId}/trajectory`

### User value

The UI can retrieve the real persisted trajectory for a specific analysis instead of relying only on demo data.

---

# 11. Frontend Trajectory Routing Fix

## 11.1 Initial Problem

The frontend requested:

`GET /analyses/undefined/trajectory`

The backend correctly rejected the request with:

`422 Unprocessable Content`

because `undefined` is not a valid UUID.

---

## 11.2 Root Cause

The trajectory page was expecting:

`analysisId`

but the frontend route structure did not initially provide that dynamic parameter.

---

## 11.3 Improvement

A dynamic route was added:

`app/trajectories/[analysisId]/page.tsx`

The existing static page:

`app/trajectories/page.tsx`

was retained as the non-specific entry point.

The dynamic page receives the actual analysis ID and passes it to:

`api.getTrajectories(analysisId)`

---

## 11.4 Result

The trajectory page now successfully loads the real backend trajectory and displays the seven analysis execution steps.

### User value

A user can inspect the execution history for a specific analysis instead of seeing a loading state followed by an API validation error.

---

# 12. Frontend Trajectory UI Improvements

The trajectory UI now provides:

- step number
- event type
- timestamp
- observation
- tool name
- JSON input
- JSON output
- execution duration
- loading state
- error state
- empty state
- navigation back to audits

The UI also uses different icons and visual treatments for common event types.

### User value

The execution trace is understandable at a glance while still allowing technical details to be inspected.

---

# 13. Evaluation Improvements

## 13.1 Persisted Evaluation

The evaluation workflow now persists an evaluation with:

- evaluation ID
- status
- benchmark version
- primary metric
- baseline overall result
- advanced overall result
- human time
- cost
- configuration
- creation time

---

## 13.2 Evaluation Metrics

The current benchmark records metrics including:

- human time
- false positives
- cost per task
- critical issue detection
- evidence-supported findings
- primary outcome

Each metric contains:

- key
- label
- unit
- baseline value
- advanced value
- whether higher is better
- creation time

---

## 13.3 Case-Level Evaluation

The evaluation also stores per-case results including:

- case ID
- case name
- description
- baseline score
- advanced score
- improvement
- baseline TP
- baseline FP
- baseline FN
- advanced TP
- advanced FP
- advanced FN
- expected rules
- baseline rules
- advanced rules

### User value

The benchmark is not only an overall percentage. It provides evidence of exactly which cases improved and why.

---

# 14. Benchmark Result Improvement

A verified evaluation run produced the following overall result:

| Metric | Baseline | Advanced |
|---|---:|---:|
| Primary F1 outcome | 53.33% | 100% |
| Critical issue detection | 60% | 100% |
| Evidence-supported findings | 100% | 100% |
| Human time per task | 5.4 min | 2.1 min |
| Cost per task | $5.40 | $2.12 |
| False positives | 0% | 0% |

The benchmark configuration recorded:

- 10 cases
- baseline: three-rule deterministic detector `(RG001, RG002, RG005)`
- advanced: full RepoGuard rule detector `(RG001-RG008)`
- human review rate: 60 per hour
- agent compute cost: $0.02 per case

### Interpretation

The benchmark demonstrates a large improvement in primary detection performance while preserving evidence support and zero measured false positives in the benchmark.

Human time also decreased substantially in the benchmark.

---

# 15. API Improvements

The backend API surface now covers the major product workflows.

Important endpoints include:

## Health

`GET /health`

Checks whether the service is available.

---

## Repository APIs

`GET /repositories`

Lists repositories.

`GET /repositories/{repository_id}`

Returns a repository.

`POST /repositories/upload`

Uploads a repository ZIP.

`POST /repositories/github`

Ingests a GitHub repository.

---

## Analysis APIs

`GET /analyses`

Lists analysis runs.

`POST /analyses`

Creates an analysis.

`GET /analyses/{analysis_id}`

Returns an analysis.

`POST /analyses/{analysis_id}/run`

Executes an analysis.

`GET /analyses/{analysis_id}/findings`

Returns findings for an analysis.

`GET /analyses/{analysis_id}/trajectory`

Returns the persisted agent trajectory.

---

## Finding APIs

`GET /findings/{finding_id}/evidence`

Returns evidence associated with a finding.

---

## Evaluation APIs

`GET /evaluations`

Lists evaluations.

`POST /evaluations/run`

Runs the benchmark evaluation.

`GET /evaluations/{evaluation_id}`

Returns detailed evaluation results.

`GET /evaluations/{evaluation_id}/cases`

Returns evaluation cases.

`GET /evaluations/{evaluation_id}/metrics`

Returns evaluation metrics.

---

# 16. Error Handling Improvements

The API uses appropriate HTTP responses for common failure conditions.

Examples include:

- `404 Not Found` when an analysis/evaluation/repository does not exist;
- `422 Unprocessable Content` when a path parameter cannot be validated, such as `undefined` instead of a UUID;
- `400 Bad Request` for invalid ingestion input;
- `500 Internal Server Error` for unexpected evaluation failures.

### Improvement

Errors are now easier to diagnose because the backend provides meaningful exception details while the frontend displays loading, error, and empty states.

---

# 17. API Route Verification

During development, route verification was used to identify an issue with directly iterating over FastAPI's complete route collection.

The original diagnostic command failed because FastAPI includes non-route objects such as `_IncludedRouter`, which do not expose `.path`.

### Improvement

Route inspection should filter actual route objects or inspect the application after router inclusion rather than assuming every item in `app.routes` has a path.

### Result

This helped distinguish routing/debugging issues from actual application endpoint failures.

---

# 18. Data Contract Improvements

The frontend and backend now share explicit data structures for:

- Analysis
- Finding
- Evidence
- Repository
- Evaluation
- Evaluation metrics
- Evaluation cases
- Agent trajectory

The trajectory API response matches the backend trajectory schema with fields such as:

- `id`
- `analysis_run_id`
- `step_number`
- `event_type`
- `tool_name`
- `input_data`
- `output_data`
- `observation`
- `created_at`

### User value

Consistent contracts reduce frontend/backend integration errors.

---

# 19. Documentation Improvements

The project documentation was expanded to include:

- problem statement
- target user
- user bottleneck
- product value
- architecture
- repository ingestion
- analysis workflow
- security rules
- findings
- evidence
- agent trajectory
- evaluation
- API endpoint documentation
- reproducibility instructions
- limitations
- improvement history

This changelog provides the evaluator with a direct record of the evolution of the system.

---

# 20. Reproducibility Improvements

The workflow is designed so an evaluator can reproduce the major product path.

Recommended verification sequence:

1. Start the backend.
2. Start the frontend.
3. Confirm `/health`.
4. Upload a ZIP repository or ingest a valid GitHub repository URL.
5. Create an analysis for the ingested repository.
6. Run the analysis.
7. Open the analysis results.
8. Inspect findings.
9. Inspect finding evidence.
10. Open the trajectory for the analysis.
11. Confirm the seven trajectory steps.
12. Run the evaluation.
13. Open the evaluation detail.
14. Inspect metrics.
15. Inspect case-level results.

---

# 21. Known Limitations

The current implementation is intentionally deterministic rather than a fully autonomous LLM security agent.

Important limitations include:

- detection is pattern-based;
- semantic understanding of code is limited;
- some rules can produce false positives or false negatives outside the benchmark;
- supported languages are limited to Python, JavaScript, TypeScript, JSX, and TSX;
- the GitHub ingestion flow depends on repositories being accessible to the configured Git client;
- trajectory data represents user-facing execution events and not hidden chain-of-thought;
- benchmark results should not be interpreted as universal real-world security accuracy.

These limitations are documented deliberately rather than hidden.

---

# 22. Evidence of Completion

The following implementation evidence demonstrates the current state:

### Backend

- `AnalysisRun` model exists.
- `AgentTrajectory` model exists.
- trajectory service persists and lists trajectory steps.
- analysis service creates seven trajectory steps.
- analysis service persists findings and evidence.
- evaluation service produces benchmark metrics and cases.
- routers expose analysis, trajectory, finding, repository, and evaluation APIs.

### Frontend

- trajectory TypeScript types exist.
- API client includes `getTrajectories`.
- dynamic trajectory route exists at:
  `app/trajectories/[analysisId]/page.tsx`
- trajectory UI displays real execution steps.
- loading/error/empty states are implemented.

### Runtime evidence

A completed analysis has produced seven trajectory events:

1. `analysis_started`
2. `repository_inspection_started`
3. `repository_inspected`
4. `security_scan_started`
5. `findings_generated`
6. `evidence_collected`
7. `analysis_completed`

This confirms that trajectory persistence and retrieval are not only theoretical features.

---

# 23. Final Product Improvement Story

The improvement story can be summarized as:

### Initial prototype

A deterministic security scanner could identify a small number of security patterns.

### Improvement 1

Repository ingestion was expanded to support practical repository acquisition.

### Improvement 2

Analysis became a persisted, inspectable workflow.

### Improvement 3

Detection coverage expanded from three baseline rules to eight RepoGuard rules.

### Improvement 4

Findings became structured records with severity and source locations.

### Improvement 5

Evidence was attached directly to findings.

### Improvement 6

Agent execution was made observable through persisted trajectory steps.

### Improvement 7

The frontend was connected to the trajectory API through a real dynamic analysis route.

### Improvement 8

Evaluation became measurable at both overall and case level.

### Improvement 9

The benchmark demonstrated measurable gains in primary outcome, critical detection, human time, and cost while maintaining evidence support and zero measured false positives in the benchmark.

### Current state

RepoGuard Agent AI now presents an end-to-end security analysis workflow that is:

- usable,
- inspectable,
- evidence-backed,
- measurable,
- reproducible,
- and documented.

---

# 24. Evaluator-Facing Summary

The strongest demonstration path is:

**Ingest repository → Create analysis → Run analysis → Inspect findings → Inspect evidence → Open Agent Trajectory → Confirm seven steps → Run Evaluation → Compare baseline vs advanced metrics**

This demonstrates the relationship between the major system components rather than showing isolated features.

The key improvement is not simply that more rules were added. The system was evolved into a connected workflow in which the user can see:

**what repository was analyzed, what the agent did, what it found, where the evidence came from, how the execution progressed, and how the improved detector performed against the baseline.**
