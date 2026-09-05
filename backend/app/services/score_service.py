from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun
from app.models.finding import Finding


SEVERITY_WEIGHTS = {
    "critical": 20,
    "high": 10,
    "medium": 5,
    "low": 2,
}


def calculate_security_score(
    findings: list[Finding],
) -> float:
    if not findings:
        return 100.0

    deduction = sum(
        SEVERITY_WEIGHTS.get(
            finding.severity,
            0,
        )
        for finding in findings
    )

    return max(
        0.0,
        min(
            100.0,
            100.0 - deduction,
        ),
    )


def calculate_analysis_scores(
    db: Session,
    analysis: AnalysisRun,
) -> dict:
    findings = (
        db.query(Finding)
        .filter(
            Finding.analysis_run_id == analysis.id
        )
        .all()
    )

    security_score = calculate_security_score(
        findings
    )

    return {
        "overall_score": security_score,
        "category_scores": [
            {
                "category": "security",
                "score": security_score,
                "max_score": 100,
            },
            {
                "category": "architecture",
                "score": None,
                "max_score": 100,
            },
            {
                "category": "testing",
                "score": None,
                "max_score": 100,
            },
            {
                "category": "dependencies",
                "score": None,
                "max_score": 100,
            },
            {
                "category": "code_quality",
                "score": None,
                "max_score": 100,
            },
        ],
    }