from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun
from app.models.finding import Finding


@dataclass
class AgentContext:
    analysis_id: UUID
    repository_id: UUID
    workspace: Path

    files: list[str] = field(default_factory=list)
    supported_files: list[str] = field(default_factory=list)

    candidate_findings: list[Finding] = field(default_factory=list)
    verified_findings: list[Finding] = field(default_factory=list)

    current_stage: str = "initialized"


class RepoGuardSupervisor:
    """
    Bounded supervisor for the RepoGuard agent workflow.

    The supervisor does not directly inspect source code.
    It delegates repository inspection, security scanning,
    evidence collection, verification, and judging to
    specialized agents/tools.
    """

    def __init__(
        self,
        db: Session,
        analysis: AnalysisRun,
    ):
        self.db = db
        self.analysis = analysis

    def create_context(
        self,
        workspace: Path,
    ) -> AgentContext:
        return AgentContext(
            analysis_id=self.analysis.id,
            repository_id=self.analysis.repository_id,
            workspace=workspace,
        )

    def next_stage(
        self,
        context: AgentContext,
    ) -> str:
        """
        Determine the next bounded workflow stage.

        This is intentionally explicit and auditable rather
        than allowing arbitrary tool execution.
        """

        transitions = {
            "initialized": "repository_inspection",
            "repository_inspection": "security_analysis",
            "security_analysis": "evidence_collection",
            "evidence_collection": "verification",
            "verification": "judging",
            "judging": "completed",
        }

        next_stage = transitions.get(context.current_stage)

        if not next_stage:
            raise RuntimeError(
                f"No valid transition from stage "
                f"{context.current_stage}"
            )

        return next_stage