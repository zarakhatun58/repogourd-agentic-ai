
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.analysis import AnalysisRun
from app.models.repository import Repository
from app.services.architecture_service import analyze_architecture


router = APIRouter(
    prefix="/analyses",
    tags=["Architecture Analysis"],
)


@router.get(
    "/{analysis_id}/architecture",
    status_code=status.HTTP_200_OK,
)
def get_analysis_architecture(
    analysis_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Return dynamic architecture analysis for an analysis run.

    The architecture is calculated from the repository workspace associated
    with the AnalysisRun. No demo/static architecture data is returned.
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
        result = analyze_architecture(repository)
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
            detail="Unable to read repository workspace",
        ) from exc

    return {
        "analysis_id": str(analysis.id),
        "repository_id": str(repository.id),
        "status": analysis.status,
        "architecture": result,
    }

