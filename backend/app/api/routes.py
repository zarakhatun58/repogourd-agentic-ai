from uuid import uuid4
from fastapi import APIRouter, HTTPException
from app.schemas.audit import AuditCreate, AuditResponse
from app.services.audit_service import create_audit, get_audit

router = APIRouter()

@router.post("/audits", response_model=AuditResponse, status_code=201)
async def create_audit_route(payload: AuditCreate):
    return create_audit(payload)

@router.get("/audits/{audit_id}", response_model=AuditResponse)
async def get_audit_route(audit_id: str):
    result = get_audit(audit_id)
    if not result:
        raise HTTPException(status_code=404, detail="Audit not found")
    return result
