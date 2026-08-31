
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.testing import TestingAnalysisResponse
from app.services.testing_service import get_testing_analysis


router = APIRouter(
    prefix="/analyses",
    tags=["Testing Analysis"],
)


@router.get(
    "/{analysis_id}/testing",
    response_model=TestingAnalysisResponse,
)
def get_testing(
    analysis_id: UUID,
    db: Session = Depends(get_db),
) -> TestingAnalysisResponse:
    """
    Return dynamic testing analysis for an analysis run.
    """

    try:
        return get_testing_analysis(
            db=db,
            analysis_id=analysis_id,
        )

    except ValueError as exc:
        message = str(exc)

        if message == "Analysis not found.":
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        if message == "Repository not found.":
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=422,
            detail=message,
        ) from exc

