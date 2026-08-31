from pathlib import Path

from app.agents.supervisor_agent import AgentContext


SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    "coverage",
}


class RepositoryAgent:
    """
    Responsible only for repository discovery.

    It does not create findings.
    """

    def inspect(
        self,
        context: AgentContext,
    ) -> AgentContext:

        files: list[str] = []
        supported_files: list[str] = []

        for path in context.workspace.rglob("*"):

            if not path.is_file():
                continue

            if any(
                part in IGNORED_DIRECTORIES
                for part in path.parts
            ):
                continue

            relative = str(
                path.relative_to(context.workspace)
            )

            files.append(relative)

            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                supported_files.append(relative)

        context.files = files
        context.supported_files = supported_files
        context.current_stage = "repository_inspection"

        return context