
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Supported source files
# ---------------------------------------------------------------------------

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}

MANIFEST_FILES = {
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Pipfile",
    "Pipfile.lock",
    "setup.py",
    "setup.cfg",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".next",
    "coverage",
    ".idea",
    ".vscode",
}


# ---------------------------------------------------------------------------
# Public result types
# ---------------------------------------------------------------------------


ArchitectureToolResult = dict[str, Any]


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------


def _normalise_relative_path(
    workspace: Path,
    path: Path,
) -> str:
    """Return a POSIX-style repository-relative path."""

    try:
        relative = path.resolve().relative_to(workspace.resolve())
    except ValueError:
        relative = path

    return relative.as_posix()


def _safe_read_text(path: Path) -> str:
    """Read a source file without allowing one unreadable file to fail a scan."""

    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except (OSError, UnicodeError):
        return ""


def _iter_repository_files(workspace: Path):
    """
    Yield repository files while respecting the architecture scanner boundary.

    Generated dependencies, virtual environments, VCS metadata and build
    output are deliberately excluded.
    """

    if not workspace.exists() or not workspace.is_dir():
        return

    for path in workspace.rglob("*"):
        if not path.is_file():
            continue

        try:
            relative_parts = path.relative_to(workspace).parts
        except ValueError:
            continue

        if any(
            part in IGNORED_DIRECTORIES
            for part in relative_parts
        ):
            continue

        yield path


def _source_files(workspace: Path) -> list[Path]:
    """Return bounded source files in deterministic order."""

    files = [
        path
        for path in _iter_repository_files(workspace)
        if path.suffix.lower() in SOURCE_EXTENSIONS
    ]

    return sorted(
        files,
        key=lambda path: path.as_posix().lower(),
    )


# ---------------------------------------------------------------------------
# Technology detection
# ---------------------------------------------------------------------------


def _detect_python_technology(
    workspace: Path,
    files: list[Path],
) -> set[str]:
    technologies: set[str] = set()

    python_files = [
        path
        for path in files
        if path.suffix.lower() == ".py"
    ]

    if python_files:
        technologies.add("Python")

    manifest_paths = {
        path.name.lower(): path
        for path in _iter_repository_files(workspace)
        if path.name in MANIFEST_FILES
    }

    if "requirements.txt" in manifest_paths:
        requirements = _safe_read_text(
            manifest_paths["requirements.txt"]
        ).lower()

        if "fastapi" in requirements:
            technologies.add("FastAPI")

        if "sqlalchemy" in requirements:
            technologies.add("SQLAlchemy")

        if "alembic" in requirements:
            technologies.add("Alembic")

        if "langgraph" in requirements:
            technologies.add("LangGraph")

        if "psycopg" in requirements:
            technologies.add("PostgreSQL")

    if "pyproject.toml" in manifest_paths:
        content = _safe_read_text(
            manifest_paths["pyproject.toml"]
        ).lower()

        if "fastapi" in content:
            technologies.add("FastAPI")

        if "sqlalchemy" in content:
            technologies.add("SQLAlchemy")

        if "alembic" in content:
            technologies.add("Alembic")

        if "langgraph" in content:
            technologies.add("LangGraph")

    return technologies


def _detect_javascript_technology(
    workspace: Path,
    files: list[Path],
) -> set[str]:
    technologies: set[str] = set()

    javascript_files = [
        path
        for path in files
        if path.suffix.lower() in {
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
        }
    ]

    if not javascript_files:
        return technologies

    technologies.add("JavaScript/TypeScript")

    package_json = workspace / "package.json"

    if package_json.is_file():
        try:
            package_data = json.loads(
                _safe_read_text(package_json)
            )
        except json.JSONDecodeError:
            package_data = {}

        dependencies: dict[str, Any] = {}

        dependencies.update(
            package_data.get("dependencies", {})
        )

        dependencies.update(
            package_data.get("devDependencies", {})
        )

        dependency_names = {
            str(name).lower()
            for name in dependencies
        }

        if "next" in dependency_names:
            technologies.add("Next.js")

        if "react" in dependency_names:
            technologies.add("React")

        if "typescript" in dependency_names:
            technologies.add("TypeScript")

        if "tailwindcss" in dependency_names:
            technologies.add("Tailwind CSS")

    return technologies


def detect_technologies(
    workspace: Path,
    files: list[Path] | None = None,
) -> list[str]:
    """
    Detect technologies from actual repository contents.

    This function never invents a technology. A technology is returned only
    when there is source or manifest evidence for it.
    """

    if files is None:
        files = _source_files(workspace)

    technologies: set[str] = set()

    technologies.update(
        _detect_python_technology(
            workspace,
            files,
        )
    )

    technologies.update(
        _detect_javascript_technology(
            workspace,
            files,
        )
    )

    return sorted(
        technologies,
        key=str.lower,
    )


# ---------------------------------------------------------------------------
# Layer detection
# ---------------------------------------------------------------------------


def _layer_for_path(relative_path: str) -> tuple[str, str]:
    """
    Infer an application layer from repository structure.

    The result is intentionally conservative. Unknown directories become
    "Other" rather than being assigned an invented architectural meaning.
    """

    path = Path(relative_path)

    parts = [
        part.lower()
        for part in path.parts
    ]

    filename = path.name.lower()

    layer_map = (
        (
            {
                "api",
                "routes",
                "routers",
                "controllers",
                "endpoints",
            },
            "API",
        ),
        (
            {
                "services",
                "service",
                "usecases",
                "use_cases",
                "application",
            },
            "Services",
        ),
        (
            {
                "agents",
                "agent",
                "workflows",
                "workflow",
            },
            "Agents",
        ),
        (
            {
                "tools",
                "tool",
                "adapters",
                "integrations",
            },
            "Tools",
        ),
        (
            {
                "models",
                "model",
                "entities",
                "domain",
            },
            "Domain",
        ),
        (
            {
                "schemas",
                "schema",
            },
            "Schemas",
        ),
        (
            {
                "db",
                "database",
                "repositories",
                "repository",
                "persistence",
            },
            "Persistence",
        ),
        (
            {
                "components",
                "pages",
                "app",
                "src",
            },
            "Frontend",
        ),
        (
            {
                "tests",
                "test",
                "__tests__",
            },
            "Testing",
        ),
    )

    for directory_names, layer_name in layer_map:
        for part in parts[:-1]:
            if part in directory_names:
                return (
                    layer_name,
                    str(path.parent).replace("\\", "/"),
                )

    if (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or ".test." in filename
        or ".spec." in filename
    ):
        return (
            "Testing",
            str(path.parent).replace("\\", "/"),
        )

    if "main.py" == filename:
        return (
            "API",
            str(path.parent).replace("\\", "/"),
        )

    return (
        "Other",
        str(path.parent).replace("\\", "/"),
    )


def detect_layers(
    workspace: Path,
    files: list[Path],
) -> list[dict[str, str]]:
    """Build deterministic application-layer information."""

    layer_modules: dict[str, set[str]] = {}

    for path in files:
        relative_path = _normalise_relative_path(
            workspace,
            path,
        )

        layer_name, module = _layer_for_path(
            relative_path
        )

        layer_modules.setdefault(
            layer_name,
            set(),
        ).add(module)

    preferred_order = [
        "Frontend",
        "API",
        "Agents",
        "Services",
        "Tools",
        "Domain",
        "Schemas",
        "Persistence",
        "Testing",
        "Other",
    ]

    layers: list[dict[str, str]] = []

    for layer_name in preferred_order:
        modules = sorted(
            layer_modules.get(layer_name, set()),
            key=str.lower,
        )

        if not modules:
            continue

        module = modules[0]

        if len(modules) > 1:
            module = ", ".join(modules)

        layers.append(
            {
                "name": layer_name,
                "module": module,
            }
        )

    return layers


# ---------------------------------------------------------------------------
# Python import analysis
# ---------------------------------------------------------------------------


def _python_imports(
    path: Path,
) -> list[str]:
    """Extract Python import targets using the AST."""

    content = _safe_read_text(path)

    if not content:
        return []

    try:
        tree = ast.parse(
            content,
            filename=str(path),
        )
    except (SyntaxError, ValueError):
        return []

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(
                        alias.name.split(".")[0]
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(
                    node.module.split(".")[0]
                )

    return sorted(
        imports,
        key=str.lower,
    )


# ---------------------------------------------------------------------------
# JavaScript / TypeScript import analysis
# ---------------------------------------------------------------------------


def _javascript_imports(
    path: Path,
) -> list[str]:
    """
    Extract common JavaScript/TypeScript imports.

    This is intentionally lexical rather than a full JS parser so the
    architecture tool remains lightweight and deterministic.
    """

    content = _safe_read_text(path)

    if not content:
        return []

    imports: set[str] = set()

    lines = content.splitlines()

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("import "):
            if " from " in stripped:
                value = stripped.split(
                    " from ",
                    1,
                )[1].strip()
            else:
                value = stripped[len("import ") :].strip()

            value = value.strip(
                "; \t\r\n'\""
            )

            if value:
                imports.add(value)

        if stripped.startswith("export ") and " from " in stripped:
            value = stripped.split(
                " from ",
                1,
            )[1].strip()

            value = value.strip(
                "; \t\r\n'\""
            )

            if value:
                imports.add(value)

        if "require(" in stripped:
            fragment = stripped.split(
                "require(",
                1,
            )[1]

            fragment = fragment.split(
                ")",
                1,
            )[0]

            fragment = fragment.strip(
                " \t\r\n'\""
            )

            if fragment:
                imports.add(fragment)

    return sorted(
        imports,
        key=str.lower,
    )


def extract_imports(
    path: Path,
) -> list[str]:
    """Extract imports according to the source-file type."""

    suffix = path.suffix.lower()

    if suffix == ".py":
        return _python_imports(path)

    if suffix in {
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
    }:
        return _javascript_imports(path)

    return []


# ---------------------------------------------------------------------------
# Module construction
# ---------------------------------------------------------------------------


def _module_id(relative_path: str) -> str:
    """Create a stable module identifier."""

    path = Path(relative_path)

    if path.parent == Path("."):
        return path.stem

    return path.parent.as_posix()


def _responsibilities_for_file(
    path: Path,
    layer: str,
) -> list[str]:
    """Generate evidence-based responsibility labels."""

    filename = path.name.lower()

    responsibilities: list[str] = []

    if layer == "API":
        responsibilities.append(
            "Exposes application API endpoints"
        )

    elif layer == "Services":
        responsibilities.append(
            "Contains application service logic"
        )

    elif layer == "Agents":
        responsibilities.append(
            "Contains agent or workflow logic"
        )

    elif layer == "Tools":
        responsibilities.append(
            "Provides bounded analysis or integration tools"
        )

    elif layer == "Domain":
        responsibilities.append(
            "Defines domain models or persistence entities"
        )

    elif layer == "Schemas":
        responsibilities.append(
            "Defines structured input/output schemas"
        )

    elif layer == "Persistence":
        responsibilities.append(
            "Handles database or persistence concerns"
        )

    elif layer == "Testing":
        responsibilities.append(
            "Contains automated tests"
        )

    elif layer == "Frontend":
        responsibilities.append(
            "Contains frontend application code"
        )

    if filename in {
        "main.py",
        "app.py",
        "server.py",
    }:
        responsibilities.append(
            "Application entry point"
        )

    if "route" in filename:
        responsibilities.append(
            "Defines HTTP routing"
        )

    if "schema" in filename:
        responsibilities.append(
            "Defines validation structures"
        )

    if "service" in filename:
        responsibilities.append(
            "Implements service operations"
        )

    return sorted(
        set(responsibilities),
        key=str.lower,
    )


def build_modules(
    workspace: Path,
    files: list[Path],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, str]],
]:
    """
    Build module and module-relationship information.

    Relationships are derived from actual import statements. No relationship
    is created merely because two directories have similar names.
    """

    module_data: dict[str, dict[str, Any]] = {}

    path_to_module: dict[str, str] = {}

    for path in files:
        relative_path = _normalise_relative_path(
            workspace,
            path,
        )

        module_id = _module_id(
            relative_path
        )

        layer, _ = _layer_for_path(
            relative_path
        )

        module = module_data.setdefault(
            module_id,
            {
                "id": module_id,
                "name": Path(module_id).name,
                "layer": layer,
                "files": [],
                "responsibilities": set(),
                "dependencies": set(),
                "findings": [],
            },
        )

        module["files"].append(
            relative_path
        )

        module["responsibilities"].update(
            _responsibilities_for_file(
                path,
                layer,
            )
        )

        path_to_module[
            relative_path
        ] = module_id

    relationships: set[
        tuple[str, str, str]
    ] = set()

    all_module_ids = set(
        module_data
    )

    for path in files:
        relative_path = _normalise_relative_path(
            workspace,
            path,
        )

        source_module = path_to_module.get(
            relative_path
        )

        if not source_module:
            continue

        imports = extract_imports(path)

        for imported in imports:
            target_module: str | None = None

            # -----------------------------------------------------------
            # Local Python imports
            # -----------------------------------------------------------

            if path.suffix.lower() == ".py":
                imported_parts = imported.split(".")

                candidates = [
                    ".".join(imported_parts),
                    imported_parts[0],
                ]

                for candidate in candidates:
                    for module_id in all_module_ids:
                        if (
                            module_id == candidate
                            or module_id.endswith(
                                f"/{candidate}"
                            )
                            or module_id.endswith(
                                f".{candidate}"
                            )
                        ):
                            target_module = module_id
                            break

                    if target_module:
                        break

            # -----------------------------------------------------------
            # Local JS/TS imports
            # -----------------------------------------------------------

            else:
                if imported.startswith("."):
                    current_dir = Path(
                        relative_path
                    ).parent

                    candidate = (
                        current_dir / imported
                    ).as_posix()

                    candidate = str(
                        Path(candidate)
                    ).replace("\\", "/")

                    for module_id in all_module_ids:
                        if (
                            module_id == candidate
                            or module_id.startswith(
                                f"{candidate}/"
                            )
                        ):
                            target_module = module_id
                            break

            if not target_module:
                continue

            if target_module == source_module:
                continue

            module_data[
                source_module
            ]["dependencies"].add(
                target_module
            )

            relationships.add(
                (
                    source_module,
                    target_module,
                    "imports",
                )
            )

    modules: list[dict[str, Any]] = []

    for module_id in sorted(
        module_data,
        key=str.lower,
    ):
        data = module_data[module_id]

        modules.append(
            {
                "id": data["id"],
                "name": data["name"],
                "layer": data["layer"],
                "files": sorted(
                    data["files"],
                    key=str.lower,
                ),
                "responsibilities": sorted(
                    data["responsibilities"],
                    key=str.lower,
                ),
                "dependencies": sorted(
                    data["dependencies"],
                    key=str.lower,
                ),
                "findings": list(
                    data["findings"]
                ),
            }
        )

    relationship_results = [
        {
            "source": source,
            "target": target,
            "relationship_type": relationship_type,
        }
        for source, target, relationship_type
        in sorted(
            relationships,
            key=lambda value: (
                value[0].lower(),
                value[1].lower(),
                value[2].lower(),
            ),
        )
    ]

    return modules, relationship_results


# ---------------------------------------------------------------------------
# Architectural risk detection
# ---------------------------------------------------------------------------


def detect_architectural_risks(
    workspace: Path,
    files: list[Path],
    modules: list[dict[str, Any]],
    relationships: list[dict[str, str]],
) -> list[str]:
    """
    Detect conservative architectural risk signals.

    These are signals, not claims that the repository is insecure or broken.
    """

    risks: set[str] = set()

    layer_names = {
        module["layer"]
        for module in modules
    }

    if "Other" in layer_names:
        risks.add(
            "Some source files could not be assigned to a known application layer."
        )

    module_count = len(modules)

    if module_count == 1 and len(files) > 20:
        risks.add(
            "A large source set is concentrated in a single detected module."
        )

    # Detect unusually central modules.
    incoming: dict[str, int] = {}

    for relationship in relationships:
        target = relationship["target"]
        incoming[target] = incoming.get(
            target,
            0,
        ) + 1

    if incoming:
        most_imported_module, highest_count = max(
            incoming.items(),
            key=lambda item: item[1],
        )

        if highest_count >= 8:
            risks.add(
                "Module "
                f"'{most_imported_module}' "
                "has a high number of detected incoming import relationships."
            )

    # Detect oversized Python files.
    for path in files:
        if path.suffix.lower() != ".py":
            continue

        content = _safe_read_text(path)

        line_count = len(
            content.splitlines()
        )

        if line_count > 1000:
            relative_path = _normalise_relative_path(
                workspace,
                path,
            )

            risks.add(
                "Very large Python source file detected: "
                f"{relative_path} ({line_count} lines)."
            )

    # Detect architecture boundary violations conservatively.
    for relationship in relationships:
        source = relationship["source"].lower()
        target = relationship["target"].lower()

        source_layer = next(
            (
                module["layer"]
                for module in modules
                if module["id"].lower() == source
            ),
            None,
        )

        target_layer = next(
            (
                module["layer"]
                for module in modules
                if module["id"].lower() == target
            ),
            None,
        )

        if (
            source_layer == "Domain"
            and target_layer in {
                "API",
                "Frontend",
            }
        ):
            risks.add(
                "A detected domain module imports an outer application layer."
            )

    return sorted(
        risks,
        key=str.lower,
    )


# ---------------------------------------------------------------------------
# Public architecture analysis tool
# ---------------------------------------------------------------------------


def run_architecture_analysis(
    workspace: Path,
) -> ArchitectureToolResult:
    """
    Run the deterministic architecture analyzer.

    Input:
        workspace:
            Absolute repository workspace.

    Output:
        Structured architecture information suitable for a service/API layer.

    Guarantees:
        - deterministic ordering
        - no database writes
        - no external network access
        - no generated demo data
        - unreadable files do not terminate the scan
        - only files inside the supplied workspace are inspected
    """

    workspace = workspace.resolve()

    if not workspace.exists():
        raise FileNotFoundError(
            f"Repository workspace does not exist: {workspace}"
        )

    if not workspace.is_dir():
        raise NotADirectoryError(
            f"Repository workspace is not a directory: {workspace}"
        )

    files = _source_files(
        workspace
    )

    technologies = detect_technologies(
        workspace,
        files,
    )

    layers = detect_layers(
        workspace,
        files,
    )

    modules, relationships = build_modules(
        workspace,
        files,
    )

    risks = detect_architectural_risks(
        workspace,
        files,
        modules,
        relationships,
    )

    return {
        "technologies": technologies,
        "layers": layers,
        "modules": modules,
        "relationships": relationships,
        "risks": risks,
        "files_scanned": len(files),
    }


# ---------------------------------------------------------------------------
# Compatibility wrapper
# ---------------------------------------------------------------------------


def scan_architecture(
    workspace: Path,
) -> ArchitectureToolResult:
    """
    Compatibility alias used by services or agents.

    Keeps the public entry point concise while preserving the complete
    structured result.
    """

    return run_architecture_analysis(
        workspace=workspace
    )

