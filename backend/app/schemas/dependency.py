from typing import Literal

from pydantic import BaseModel, Field


DependencyType = Literal["prod", "dev", "optional", "unknown"]
DependencyStatus = Literal[
    "ok",
    "outdated",
    "conflict",
    "unknown",
]
DependencyRisk = Literal[
    "low",
    "medium",
    "high",
]


class DependencyPackage(BaseModel):
    package: str = Field(min_length=1)
    version: str = Field(min_length=1)
    type: DependencyType = "unknown"
    status: DependencyStatus = "unknown"
    risk: DependencyRisk = "low"


class DependencyAnalysisResult(BaseModel):
    total: int = Field(default=0, ge=0)
    direct: int = Field(default=0, ge=0)
    dev: int = Field(default=0, ge=0)
    optional: int = Field(default=0, ge=0)
    outdated: int = Field(default=0, ge=0)
    conflicts: int = Field(default=0, ge=0)

    packages: list[DependencyPackage] = Field(default_factory=list)