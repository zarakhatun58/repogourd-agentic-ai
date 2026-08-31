from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvaluationMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_id: UUID
    key: str
    label: str
    unit: str
    baseline: float
    advanced: float
    higher_is_better: bool
    created_at: datetime


class EvaluationCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_id: UUID
    case_id: str
    case_name: str
    description: str
    status: str
    baseline_score: float
    advanced_score: float
    improvement: float
    baseline_tp: int
    baseline_fp: int
    baseline_fn: int
    advanced_tp: int
    advanced_fp: int
    advanced_fn: int
    expected_rules: list | None
    baseline_rules: list | None
    advanced_rules: list | None
    created_at: datetime


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    benchmark_version: str
    primary_metric: str
    baseline_overall: float
    advanced_overall: float
    human_time_baseline: float
    human_time_advanced: float
    cost_baseline: float
    cost_advanced: float
    configuration: dict | None
    created_at: datetime


class EvaluationDetailResponse(EvaluationResponse):
    metrics: list[EvaluationMetricResponse]
    cases: list[EvaluationCaseResponse]
