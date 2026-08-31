from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class AuditCreate(BaseModel):
    repository_url: HttpUrl
    branch: str = Field(default="main", min_length=1, max_length=200)
    analysis_depth: str = Field(default="standard", pattern="^(standard|deep)$")

class AuditResponse(BaseModel):
    id: str
    repository_url: str
    branch: str
    analysis_depth: str
    status: str
    created_at: datetime
