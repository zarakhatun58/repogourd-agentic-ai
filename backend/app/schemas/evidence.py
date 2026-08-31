from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    finding_id: UUID
    evidence_type: str
    file_path: str | None
    line_start: int | None
    line_end: int | None
    content: str | None
    verification_status: str
    created_at: datetime
