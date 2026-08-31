from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisCreate(BaseModel):
    repository_id: UUID = Field(
        ...,
        description="ID of the repository to analyze",
    )

    agent_type: str = Field(
        default="repoguard-agent",
        max_length=100,
        description="AI agent responsible for the analysis",
    )


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository_id: UUID
    status: str
    agent_type: str | None
    commit_sha: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime