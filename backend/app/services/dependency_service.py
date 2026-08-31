
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


IGNORED_DIRECTORIES = {
    ".git",
    ".next",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "coverage",
}

MAX_FILE_SIZE = 5 * 1024 * 1024


def _find_workspace(repository: Any) -> Path:
    workspace = getattr(repository, "workspace", None)

    if not workspace:
        workspace = getattr(repository, "workspace_path", None)

    if not workspace:
        raise ValueError("Repository workspace path is not configured.")

    path = Path(str(workspace)).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Repository workspace does not exist: {path}"
        )

    if not path.is_dir():
        raise ValueError(
            f"Repository workspace is not a directory: {path}"
        )

    return path


def _ignored(path: Path, workspace: Path) -> bool:
    try:
        relative = path.relative_to(workspace)
    except ValueError:
        return True

    return any(
        part in IGNORED_DIRECTORIES
        for part in relative.parts
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as file:
            value = json.load(file)

        return value if isinstance(value, dict) else {}

    except (OSError, json.JSONDecodeError):
        return {}


def _normalize_package_name(value: str) -> str:
    return value.strip()


def _node_dependencies(
    workspace: Path,
) -> list[dict[str, str]]:
    package_file = workspace / "package.json"

    if not package_file.is_file():
        return []

    package_data = _read_json(package_file)

    results: list[dict[str, str]] = []

    dependencies = package_data.get("dependencies", {})
    dev_dependencies = package_data.get("devDependencies", {})

    if isinstance(dependencies, dict):
        for package, version in dependencies.items():
            results.append(
                {
                    "package": _normalize_package_name(str(package)),
                    "version": str(version),
                    "type": "prod",
                    "status": "ok",
                    "risk": "low",
                }
            )

    if isinstance(dev_dependencies, dict):
        for package, version in dev_dependencies.items():
            results.append(
                {
                    "package": _normalize_package_name(str(package)),
                    "version": str(version),
                    "type": "dev",
                    "status": "ok",
                    "risk": "low",
                }
            )

    return results


def _python_dependencies(
    workspace: Path,
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    requirements = workspace / "requirements.txt"

    if requirements.is_file():
        try:
            content = requirements.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            content = ""

        for raw_line in content.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith(("#", "-", "git+")):
                continue

            match = re.match(
                r"^([A-Za-z0-9_.-]+)\s*(.*)$",
                line,
            )

            if not match:
                continue

            package = match.group(1)
            version = match.group(2).strip() or "*"

            results.append(
                {
                    "package": package,
                    "version": version,
                    "type": "prod",
                    "status": "ok",
                    "risk": "low",
                }
            )

    pyproject = workspace / "pyproject.toml"

    if pyproject.is_file():
        try:
            content = pyproject.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            content = ""

        in_dependencies = False

        for raw_line in content.splitlines():
            line = raw_line.strip()

            if line.startswith("["):
                in_dependencies = (
                    line == "[project]"
                    or line == "[tool.poetry.dependencies]"
                )

            if not in_dependencies:
                continue

            match = re.match(
                r'^["\']?([A-Za-z0-9_.-]+)["\']?\s*=\s*(.+)$',
                line,
            )

            if not match:
                continue

            package = match.group(1)

            if package.lower() in {
                "name",
                "version",
                "description",
                "requires-python",
            }:
                continue

            version = match.group(2).strip()

            results.append(
                {
                    "package": package,
                    "version": version,
                    "type": "prod",
                    "status": "ok",
                    "risk": "low",
                }
            )

    return results


def _go_dependencies(
    workspace: Path,
) -> list[dict[str, str]]:
    path = workspace / "go.mod"

    if not path.is_file():
        return []

    try:
        content = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError:
        return []

    results: list[dict[str, str]] = []

    for line in content.splitlines():
        line = line.strip()

        if not line or line.startswith("//"):
            continue

        match = re.match(
            r"^([A-Za-z0-9._/~:-]+)\s+(v[^\s]+)",
            line,
        )

        if not match:
            continue

        results.append(
            {
                "package": match.group(1),
                "version": match.group(2),
                "type": "prod",
                "status": "ok",
                "risk": "low",
            }
        )

    return results


def _java_dependencies(
    workspace: Path,
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    pom = workspace / "pom.xml"

    if pom.is_file():
        try:
            content = pom.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            content = ""

        dependency_blocks = re.findall(
            r"<dependency>(.*?)</dependency>",
            content,
            flags=re.DOTALL,
        )

        for block in dependency_blocks:
            group = re.search(
                r"<groupId>(.*?)</groupId>",
                block,
            )
            artifact = re.search(
                r"<artifactId>(.*?)</artifactId>",
                block,
            )
            version = re.search(
                r"<version>(.*?)</version>",
                block,
            )

            if not group or not artifact:
                continue

            package = (
                f"{group.group(1).strip()}:"
                f"{artifact.group(1).strip()}"
            )

            results.append(
                {
                    "package": package,
                    "version": (
                        version.group(1).strip()
                        if version
                        else "*"
                    ),
                    "type": "prod",
                    "status": "ok",
                    "risk": "low",
                }
            )

    return results


def _deduplicate(
    packages: list[dict[str, str]],
) -> list[dict[str, str]]:
    unique: dict[tuple[str, str], dict[str, str]] = {}

    for package in packages:
        key = (
            package["package"].lower(),
            package["type"],
        )

        unique[key] = package

    return sorted(
        unique.values(),
        key=lambda item: (
            item["package"].lower(),
            item["type"],
        ),
    )


def _risk_for_dependency(
    package: dict[str, str],
) -> str:
    name = package["package"].lower()

    high_risk_patterns = (
        "eval",
        "shell",
        "command",
        "exec",
        "pickle",
        "des",
        "md5",
    )

    medium_risk_patterns = (
        "crypto",
        "auth",
        "jwt",
        "http",
        "request",
        "xml",
    )

    if any(pattern in name for pattern in high_risk_patterns):
        return "high"

    if any(pattern in name for pattern in medium_risk_patterns):
        return "medium"

    return "low"


def _apply_risk(
    packages: list[dict[str, str]],
) -> None:
    for package in packages:
        package["risk"] = _risk_for_dependency(package)


def _detect_conflicts(
    packages: list[dict[str, str]],
) -> int:
    """
    Detect packages that occur in both production and development
    dependency sets with different versions.
    """
    grouped: dict[str, dict[str, set[str]]] = {}

    for package in packages:
        name = package["package"].lower()

        grouped.setdefault(
            name,
            {
                "prod": set(),
                "dev": set(),
            },
        )

        grouped[name][package["type"]].add(
            package["version"]
        )

    conflicts = 0

    for dependency in grouped.values():
        prod = dependency["prod"]
        dev = dependency["dev"]

        if prod and dev and prod != dev:
            conflicts += 1

    return conflicts


def _mark_outdated_candidates(
    packages: list[dict[str, str]],
) -> None:
    """
    Deterministically mark obviously unconstrained dependencies.

    This does not claim that a package is actually outdated without
    consulting a package registry. A wildcard/unbounded version is
    therefore reported as a review candidate.
    """
    for package in packages:
        version = package["version"].strip()

        if version in {"*", "", "latest"}:
            package["status"] = "review"


def analyze_dependencies(
    repository: Any,
) -> dict[str, Any]:
    """
    Perform deterministic dependency analysis against a repository.

    Supported manifests:
        package.json
        requirements.txt
        pyproject.toml
        go.mod
        pom.xml
    """
    workspace = _find_workspace(repository)

    packages: list[dict[str, str]] = []

    packages.extend(_node_dependencies(workspace))
    packages.extend(_python_dependencies(workspace))
    packages.extend(_go_dependencies(workspace))
    packages.extend(_java_dependencies(workspace))

    packages = _deduplicate(packages)

    _apply_risk(packages)
    _mark_outdated_candidates(packages)

    total = len(packages)
    direct = sum(
        1
        for package in packages
        if package["type"] == "prod"
    )
    dev = sum(
        1
        for package in packages
        if package["type"] == "dev"
    )
    outdated = sum(
        1
        for package in packages
        if package["status"] == "review"
    )

    conflicts = _detect_conflicts(packages)

    return {
        "total": total,
        "direct": direct,
        "dev": dev,
        "outdated": outdated,
        "conflicts": conflicts,
        "packages": packages,
        "manifests": [
            name
            for name in (
                "package.json",
                "requirements.txt",
                "pyproject.toml",
                "go.mod",
                "pom.xml",
            )
            if (workspace / name).is_file()
        ],
    }

