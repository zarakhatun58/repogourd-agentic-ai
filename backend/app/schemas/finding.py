from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    rule_id: str
    severity: str
    title: str
    description: str | None
    file_path: str | None
    line_start: int | None
    line_end: int | None
    status: str
    created_at: datetime
