from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GitHubRepositoryCreate(BaseModel):
    url: str


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source_type: str
    source_url: str | None
    default_branch: str