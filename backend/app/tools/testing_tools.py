
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict


class TestingCategoryResult(TypedDict):
    name: str
    count: int


class TestingToolResult(TypedDict):
    test_files: int
    test_suites: int
    passed: int
    failed: int
    coverage: float | None
    coverage_source: str
    framework: str
    categories: list[TestingCategoryResult]
    missing_areas: list[str]
    execution_status: str
    files_scanned: int


# ---------------------------------------------------------------------
# Test file detection
# ---------------------------------------------------------------------

TEST_FILE_PATTERNS = (
    re.compile(r"(^|/)test_[^/]+\.py$", re.IGNORECASE),
    re.compile(r"(^|/)[^/]+_test\.py$", re.IGNORECASE),
    re.compile(r"(^|/)tests?/[^/]+\.py$", re.IGNORECASE),
    re.compile(r"(^|/)[^/]+\.(test|spec)\.(js|jsx|ts|tsx)$", re.IGNORECASE),
)


SUPPORTED_SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".next",
    "dist",
    "build",
}


def _relative_files(workspace: Path) -> list[str]:
    """
    Return bounded repository-relative files.

    Hidden build/cache directories and virtual environments are ignored.
    """

    files: list[str] = []

    if not workspace.exists() or not workspace.is_dir():
        return files

    for path in workspace.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(workspace)

        if any(
            part in IGNORED_DIRECTORIES
            for part in relative.parts
        ):
            continue

        files.append(relative.as_posix())

    return files


def _is_test_file(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")

    return any(
        pattern.search(normalized)
        for pattern in TEST_FILE_PATTERNS
    )


def _detect_framework(
    test_files: list[str],
    workspace: Path,
) -> str:
    """
    Detect common testing frameworks from repository files.

    Detection is intentionally conservative.
    """

    # Python
    pyproject = workspace / "pyproject.toml"
    requirements = workspace / "requirements.txt"

    python_text = ""

    for candidate in (pyproject, requirements):
        if candidate.is_file():
            try:
                python_text += candidate.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).lower()
            except OSError:
                pass

    if "pytest" in python_text:
        return "pytest"

    if "unittest" in python_text:
        return "unittest"

    # JavaScript / TypeScript
    package_json = workspace / "package.json"

    if package_json.is_file():
        try:
            data = json.loads(
                package_json.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            )

            dependency_text = json.dumps(
                {
                    "dependencies": data.get(
                        "dependencies",
                        {},
                    ),
                    "devDependencies": data.get(
                        "devDependencies",
                        {},
                    ),
                }
            ).lower()

            if "vitest" in dependency_text:
                return "vitest"

            if "jest" in dependency_text:
                return "jest"

            if "mocha" in dependency_text:
                return "mocha"

        except (OSError, json.JSONDecodeError):
            pass

    # Infer from file naming if configuration isn't available.
    joined = " ".join(test_files).lower()

    if ".spec." in joined or ".test." in joined:
        return "javascript/typescript test runner"

    if test_files:
        return "python test suite"

    return "unknown"


def _count_test_suites(
    workspace: Path,
    test_files: list[str],
) -> int:
    """
    Approximate suite count from common test declarations.

    This is static analysis only. It does not execute tests.
    """

    suites = 0

    for relative_path in test_files:
        file_path = workspace / relative_path

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            continue

        suffix = file_path.suffix.lower()

        if suffix == ".py":
            suites += len(
                re.findall(
                    r"^\s*class\s+Test[A-Za-z0-9_]*",
                    content,
                    re.MULTILINE,
                )
            )

            function_tests = len(
                re.findall(
                    r"^\s*def\s+test_[A-Za-z0-9_]*",
                    content,
                    re.MULTILINE,
                )
            )

            suites += function_tests

        elif suffix in {".js", ".jsx", ".ts", ".tsx"}:
            suites += len(
                re.findall(
                    r"\b(?:describe|suite)\s*\(",
                    content,
                    re.IGNORECASE,
                )
            )

    # If tests exist but no explicit suite declaration was found,
    # treat the test files themselves as suites.
    return max(suites, len(test_files))


def _detect_categories(
    workspace: Path,
    test_files: list[str],
) -> list[TestingCategoryResult]:
    categories = {
        "unit": 0,
        "integration": 0,
        "end-to-end": 0,
    }

    for relative_path in test_files:
        normalized = relative_path.lower()

        if any(
            token in normalized
            for token in (
                "integration",
                "e2e",
                "end_to_end",
                "end-to-end",
            )
        ):
            categories["integration" if "integration" in normalized else "end-to-end"] += 1
            continue

        # Inspect content for common integration/e2e signals.
        file_path = workspace / relative_path

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()
        except OSError:
            content = ""

        if any(
            token in content
            for token in (
                "testclient",
                "httpx",
                "playwright",
                "selenium",
                "cypress",
            )
        ):
            if any(
                token in content
                for token in (
                    "playwright",
                    "selenium",
                    "cypress",
                )
            ):
                categories["end-to-end"] += 1
            else:
                categories["integration"] += 1
        else:
            categories["unit"] += 1

    return [
        {
            "name": name,
            "count": count,
        }
        for name, count in categories.items()
        if count > 0
    ]


def _detect_missing_areas(
    workspace: Path,
    test_files: list[str],
    source_files: list[str],
) -> list[str]:
    """
    Identify obvious testing gaps from repository structure.

    This does not claim that an area is definitively untested.
    """

    missing: list[str] = []

    if not test_files:
        return [
            "No test files detected.",
            "Unit tests are missing or could not be detected.",
            "Integration tests are missing or could not be detected.",
            "End-to-end tests are missing or could not be detected.",
        ]

    normalized_tests = [
        path.lower()
        for path in test_files
    ]

    has_unit = any(
        "test" in path
        and not any(
            token in path
            for token in (
                "integration",
                "e2e",
                "end_to_end",
                "end-to-end",
            )
        )
        for path in normalized_tests
    )

    has_integration = any(
        "integration" in path
        for path in normalized_tests
    )

    has_e2e = any(
        token in path
        for path in normalized_tests
        for token in (
            "e2e",
            "end_to_end",
            "end-to-end",
        )
    )

    if not has_unit:
        missing.append(
            "No clearly identifiable unit-test area was detected."
        )

    if not has_integration:
        missing.append(
            "No clearly identifiable integration-test area was detected."
        )

    if not has_e2e:
        missing.append(
            "No clearly identifiable end-to-end test area was detected."
        )

    if source_files and len(test_files) < max(
        1,
        len(source_files) // 5,
    ):
        missing.append(
            "Test-file count is low relative to the detected source-file count."
        )

    return missing


def _detect_coverage(
    workspace: Path,
) -> tuple[float | None, str]:
    """
    Read coverage information if it already exists.

    The tool does not fabricate coverage values.
    """

    candidates = [
        workspace / "coverage.json",
        workspace / ".coverage.json",
    ]

    for candidate in candidates:
        if not candidate.is_file():
            continue

        try:
            data = json.loads(
                candidate.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            )
        except (OSError, json.JSONDecodeError):
            continue

        totals = data.get("totals")

        if isinstance(totals, dict):
            percent = totals.get("percent_covered")

            if isinstance(percent, (int, float)):
                return float(percent), "coverage.json"

    return None, "not_available"


def run_testing_analysis(
    workspace: Path,
) -> TestingToolResult:
    """
    Analyze repository testing structure.

    Important:
    - Does not execute arbitrary repository tests.
    - Does not modify repository files.
    - Does not create database records.
    - Does not invent coverage.
    """

    all_files = _relative_files(workspace)

    source_files = [
        path
        for path in all_files
        if Path(path).suffix.lower()
        in SUPPORTED_SOURCE_EXTENSIONS
    ]

    test_files = [
        path
        for path in all_files
        if _is_test_file(path)
    ]

    framework = _detect_framework(
        test_files=test_files,
        workspace=workspace,
    )

    test_suites = _count_test_suites(
        workspace=workspace,
        test_files=test_files,
    )

    categories = _detect_categories(
        workspace=workspace,
        test_files=test_files,
    )

    missing_areas = _detect_missing_areas(
        workspace=workspace,
        test_files=test_files,
        source_files=source_files,
    )

    coverage, coverage_source = _detect_coverage(
        workspace=workspace,
    )

    return {
        "test_files": len(test_files),
        "test_suites": test_suites,
        "passed": 0,
        "failed": 0,
        "coverage": coverage,
        "coverage_source": coverage_source,
        "framework": framework,
        "categories": categories,
        "missing_areas": missing_areas,
        "execution_status": "not_run",
        "files_scanned": len(all_files),
    }

