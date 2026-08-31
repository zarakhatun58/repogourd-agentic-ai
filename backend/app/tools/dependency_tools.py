from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.schemas.dependency import (
    DependencyAnalysisResult,
    DependencyPackage,
)


# ---------------------------------------------------------------------
# Supported dependency manifests
# ---------------------------------------------------------------------

MANIFESTS = {
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return ""


def _normalize_version(value: str) -> str:
    """
    Keep the dependency declaration readable while avoiding
    pretending that a version constraint is an exact installed version.
    """
    value = value.strip()

    if not value:
        return "unknown"

    value = value.split("#", 1)[0].strip()

    return value


def _parse_requirements(
    workspace: Path,
    relative_path: str,
) -> list[DependencyPackage]:
    path = workspace / relative_path

    packages: list[DependencyPackage] = []

    for raw_line in _read_text(path).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if line.startswith(("-", "--")):
            continue

        if line.startswith((
            "git+",
            "http://",
            "https://",
            "file:",
        )):
            package = line.split("#", 1)[0].strip()

            packages.append(
                DependencyPackage(
                    package=package,
                    version="source",
                    type="prod",
                    status="unknown",
                    risk="low",
                )
            )
            continue

        match = re.match(
            r"^([A-Za-z0-9_.-]+)\s*(.*)$",
            line,
        )

        if not match:
            continue

        name = match.group(1)
        version = _normalize_version(match.group(2))

        packages.append(
            DependencyPackage(
                package=name,
                version=version or "unspecified",
                type="prod",
                status="unknown",
                risk="low",
            )
        )

    return packages


def _parse_package_json(
    workspace: Path,
    relative_path: str,
) -> list[DependencyPackage]:
    path = workspace / relative_path

    try:
        data: dict[str, Any] = json.loads(
            _read_text(path)
        )
    except (json.JSONDecodeError, TypeError):
        return []

    packages: list[DependencyPackage] = []

    for dependency_type, output_type in (
        ("dependencies", "prod"),
        ("devDependencies", "dev"),
        ("optionalDependencies", "optional"),
    ):
        dependencies = data.get(
            dependency_type,
            {},
        )

        if not isinstance(dependencies, dict):
            continue

        for name, version in dependencies.items():
            if not isinstance(name, str):
                continue

            packages.append(
                DependencyPackage(
                    package=name,
                    version=str(version),
                    type=output_type,
                    status="unknown",
                    risk="low",
                )
            )

    return packages


def _parse_pyproject(
    workspace: Path,
    relative_path: str,
) -> list[DependencyPackage]:
    """
    Lightweight deterministic parser.

    This intentionally does not attempt to implement the complete TOML
    specification. It handles the common dependency sections used by
    Python repositories without adding another runtime dependency.
    """

    path = workspace / relative_path
    content = _read_text(path)

    packages: list[DependencyPackage] = []

    current_section: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        section_match = re.match(
            r"^\[([^\]]+)\]$",
            line,
        )

        if section_match:
            current_section = section_match.group(1)
            continue

        if current_section not in {
            "project",
            "tool.poetry.dependencies",
            "tool.poetry.group.dev.dependencies",
        }:
            continue

        if "=" not in line:
            continue

        name, value = line.split("=", 1)

        name = name.strip()
        value = value.strip()

        if name in {
            "requires-python",
            "dependencies",
        }:
            continue

        if not re.match(
            r"^[A-Za-z0-9_.-]+$",
            name,
        ):
            continue

        dependency_type = (
            "dev"
            if current_section
            == "tool.poetry.group.dev.dependencies"
            else "prod"
        )

        packages.append(
            DependencyPackage(
                package=name,
                version=_normalize_version(value),
                type=dependency_type,
                status="unknown",
                risk="low",
            )
        )

    # Handle PEP 621 dependencies = [...]
    project_match = re.search(
        r"dependencies\s*=\s*\[(.*?)\]",
        content,
        flags=re.DOTALL,
    )

    if project_match:
        block = project_match.group(1)

        for match in re.finditer(
            r"""["']([^"']+)["']""",
            block,
        ):
            declaration = match.group(1).strip()

            parsed = re.match(
                r"^([A-Za-z0-9_.-]+)\s*(.*)$",
                declaration,
            )

            if not parsed:
                continue

            packages.append(
                DependencyPackage(
                    package=parsed.group(1),
                    version=parsed.group(2).strip()
                    or "unspecified",
                    type="prod",
                    status="unknown",
                    risk="low",
                )
            )

    return packages


def _find_manifests(workspace: Path) -> list[str]:
    manifests: list[str] = []

    for path in workspace.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in {
                ".git",
                ".venv",
                "venv",
                "node_modules",
                "__pycache__",
                ".next",
                "dist",
                "build",
            }
            for part in path.parts
        ):
            continue

        if path.name in MANIFESTS:
            manifests.append(
                path.relative_to(workspace).as_posix()
            )

    return sorted(manifests)


def run_dependency_analysis(
    workspace: Path,
) -> DependencyAnalysisResult:
    """
    Deterministic dependency-analysis tool.

    Input:
        Repository workspace.

    Output:
        Structured dependency analysis.

    The tool does not:
    - write database records
    - modify repository files
    - install dependencies
    - execute arbitrary repository code
    - claim vulnerability information without evidence
    """

    workspace = workspace.resolve()

    if not workspace.exists():
        return DependencyAnalysisResult()

    packages: list[DependencyPackage] = []

    manifests = _find_manifests(workspace)

    for relative_path in manifests:
        filename = Path(relative_path).name

        if filename == "requirements.txt":
            packages.extend(
                _parse_requirements(
                    workspace,
                    relative_path,
                )
            )

        elif filename == "package.json":
            packages.extend(
                _parse_package_json(
                    workspace,
                    relative_path,
                )
            )

        elif filename == "pyproject.toml":
            packages.extend(
                _parse_pyproject(
                    workspace,
                    relative_path,
                )
            )

    # Deduplicate package declarations while preserving deterministic
    # ordering. If the same package appears in multiple manifests,
    # keep the first declaration and mark duplicates as conflicts.
    unique: dict[
        tuple[str, str],
        DependencyPackage,
    ] = {}

    conflict_packages: set[str] = set()

    for package in packages:
        key = (
            package.package.lower(),
            package.type,
        )

        if key in unique:
            conflict_packages.add(
                package.package.lower()
            )
            continue

        unique[key] = package

    normalized: list[DependencyPackage] = []

    for package in unique.values():
        if package.package.lower() in conflict_packages:
            normalized.append(
                package.model_copy(
                    update={
                        "status": "conflict",
                        "risk": "medium",
                    }
                )
            )
        else:
            normalized.append(package)

    normalized.sort(
        key=lambda item: (
            item.package.lower(),
            item.type,
        )
    )

    total = len(normalized)
    direct = sum(
        1
        for package in normalized
        if package.type == "prod"
    )
    dev = sum(
        1
        for package in normalized
        if package.type == "dev"
    )
    optional = sum(
        1
        for package in normalized
        if package.type == "optional"
    )
    outdated = sum(
        1
        for package in normalized
        if package.status == "outdated"
    )
    conflicts = sum(
        1
        for package in normalized
        if package.status == "conflict"
    )

    return DependencyAnalysisResult(
        total=total,
        direct=direct,
        dev=dev,
        optional=optional,
        outdated=outdated,
        conflicts=conflicts,
        packages=normalized,
    )