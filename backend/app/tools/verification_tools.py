from pathlib import Path

from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.finding import Finding


def verify_findings(
    db: Session,
    analysis_id,
    workspace: Path,
) -> dict:
    """
    Verify that finding evidence still exists at the recorded
    file and line location.

    Verification is intentionally deterministic and reproducible.
    """

    findings = (
        db.query(Finding)
        .filter(Finding.analysis_run_id == analysis_id)
        .all()
    )

    verified_findings = 0
    failed_findings = 0

    for finding in findings:
        evidence_items = (
            db.query(Evidence)
            .filter(Evidence.finding_id == finding.id)
            .all()
        )

        finding_verified = False

        for evidence in evidence_items:
            file_path = workspace / evidence.file_path

            if not file_path.exists():
                evidence.verification_status = "failed"
                continue

            try:
                lines = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()

                start = max(1, evidence.line_start or 1)
                end = evidence.line_end or start

                selected_lines = lines[start - 1:end]

                actual_content = "\n".join(
                    line.strip()
                    for line in selected_lines
                )

                expected_content = (
                    evidence.content or ""
                ).strip()

                if expected_content in actual_content:
                    evidence.verification_status = "verified"
                    finding_verified = True
                else:
                    evidence.verification_status = "failed"

            except Exception:
                evidence.verification_status = "failed"

        if finding_verified:
            verified_findings += 1
        else:
            failed_findings += 1

    db.flush()

    return {
        "finding_count": len(findings),
        "verified_findings": verified_findings,
        "failed_findings": failed_findings,
    }