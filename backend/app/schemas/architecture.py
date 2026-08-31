
from typing import List

from pydantic import BaseModel, Field


class ArchitectureLayer(BaseModel):
    """Detected application layer."""

    name: str
    module: str


class ArchitectureModule(BaseModel):
    """Detected repository module/package."""

    id: str
    name: str
    layer: str
    files: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)


class ArchitectureRelationship(BaseModel):
    """Relationship between two repository modules."""

    source: str
    target: str
    relationship_type: str = "imports"


class ArchitectureAnalysis(BaseModel):
    """Complete deterministic architecture analysis result."""

    analysis_id: str

    technologies: List[str] = Field(default_factory=list)

    layers: List[ArchitectureLayer] = Field(default_factory=list)

    modules: List[ArchitectureModule] = Field(default_factory=list)

    relationships: List[ArchitectureRelationship] = Field(
        default_factory=list
    )

    risks: List[str] = Field(default_factory=list)

    files_scanned: int = 0

