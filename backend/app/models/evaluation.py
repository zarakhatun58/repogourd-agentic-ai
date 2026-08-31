import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="completed")
    benchmark_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    primary_metric: Mapped[str] = mapped_column(String(100), nullable=False, default="f1")
    baseline_overall: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    advanced_overall: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    human_time_baseline: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    human_time_advanced: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    cost_baseline: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    cost_advanced: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    configuration: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvaluationCaseResult(Base):
    __tablename__ = "evaluation_case_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(100), nullable=False)
    case_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="completed")
    baseline_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    advanced_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    improvement: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    baseline_tp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    baseline_fp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    baseline_fn: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    advanced_tp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    advanced_fp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    advanced_fn: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_rules: Mapped[list | None] = mapped_column(JSON, nullable=True)
    baseline_rules: Mapped[list | None] = mapped_column(JSON, nullable=True)
    advanced_rules: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvaluationMetricResult(Base):
    __tablename__ = "evaluation_metric_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="%")
    baseline: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    advanced: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    higher_is_better: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
