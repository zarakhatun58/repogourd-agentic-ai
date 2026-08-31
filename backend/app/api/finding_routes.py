from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.finding import Finding
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceResponse


router = APIRouter(
    prefix="/findings",
    tags=["Findings"],
)


@router.get(
    "/{finding_id}/evidence",
    response_model=list[EvidenceResponse],
)
def get_finding_evidence(
    finding_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get all evidence associated with a finding.
    """

    finding = (
        db.query(Finding)
        .filter(Finding.id == finding_id)
        .first()
    )

    if not finding:
        raise HTTPException(
            status_code=404,
            detail="Finding not found",
        )

    evidence = (
        db.query(Evidence)
        .filter(
            Evidence.finding_id == finding_id
        )
        .order_by(
            Evidence.created_at.asc()
        )
        .all()
    )

    return evidence
