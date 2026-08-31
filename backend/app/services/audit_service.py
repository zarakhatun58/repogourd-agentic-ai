from datetime import datetime, timezone
from app.schemas.audit import AuditCreate

_store = {}

def create_audit(payload: AuditCreate):
    from uuid import uuid4
    audit_id = str(uuid4())
    result = {
        "id": audit_id,
        "repository_url": str(payload.repository_url),
        "branch": payload.branch,
        "analysis_depth": payload.analysis_depth,
        "status": "queued",
        "created_at": datetime.now(timezone.utc),
    }
    _store[audit_id] = result
    return result

def get_audit(audit_id: str):
    return _store.get(audit_id)
