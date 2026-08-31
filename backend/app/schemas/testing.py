
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TestingStatus = Literal[
    "completed",
    "partial",
    "failed",
]


class TestingCategory(BaseModel):
    name: str
    count: int = Field(ge=0)


class TestingAnalysisResponse(BaseModel):
    analysis_id: str

    status: TestingStatus

    test_files: int = Field(ge=0)
    test_suites: int = Field(ge=0)

    passed: int = Field(ge=0)
    failed: int = Field(ge=0)

    coverage: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    coverage_source: str = "not_available"

    framework: str = "unknown"

    categories: list[TestingCategory] = Field(
        default_factory=list,
    )

    missing_areas: list[str] = Field(
        default_factory=list,
    )

    execution_status: str = "not_run"

    files_scanned: int = Field(ge=0)

