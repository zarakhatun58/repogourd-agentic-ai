from app.agents.supervisor_agent import AgentContext
from app.tools.security_tools import run_security_scan


class SecurityAgent:
    """
    Generates candidate findings using bounded security tools.

    Candidates are not considered final findings until
    evidence verification succeeds.
    """

    def analyze(
        self,
        context: AgentContext,
    ) -> tuple[AgentContext, list[dict]]:

        candidates = run_security_scan(
            workspace=context.workspace,
            files=context.supported_files,
        )

        context.current_stage = "security_analysis"

        return context, candidates