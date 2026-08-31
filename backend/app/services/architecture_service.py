
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from app.models.repository import Repository


SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".cs",
    ".c",
    ".h",
    ".cpp",
    ".cc",
    ".hpp",
    ".swift",
    ".dart",
    ".vue",
    ".svelte",
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


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except (OSError, UnicodeError):
        return ""


def _resolve_workspace(repository: Repository) -> Path:
    for attribute in (
        "workspace_path",
        "workspace",
        "local_path",
        "path",
    ):
        value = getattr(repository, attribute, None)

        if value:
            path = Path(str(value)).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            return path.resolve()

    raise ValueError(
        "Repository does not contain a usable workspace path."
    )


def _collect_files(workspace: Path) -> list[Path]:
    if not workspace.exists() or not workspace.is_dir():
        return []

    files: list[Path] = []

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

        files.append(path)

    return sorted(
        files,
        key=lambda path: path.as_posix().lower(),
    )


# ---------------------------------------------------------------------------
# Technology detection
# ---------------------------------------------------------------------------

def _package_json_technologies(
    workspace: Path,
) -> set[str]:
    technologies: set[str] = set()

    package_json = workspace / "package.json"

    if not package_json.is_file():
        return technologies

    try:
        package_data = json.loads(
            _safe_read_text(package_json)
        )
    except json.JSONDecodeError:
        return technologies

    dependencies: dict[str, Any] = {}

    dependencies.update(
        package_data.get("dependencies", {})
    )

    dependencies.update(
        package_data.get("devDependencies", {})
    )

    names = {
        str(name).lower()
        for name in dependencies
    }

    technology_map = {
        "next": "Next.js",
        "react": "React",
        "react-dom": "React",
        "typescript": "TypeScript",
        "tailwindcss": "Tailwind CSS",
        "lucide-react": "Lucide",
        "framer-motion": "Framer Motion",
        "axios": "Axios",
        "zustand": "Zustand",
        "redux": "Redux",
        "@reduxjs/toolkit": "Redux Toolkit",
        "react-query": "React Query",
        "@tanstack/react-query": "TanStack Query",
        "zod": "Zod",
        "react-hook-form": "React Hook Form",
        "prisma": "Prisma",
        "@prisma/client": "Prisma",
        "drizzle-orm": "Drizzle ORM",
        "mongoose": "MongoDB / Mongoose",
        "express": "Express",
        "fastify": "Fastify",
        "vite": "Vite",
        "vitest": "Vitest",
        "jest": "Jest",
        "playwright": "Playwright",
        "cypress": "Cypress",
    }

    for package_name, technology in technology_map.items():
        if package_name.lower() in names:
            technologies.add(technology)

    return technologies


def _python_manifest_technologies(
    workspace: Path,
) -> set[str]:
    technologies: set[str] = set()

    manifests = [
        workspace / "requirements.txt",
        workspace / "requirements-dev.txt",
        workspace / "pyproject.toml",
        workspace / "Pipfile",
        workspace / "Pipfile.lock",
    ]

    content = ""

    for manifest in manifests:
        if manifest.is_file():
            content += "\n" + _safe_read_text(manifest).lower()

    if not content:
        return technologies

    technology_map = {
        "fastapi": "FastAPI",
        "starlette": "Starlette",
        "pydantic": "Pydantic",
        "sqlalchemy": "SQLAlchemy",
        "alembic": "Alembic",
        "psycopg": "PostgreSQL",
        "psycopg2": "PostgreSQL",
        "asyncpg": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "pymysql": "MySQL",
        "redis": "Redis",
        "celery": "Celery",
        "langgraph": "LangGraph",
        "langchain": "LangChain",
        "httpx": "HTTPX",
        "requests": "Requests",
        "pytest": "Pytest",
        "ruff": "Ruff",
        "mypy": "MyPy",
        "django": "Django",
        "flask": "Flask",
        "uvicorn": "Uvicorn",
        "gunicorn": "Gunicorn",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "scikit-learn": "Scikit-learn",
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
    }

    for package_name, technology in technology_map.items():
        if package_name in content:
            technologies.add(technology)

    return technologies


def _detect_technologies(
    workspace: Path,
    files: list[Path],
) -> list[str]:
    """
    Detect technologies from actual repository evidence.

    Sources:
    - source-file extensions
    - package.json
    - Python dependency manifests
    - Docker files
    - database/config files
    """

    detected: set[str] = set()

    extensions = {
        path.suffix.lower()
        for path in files
    }

    extension_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".kt": "Kotlin",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
        ".c": "C/C++",
        ".h": "C/C++",
        ".cpp": "C/C++",
        ".cc": "C/C++",
        ".hpp": "C/C++",
        ".swift": "Swift",
        ".dart": "Dart",
        ".vue": "Vue",
        ".svelte": "Svelte",
    }

    for extension, technology in extension_map.items():
        if extension in extensions:
            detected.add(technology)

    detected.update(
        _package_json_technologies(workspace)
    )

    detected.update(
        _python_manifest_technologies(workspace)
    )

    filenames = {
        path.name.lower()
        for path in files
    }

    if "package.json" in filenames:
        detected.add("Node.js")

    if "tsconfig.json" in filenames:
        detected.add("TypeScript")

    if "dockerfile" in filenames:
        detected.add("Docker")

    if (
        "docker-compose.yml" in filenames
        or "docker-compose.yaml" in filenames
    ):
        detected.add("Docker Compose")

    if "alembic.ini" in filenames:
        detected.add("Alembic")

    if "go.mod" in filenames:
        detected.add("Go")

    if "cargo.toml" in filenames:
        detected.add("Rust")

    if "pom.xml" in filenames:
        detected.add("Maven")

    if (
        "build.gradle" in filenames
        or "build.gradle.kts" in filenames
    ):
        detected.add("Gradle")

    return sorted(
        detected,
        key=str.lower,
    )


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------

def _detect_layer(
    relative_path: Path,
) -> tuple[str, str]:
    parts = [
        part.lower()
        for part in relative_path.parts[:-1]
    ]

    filename = relative_path.name.lower()

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
                "business",
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
                "dto",
                "dtos",
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
                "migrations",
            },
            "Persistence",
        ),
        (
            {
                "components",
                "pages",
                "frontend",
                "app",
            },
            "Frontend",
        ),
        (
            {
                "tests",
                "test",
                "__tests__",
                "spec",
                "specs",
            },
            "Testing",
        ),
    )

    for directories, layer_name in layer_map:
        for part in parts:
            if part in directories:
                return (
                    layer_name,
                    str(relative_path.parent).replace(
                        "\\",
                        "/",
                    ),
                )

    if (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or ".test." in filename
        or ".spec." in filename
    ):
        return (
            "Testing",
            str(relative_path.parent).replace(
                "\\",
                "/",
            ),
        )

    if filename in {
        "main.py",
        "app.py",
        "server.py",
    }:
        return (
            "API",
            str(relative_path.parent).replace(
                "\\",
                "/",
            ),
        )

    return (
        "Other",
        str(relative_path.parent).replace(
            "\\",
            "/",
        ),
    )


def _build_layers(
    workspace: Path,
    files: list[Path],
) -> list[dict[str, str]]:
    grouped: dict[str, set[str]] = {}

    for path in files:
        relative = path.relative_to(workspace)

        layer, module = _detect_layer(relative)

        grouped.setdefault(
            layer,
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

    result: list[dict[str, str]] = []

    for layer_name in preferred_order:
        modules = sorted(
            grouped.get(layer_name, set()),
            key=str.lower,
        )

        if not modules:
            continue

        result.append(
            {
                "name": layer_name,
                "module": ", ".join(modules),
            }
        )

    return result


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

def _python_imports(
    path: Path,
) -> list[str]:
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


def _javascript_imports(
    path: Path,
) -> list[str]:
    content = _safe_read_text(path)

    if not content:
        return []

    imports: set[str] = set()

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("import "):
            if " from " in stripped:
                value = stripped.split(
                    " from ",
                    1,
                )[1].strip()
            else:
                value = stripped[len("import "):].strip()

            value = value.strip(
                "; \t\r\n'\""
            )

            if value:
                imports.add(value)

        if (
            stripped.startswith("export ")
            and " from " in stripped
        ):
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


def _extract_imports(
    path: Path,
) -> list[str]:
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
# Modules
# ---------------------------------------------------------------------------

def _module_id(relative_path: str) -> str:
    path = Path(relative_path)

    if path.parent == Path("."):
        return path.stem

    return path.parent.as_posix()


def _responsibilities(
    layer: str,
    files: list[Path],
) -> list[str]:
    result: set[str] = set()

    if layer == "API":
        result.add(
            "Exposes application API endpoints."
        )

    elif layer == "Services":
        result.add(
            "Contains application and business logic."
        )

    elif layer == "Agents":
        result.add(
            "Contains agent orchestration and workflow logic."
        )

    elif layer == "Tools":
        result.add(
            "Provides analysis or integration tools."
        )

    elif layer == "Domain":
        result.add(
            "Defines domain models and entities."
        )

    elif layer == "Schemas":
        result.add(
            "Defines validation and serialization schemas."
        )

    elif layer == "Persistence":
        result.add(
            "Handles persistence and database concerns."
        )

    elif layer == "Frontend":
        result.add(
            "Contains frontend application code."
        )

    elif layer == "Testing":
        result.add(
            "Contains automated tests."
        )

    if not result:
        result.add(
            f"Contains {len(files)} repository file(s)."
        )

    return sorted(
        result,
        key=str.lower,
    )


def _build_modules(
    workspace: Path,
    files: list[Path],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, str]],
]:
    module_data: dict[str, dict[str, Any]] = {}

    path_to_module: dict[str, str] = {}

    for path in files:
        relative = path.relative_to(workspace)
        relative_string = relative.as_posix()

        module_id = _module_id(
            relative_string
        )

        layer, _ = _detect_layer(relative)

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
            relative_string
        )

        module["responsibilities"].update(
            _responsibilities(
                layer,
                [path],
            )
        )

        path_to_module[
            relative_string
        ] = module_id

    relationships: set[
        tuple[str, str, str]
    ] = set()

    all_module_ids = set(
        module_data
    )

    for path in files:
        relative = path.relative_to(workspace)
        relative_string = relative.as_posix()

        source_module = path_to_module.get(
            relative_string
        )

        if not source_module:
            continue

        for imported in _extract_imports(path):
            target_module = None

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

            elif imported.startswith("."):
                current_dir = relative.parent

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
                )[:100],
                "responsibilities": sorted(
                    data["responsibilities"],
                    key=str.lower,
                ),
                "dependencies": sorted(
                    data["dependencies"],
                    key=str.lower,
                ),
                "findings": data["findings"],
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
# Risks
# ---------------------------------------------------------------------------

def _detect_architecture_risks(
    workspace: Path,
    files: list[Path],
    modules: list[dict[str, Any]],
) -> list[str]:
    risks: list[str] = []

    source_files = [
        path
        for path in files
        if path.suffix.lower()
        in SOURCE_EXTENSIONS
    ]

    test_files = [
        path
        for path in source_files
        if (
            path.name.lower().startswith("test_")
            or "_test." in path.name.lower()
            or ".test." in path.name.lower()
            or ".spec." in path.name.lower()
        )
    ]

    if source_files and not test_files:
        risks.append(
            "No recognizable automated test files were detected."
        )

    if len(source_files) > 500:
        risks.append(
            "Repository contains more than 500 source files; "
            "module boundaries may require additional review."
        )

    module_names = {
        module["name"].lower()
        for module in modules
    }

    if (
        "api" in module_names
        and "services" not in module_names
        and "service" not in module_names
    ):
        risks.append(
            "API code was detected without a recognizable service layer."
        )

    if (
        "models" in module_names
        and "schemas" not in module_names
    ):
        risks.append(
            "Persistent models were detected without a recognizable "
            "schema/DTO layer."
        )

    return sorted(
        set(risks),
        key=str.lower,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_architecture(
    repository: Repository,
) -> dict[str, Any]:
    workspace = _resolve_workspace(
        repository
    )

    if not workspace.exists():
        raise FileNotFoundError(
            f"Repository workspace does not exist: {workspace}"
        )

    if not workspace.is_dir():
        raise ValueError(
            f"Repository workspace is not a directory: {workspace}"
        )

    files = _collect_files(
        workspace
    )

    technologies = _detect_technologies(
        workspace,
        files,
    )

    layers = _build_layers(
        workspace,
        files,
    )

    modules, relationships = _build_modules(
        workspace,
        files,
    )

    risks = _detect_architecture_risks(
        workspace,
        files,
        modules,
    )

    return {
        "technologies": technologies,
        "layers": layers,
        "modules": modules,
        "relationships": relationships,
        "risks": risks,
        "files_scanned": len(files),
    }


def architecture_analysis_for_repository(
    repository: Repository,
) -> dict[str, Any]:
    return analyze_architecture(
        repository
    )

