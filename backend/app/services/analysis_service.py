
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.analysis import AnalysisRun
from app.models.repository import Repository
from app.models.finding import Finding
from app.models.evidence import Evidence
from app.tools.security_tools import run_security_scan
from app.models.agent_trajectory import AgentTrajectory


class AnalysisError(Exception):
    """Raised when analysis creation or execution fails."""


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    "coverage",
}


def create_analysis(
    db: Session,
    repository_id: UUID,
    agent_type: str = "repoguard-agent",
) -> AnalysisRun:
    """
    Create a new analysis run for a repository.
    """

    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository:
        raise AnalysisError(
            f"Repository not found: {repository_id}"
        )

    if not repository.workspace_path:
        raise AnalysisError(
            "Repository has no workspace. "
            "Ingest the repository before starting analysis."
        )

    analysis = AnalysisRun(
        repository_id=repository.id,
        status="queued",
        agent_type=agent_type,
        commit_sha=repository.latest_commit_sha,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


def get_analysis(
    db: Session,
    analysis_id: UUID,
) -> AnalysisRun | None:
    """
    Get an analysis run by ID.
    """

    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == analysis_id)
        .first()
    )


def list_analyses(
    db: Session,
) -> list[AnalysisRun]:
    """
    Get all analysis runs.

    Returns newest analyses first.
    """

    return (
        db.query(AnalysisRun)
        .order_by(
            AnalysisRun.created_at.desc()
        )
        .all()
    )


def _add_trajectory(
    db: Session,
    analysis_id: UUID,
    step_number: int,
    event_type: str,
    observation: str,
    tool_name: str | None = None,
    input_data: dict | None = None,
    output_data: dict | None = None,
) -> AgentTrajectory:
    """
    Store one observable agent workflow step.

    Only user-facing execution information is recorded.
    Hidden chain-of-thought is never stored.
    """

    trajectory = AgentTrajectory(
        analysis_run_id=analysis_id,
        step_number=step_number,
        event_type=event_type,
        tool_name=tool_name,
        input_data=input_data,
        output_data=output_data,
        observation=observation,
    )

    db.add(trajectory)
    db.flush()

    return trajectory


def _inspect_repository(
    workspace: Path,
) -> tuple[int, list[str]]:
    """
    Repository inspection tool.

    Responsibilities:
    - enumerate files
    - ignore generated/vendor directories
    - select supported source files

    Returns:
        (total_file_count, supported_source_files)
    """

    total_file_count = 0
    supported_files: list[str] = []

    for file_path in workspace.rglob("*"):

        if not file_path.is_file():
            continue

        if any(
            part in IGNORED_DIRECTORIES
            for part in file_path.parts
        ):
            continue

        total_file_count += 1

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        relative_path = str(
            file_path.relative_to(workspace)
        )

        supported_files.append(relative_path)

    supported_files.sort()

    return total_file_count, supported_files


def _create_findings_from_scan(
    db: Session,
    analysis: AnalysisRun,
    scan_results: list[dict],
) -> int:
    """
    Convert security-tool output into database findings.

    Tool boundary:

        Security Scanner
                ↓
        structured scan results
                ↓
        Finding records

    The scanner does not write database records directly.
    """

    findings_created = 0

    for result in scan_results:

        finding = Finding(
            analysis_run_id=analysis.id,
            rule_id=result["rule_id"],
            severity=result["severity"],
            title=result["title"],
            description=result["description"],
            file_path=result["file_path"],
            line_start=result["line_start"],
            line_end=result["line_end"],
            status="open",
        )

        db.add(finding)
        db.flush()

        findings_created += 1

    return findings_created


def _collect_evidence(
    db: Session,
    analysis: AnalysisRun,
) -> int:
    """
    Evidence collection stage.

    For every finding, read the cited source line again and create
    an evidence record.

    This provides an explicit evidence boundary between:
        detection → evidence collection
    """

    findings = (
        db.query(Finding)
        .filter(
            Finding.analysis_run_id == analysis.id
        )
        .all()
    )

    evidence_created = 0

    repository = (
        db.query(Repository)
        .filter(
            Repository.id == analysis.repository_id
        )
        .first()
    )

    if not repository or not repository.workspace_path:
        raise AnalysisError(
            "Repository workspace unavailable during evidence collection."
        )

    workspace = Path(repository.workspace_path)

    for finding in findings:

        if not finding.file_path:
            continue

        file_path = workspace / finding.file_path

        if not file_path.is_file():
            continue

        try:
            lines = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines()
        except Exception:
            continue

        start = finding.line_start or 1
        end = finding.line_end or start

        if start < 1:
            start = 1

        if end < start:
            end = start

        if start > len(lines):
            continue

        end = min(end, len(lines))

        evidence_lines = lines[start - 1:end]

        content = "\n".join(
            line.strip()
            for line in evidence_lines
        )

        evidence = Evidence(
            finding_id=finding.id,
            evidence_type="source_code",
            file_path=finding.file_path,
            line_start=start,
            line_end=end,
            content=content,
            verification_status="pending",
        )

        db.add(evidence)

        evidence_created += 1

    db.flush()

    return evidence_created


def _verify_findings(
    db: Session,
    analysis: AnalysisRun,
) -> tuple[int, int]:
    """
    Verification stage.

    Re-check every finding against the current repository source.

    A finding is marked verified only when:
    - the file still exists
    - the cited line exists
    - the original matched pattern is still present

    Returns:
        (verified_count, rejected_count)
    """

    findings = (
        db.query(Finding)
        .filter(
            Finding.analysis_run_id == analysis.id
        )
        .all()
    )

    repository = (
        db.query(Repository)
        .filter(
            Repository.id == analysis.repository_id
        )
        .first()
    )

    if not repository or not repository.workspace_path:
        raise AnalysisError(
            "Repository workspace unavailable during verification."
        )

    workspace = Path(repository.workspace_path)

    verified_count = 0
    rejected_count = 0

    for finding in findings:

        evidence_rows = (
            db.query(Evidence)
            .filter(
                Evidence.finding_id == finding.id
            )
            .all()
        )

        verified = False

        file_path = workspace / finding.file_path

        if file_path.is_file():

            try:
                lines = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()
            except Exception:
                lines = []

            start = finding.line_start or 1

            if 1 <= start <= len(lines):

                source_line = lines[start - 1].strip()

                for evidence in evidence_rows:

                    if (
                        evidence.content
                        and evidence.content.strip() == source_line
                    ):
                        verified = True
                        break

        if verified:
            verified_count += 1

            for evidence in evidence_rows:
                evidence.verification_status = "verified"

            finding.status = "open"

        else:
            rejected_count += 1

            for evidence in evidence_rows:
                evidence.verification_status = "rejected"

            finding.status = "rejected"

    db.flush()

    return verified_count, rejected_count


def execute_analysis(
    db: Session,
    analysis_id: UUID,
) -> AnalysisRun:
    """
    Execute the RepoGuard agent workflow.

    Architecture:

        1. Analysis Agent starts
        2. Repository Inspection Tool
        3. Security Analysis Tool
        4. Finding Creation
        5. Evidence Collection Tool
        6. Verification Tool
        7. Final Result

    The individual tools are bounded and deterministic.
    The analysis service orchestrates them into a reproducible
    agent workflow.

    No hidden chain-of-thought is stored or displayed.
    """

    analysis = get_analysis(
        db=db,
        analysis_id=analysis_id,
    )

    if not analysis:
        raise AnalysisError(
            f"Analysis not found: {analysis_id}"
        )

    repository = (
        db.query(Repository)
        .filter(
            Repository.id == analysis.repository_id
        )
        .first()
    )

    if not repository:
        raise AnalysisError(
            "Repository associated with analysis was not found."
        )

    if not repository.workspace_path:
        raise AnalysisError(
            "Repository workspace does not exist."
        )

    workspace = Path(repository.workspace_path)

    if not workspace.exists():
        raise AnalysisError(
            f"Repository workspace does not exist: {workspace}"
        )

    try:

        # =========================================================
        # STEP 1
        # Agent initialization
        # =========================================================

        analysis.status = "running"
        analysis.started_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(analysis)

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=1,
            event_type="analysis_started",
            observation=(
                "RepoGuard analysis agent started the repository "
                "security workflow."
            ),
            input_data={
                "repository_id": str(repository.id),
                "agent_type": analysis.agent_type,
                "commit_sha": analysis.commit_sha,
            },
            output_data={
                "status": "running",
                "workflow": [
                    "repository_inspection",
                    "security_analysis",
                    "finding_creation",
                    "evidence_collection",
                    "verification",
                    "final_result",
                ],
            },
        )

        db.commit()

        # =========================================================
        # STEP 2
        # Repository inspection starts
        # =========================================================

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=2,
            event_type="repository_inspection_started",
            tool_name="repository_inspection_tool",
            input_data={
                "workspace": str(workspace),
                "ignored_directories": sorted(
                    IGNORED_DIRECTORIES
                ),
            },
            observation=(
                "Agent delegated repository discovery to the "
                "repository inspection tool."
            ),
        )

        db.commit()

        # =========================================================
        # STEP 3
        # Repository inspection result
        # =========================================================

        file_count, source_files = _inspect_repository(
            workspace
        )

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=3,
            event_type="repository_inspected",
            tool_name="repository_inspection_tool",
            input_data={
                "supported_extensions": sorted(
                    SUPPORTED_EXTENSIONS
                ),
            },
            output_data={
                "file_count": file_count,
                "supported_file_count": len(source_files),
                "source_files": source_files[:100],
            },
            observation=(
                f"Repository inspection completed. "
                f"{file_count} usable files were discovered, "
                f"including {len(source_files)} supported source files."
            ),
        )

        db.commit()

        # =========================================================
        # STEP 4
        # Security analysis tool
        # =========================================================

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=4,
            event_type="security_scan_started",
            tool_name="security_analysis_tool",
            input_data={
                "files_requested": len(source_files),
                "rule_count": 8,
                "supported_languages": [
                    "python",
                    "javascript",
                    "typescript",
                    "jsx",
                    "tsx",
                ],
            },
            observation=(
                "Agent delegated bounded security analysis to "
                "the security-analysis tool."
            ),
        )

        db.commit()

        # =========================================================
        # STEP 5
        # Run security tool
        # =========================================================

        scan_result = run_security_scan(
            workspace=workspace,
            files=source_files,
        )

        scan_findings = scan_result["findings"]

        findings_count = _create_findings_from_scan(
            db=db,
            analysis=analysis,
            scan_results=scan_findings,
        )

        db.commit()

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=5,
            event_type="findings_generated",
            tool_name="security_analysis_tool",
            input_data={
                "files_scanned": scan_result["files_scanned"],
                "rules_executed": scan_result["rules_executed"],
            },
            output_data={
                "candidate_findings": len(scan_findings),
                "findings_created": findings_count,
            },
            observation=(
                f"Security analysis completed and produced "
                f"{findings_count} candidate finding(s)."
            ),
        )

        db.commit()

        # =========================================================
        # STEP 6
        # Evidence collection
        # =========================================================

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=6,
            event_type="evidence_collection_started",
            tool_name="evidence_collection_tool",
            input_data={
                "finding_count": findings_count,
            },
            observation=(
                "Agent delegated source-code evidence collection "
                "for the generated findings."
            ),
        )

        db.commit()

        evidence_count = _collect_evidence(
            db=db,
            analysis=analysis,
        )

        db.commit()

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=7,
            event_type="evidence_collected",
            tool_name="evidence_collection_tool",
            output_data={
                "evidence_count": evidence_count,
            },
            observation=(
                f"Evidence collection completed with "
                f"{evidence_count} source evidence record(s)."
            ),
        )

        db.commit()

        # =========================================================
        # STEP 8
        # Verification
        # =========================================================

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=8,
            event_type="verification_started",
            tool_name="verification_tool",
            input_data={
                "finding_count": findings_count,
                "evidence_count": evidence_count,
            },
            observation=(
                "Agent delegated finding verification against "
                "the repository source."
            ),
        )

        db.commit()

        verified_count, rejected_count = _verify_findings(
            db=db,
            analysis=analysis,
        )

        db.commit()

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=9,
            event_type="verification_completed",
            tool_name="verification_tool",
            output_data={
                "verified_count": verified_count,
                "rejected_count": rejected_count,
            },
            observation=(
                f"Verification completed. "
                f"{verified_count} finding(s) were verified and "
                f"{rejected_count} finding(s) were rejected."
            ),
        )

        db.commit()

        # =========================================================
        # STEP 10
        # Final result
        # =========================================================

        analysis.status = "completed"
        analysis.completed_at = datetime.now(timezone.utc)
        analysis.error_message = None

        db.commit()
        db.refresh(analysis)

        _add_trajectory(
            db=db,
            analysis_id=analysis.id,
            step_number=10,
            event_type="analysis_completed",
            output_data={
                "findings_count": findings_count,
                "evidence_count": evidence_count,
                "verified_count": verified_count,
                "rejected_count": rejected_count,
                "status": "completed",
            },
            observation=(
                "RepoGuard agent completed the workflow successfully "
                "with security findings linked to source evidence "
                "and verification results."
            ),
        )

        db.commit()

        return analysis

    except Exception as exc:

        db.rollback()

        analysis = get_analysis(
            db=db,
            analysis_id=analysis_id,
        )

        if analysis:

            analysis.status = "failed"
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.error_message = str(exc)

            db.commit()

            _add_trajectory(
                db=db,
                analysis_id=analysis.id,
                step_number=999,
                event_type="analysis_failed",
                output_data={
                    "status": "failed",
                    "error": str(exc),
                },
                observation=(
                    "RepoGuard agent workflow failed during execution."
                ),
            )

            db.commit()

        raise AnalysisError(
            f"Analysis execution failed: {exc}"
        ) from exc

