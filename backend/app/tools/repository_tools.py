from pathlib import Path


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


def inspect_repository(workspace: Path) -> dict:
    """
    Inspect a repository workspace and return structured metadata.

    This is a bounded repository-inspection tool. It does not perform
    security detection or create database findings.
    """

    if not workspace.exists():
        raise FileNotFoundError(
            f"Repository workspace does not exist: {workspace}"
        )

    files = []
    supported_files = []

    for path in workspace.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in IGNORED_DIRECTORIES
            for part in path.parts
        ):
            continue

        relative_path = str(path.relative_to(workspace))

        files.append(relative_path)

        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            supported_files.append(relative_path)

    return {
        "workspace": str(workspace),
        "file_count": len(files),
        "supported_file_count": len(supported_files),
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "files": files,
        "supported_files": supported_files,
    }