
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.agent_trajectory import AgentTrajectory


def create_trajectory_step(
    db: Session,
    analysis_run_id: UUID,
    step_number: int,
    event_type: str,
    tool_name: str | None = None,
    input_data: dict | None = None,
    output_data: dict | None = None,
    observation: str | None = None,
) -> AgentTrajectory:
    """
    Create and persist one agent trajectory step.
    """

    trajectory = AgentTrajectory(
        analysis_run_id=analysis_run_id,
        step_number=step_number,
        event_type=event_type,
        tool_name=tool_name,
        input_data=input_data,
        output_data=output_data,
        observation=observation,
    )

    db.add(trajectory)
    db.commit()
    db.refresh(trajectory)

    return trajectory


def list_trajectory_steps(
    db: Session,
    analysis_run_id: UUID,
) -> list[AgentTrajectory]:
    """
    Return all trajectory steps for an analysis,
    ordered by execution step.
    """

    return (
        db.query(AgentTrajectory)
        .filter(
            AgentTrajectory.analysis_run_id == analysis_run_id
        )
        .order_by(
            AgentTrajectory.step_number.asc(),
            AgentTrajectory.created_at.asc(),
        )
        .all()
    )

