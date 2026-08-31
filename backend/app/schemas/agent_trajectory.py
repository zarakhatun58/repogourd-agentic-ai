
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AgentTrajectoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    step_number: int
    event_type: str
    tool_name: str | None = None
    input_data: dict | None = None
    output_data: dict | None = None
    observation: str | None = None
    created_at: datetime

