
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.analysis import AnalysisRun
from app.models.repository import Repository
from app.services.dependency_service import analyze_dependencies


router = APIRouter(
    prefix="/analyses",
    tags=["Dependency Analysis"],
)


@router.get(
    "/{analysis_id}/dependencies",
    status_code=status.HTTP_200_OK,
)
def get_analysis_dependencies(
    analysis_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Return dynamic dependency analysis for an analysis run.

    Dependency information is extracted from the repository associated
    with the analysis. No demo dependency data is used.
    """

    analysis = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.id == analysis_id)
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    repository = (
        db.query(Repository)
        .filter(Repository.id == analysis.repository_id)
        .first()
    )

    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository associated with this analysis was not found",
        )

    try:
        result = analyze_dependencies(repository)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read repository dependency manifests",
        ) from exc

    return {
        "analysis_id": str(analysis.id),
        "repository_id": str(repository.id),
        "status": analysis.status,
        "dependencies": result,
    }

