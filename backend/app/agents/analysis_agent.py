from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun
from app.models.agent_trajectory import AgentTrajectory

from app.tools.repository_tools import inspect_repository
from app.tools.security_tools import scan_repository
from app.tools.evidence_tools import collect_evidence
from app.tools.verification_tools import verify_findings


class AnalysisAgentError(Exception):
    """Raised when the analysis agent cannot complete its workflow."""


class AnalysisAgent:
    """
    RepoGuard analysis agent.

    The agent orchestrates bounded tools rather than directly performing
    every analysis operation inside the service layer.

    Workflow:

        repository inspection
                ↓
        security detection
                ↓
        evidence collection
                ↓
        evidence verification
                ↓
        final result
    """

    def __init__(
        self,
        db: Session,
        analysis: AnalysisRun,
        workspace: Path,
    ):
        self.db = db
        self.analysis = analysis
        self.workspace = workspace
        self.step_number = 0

    def _record(
        self,
        event_type: str,
        observation: str,
        tool_name: str | None = None,
        input_data: dict | None = None,
        output_data: dict | None = None,
    ) -> AgentTrajectory:

        self.step_number += 1

        trajectory = AgentTrajectory(
            analysis_run_id=self.analysis.id,
            step_number=self.step_number,
            event_type=event_type,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            observation=observation,
        )

        self.db.add(trajectory)
        self.db.flush()

        return trajectory

    def run(self) -> AnalysisRun:

        try:
            # --------------------------------------------------
            # 1. Agent starts
            # --------------------------------------------------

            self._record(
                event_type="agent_started",
                observation=(
                    "RepoGuard analysis agent started a "
                    "tool-driven repository security workflow."
                ),
                input_data={
                    "analysis_id": str(self.analysis.id),
                    "repository_id": str(
                        self.analysis.repository_id
                    ),
                    "agent_type": self.analysis.agent_type,
                    "commit_sha": self.analysis.commit_sha,
                },
            )

            self.db.commit()

            # --------------------------------------------------
            # 2. Repository inspection tool
            # --------------------------------------------------

            self._record(
                event_type="tool_started",
                tool_name="repository_inspection_tool",
                observation=(
                    "Agent selected the repository inspection "
                    "tool to understand the analysis workspace."
                ),
                input_data={
                    "workspace": str(self.workspace),
                },
            )

            inspection = inspect_repository(
                self.workspace
            )

            self._record(
                event_type="tool_completed",
                tool_name="repository_inspection_tool",
                observation=(
                    "Repository inspection completed and "
                    "returned structured workspace metadata."
                ),
                output_data={
                    "file_count": inspection["file_count"],
                    "supported_file_count": inspection[
                        "supported_file_count"
                    ],
                    "supported_extensions": inspection[
                        "supported_extensions"
                    ],
                },
            )

            self.db.commit()

            # --------------------------------------------------
            # 3. Security detection tool
            # --------------------------------------------------

            self._record(
                event_type="tool_started",
                tool_name="security_scanner_tool",
                observation=(
                    "Agent selected the security scanner tool "
                    "for deterministic source-code analysis."
                ),
                input_data={
                    "supported_file_count": inspection[
                        "supported_file_count"
                    ],
                },
            )

            findings_count = scan_repository(
                db=self.db,
                analysis=self.analysis,
                workspace=self.workspace,
            )

            self._record(
                event_type="tool_completed",
                tool_name="security_scanner_tool",
                observation=(
                    "Security scanner completed and generated "
                    "candidate security findings."
                ),
                output_data={
                    "findings_count": findings_count,
                },
            )

            self.db.commit()

            # --------------------------------------------------
            # 4. Evidence collection tool
            # --------------------------------------------------

            self._record(
                event_type="tool_started",
                tool_name="evidence_collector_tool",
                observation=(
                    "Agent selected the evidence collector to "
                    "associate findings with source-code evidence."
                ),
                input_data={
                    "analysis_id": str(self.analysis.id),
                },
            )

            evidence_result = collect_evidence(
                db=self.db,
                analysis_id=self.analysis.id,
            )

            self._record(
                event_type="tool_completed",
                tool_name="evidence_collector_tool",
                observation=(
                    "Evidence collection completed."
                ),
                output_data=evidence_result,
            )

            self.db.commit()

            # --------------------------------------------------
            # 5. Verification tool
            # --------------------------------------------------

            self._record(
                event_type="tool_started",
                tool_name="verification_tool",
                observation=(
                    "Agent selected the verification tool to "
                    "re-check finding evidence against the "
                    "repository source."
                ),
                input_data={
                    "analysis_id": str(self.analysis.id),
                },
            )

            verification_result = verify_findings(
                db=self.db,
                analysis_id=self.analysis.id,
                workspace=self.workspace,
            )

            self._record(
                event_type="tool_completed",
                tool_name="verification_tool",
                observation=(
                    "Evidence verification completed using "
                    "the recorded file paths and source lines."
                ),
                output_data=verification_result,
            )

            self.db.commit()

            # --------------------------------------------------
            # 6. Agent final result
            # --------------------------------------------------

            self._record(
                event_type="agent_completed",
                observation=(
                    "RepoGuard analysis agent completed the "
                    "tool-driven security workflow successfully."
                ),
                output_data={
                    "findings_count": findings_count,
                    "evidence_count": evidence_result[
                        "evidence_count"
                    ],
                    "verified_findings": verification_result[
                        "verified_findings"
                    ],
                    "failed_findings": verification_result[
                        "failed_findings"
                    ],
                },
            )

            self.db.commit()

            return self.analysis

        except Exception as exc:
            self.db.rollback()

            self._record(
                event_type="agent_failed",
                observation=(
                    "RepoGuard analysis agent failed while "
                    "executing the tool workflow."
                ),
                output_data={
                    "error": str(exc),
                },
            )

            self.db.commit()

            raise AnalysisAgentError(
                f"Analysis agent failed: {exc}"
            ) from exc