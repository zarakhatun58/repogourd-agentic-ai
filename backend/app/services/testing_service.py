
from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun
from app.models.repository import Repository
from app.schemas.testing import (
    TestingAnalysisResponse,
    TestingCategory,
)
from app.tools.testing_tools import run_testing_analysis


def _resolve_workspace(
    repository: Repository,
) -> Path:
    """
    Resolve the repository workspace used by RepoGuard.

    Repository workspace_path is preferred when available.
    """

    workspace_path = getattr(
        repository,
        "workspace_path",
        None,
    )

    if not workspace_path:
        raise ValueError(
            "Repository workspace path is not configured."
        )

    workspace = Path(workspace_path).resolve()

    if not workspace.exists():
        raise ValueError(
            f"Repository workspace does not exist: {workspace}"
        )

    if not workspace.is_dir():
        raise ValueError(
            f"Repository workspace is not a directory: {workspace}"
        )

    return workspace


def get_testing_analysis(
    db: Session,
    analysis_id: UUID,
) -> TestingAnalysisResponse:
    """
    Generate testing analysis for an existing analysis run.
    """

    analysis = (
        db.query(AnalysisRun)
        .filter(
            AnalysisRun.id == analysis_id
        )
        .first()
    )

    if not analysis:
        raise ValueError(
            "Analysis not found."
        )

    repository = (
        db.query(Repository)
        .filter(
            Repository.id == analysis.repository_id
        )
        .first()
    )

    if not repository:
        raise ValueError(
            "Repository not found."
        )

    workspace = _resolve_workspace(
        repository
    )

    result = run_testing_analysis(
        workspace=workspace
    )

    categories = [
        TestingCategory(
            name=item["name"],
            count=item["count"],
        )
        for item in result["categories"]
    ]

    status = "completed"

    if result["files_scanned"] == 0:
        status = "partial"

    return TestingAnalysisResponse(
        analysis_id=str(analysis.id),
        status=status,
        test_files=result["test_files"],
        test_suites=result["test_suites"],
        passed=result["passed"],
        failed=result["failed"],
        coverage=result["coverage"],
        coverage_source=result["coverage_source"],
        framework=result["framework"],
        categories=categories,
        missing_areas=result["missing_areas"],
        execution_status=result["execution_status"],
        files_scanned=result["files_scanned"],
    )

