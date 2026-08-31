from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.evaluation import (
    EvaluationCaseResponse,
    EvaluationDetailResponse,
    EvaluationMetricResponse,
    EvaluationResponse,
)
from app.services.evaluation_service import (
    get_evaluation,
    get_evaluation_cases,
    get_evaluation_metrics,
    list_evaluations,
    run_evaluation,
)

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.get("", response_model=list[EvaluationResponse])
def list_evaluations_route(db: Session = Depends(get_db)):
    return list_evaluations(db)


@router.post("/run", response_model=EvaluationResponse, status_code=201)
def run_evaluation_route(db: Session = Depends(get_db)):
    try:
        return run_evaluation(db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}") from exc


@router.get("/{evaluation_id}", response_model=EvaluationDetailResponse)
def get_evaluation_route(evaluation_id: UUID, db: Session = Depends(get_db)):
    evaluation = get_evaluation(db, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return EvaluationDetailResponse(
        **EvaluationResponse.model_validate(evaluation).model_dump(),
        metrics=get_evaluation_metrics(db, evaluation_id),
        cases=get_evaluation_cases(db, evaluation_id),
    )


@router.get("/{evaluation_id}/cases", response_model=list[EvaluationCaseResponse])
def get_evaluation_cases_route(evaluation_id: UUID, db: Session = Depends(get_db)):
    if not get_evaluation(db, evaluation_id):
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return get_evaluation_cases(db, evaluation_id)


@router.get("/{evaluation_id}/metrics", response_model=list[EvaluationMetricResponse])
def get_evaluation_metrics_route(evaluation_id: UUID, db: Session = Depends(get_db)):
    if not get_evaluation(db, evaluation_id):
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return get_evaluation_metrics(db, evaluation_id)
