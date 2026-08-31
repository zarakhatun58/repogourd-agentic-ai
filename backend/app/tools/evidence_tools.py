
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.finding import Finding


def collect_evidence(
    db: Session,
    analysis_id,
    workspace: Path,
) -> dict:
    """
    Evidence collection tool.

    Responsibility:
    - Read the source location referenced by findings.
    - Collect the exact source line associated with each finding.
    - Create source-code evidence when evidence does not already exist.

    This tool does NOT:
    - run security rules
    - create findings
    - decide finding severity
    - determine whether a finding is valid

    Verification is intentionally handled by the verification tool.
    """

    if not workspace.exists():
        raise FileNotFoundError(
            f"Repository workspace does not exist: {workspace}"
        )

    findings = (
        db.query(Finding)
        .filter(Finding.analysis_run_id == analysis_id)
        .order_by(Finding.id)
        .all()
    )

    evidence_count = 0
    collected_count = 0
    verified_count = 0

    for finding in findings:
        if not finding.file_path:
            continue

        source_path = workspace / finding.file_path

        if not source_path.exists() or not source_path.is_file():
            continue

        try:
            lines = source_path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines()
        except OSError:
            continue

        line_start = finding.line_start or 1
        line_end = finding.line_end or line_start

        if line_start < 1 or line_start > len(lines):
            continue

        line_end = min(line_end, len(lines))

        content = "\n".join(
            lines[line_start - 1:line_end]
        ).strip()

        if not content:
            continue

        existing = (
            db.query(Evidence)
            .filter(
                Evidence.finding_id == finding.id,
                Evidence.file_path == finding.file_path,
                Evidence.line_start == line_start,
                Evidence.line_end == line_end,
            )
            .first()
        )

        if existing:
            evidence = existing
        else:
            evidence = Evidence(
                finding_id=finding.id,
                evidence_type="source_code",
                file_path=finding.file_path,
                line_start=line_start,
                line_end=line_end,
                content=content,
                verification_status="pending",
            )

            db.add(evidence)
            db.flush()

            collected_count += 1

        evidence_count += 1

        if evidence.verification_status == "verified":
            verified_count += 1

    return {
        "finding_count": len(findings),
        "evidence_count": evidence_count,
        "collected_evidence_count": collected_count,
        "verified_evidence_count": verified_count,
    }

