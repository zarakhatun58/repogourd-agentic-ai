
from pathlib import Path
from typing import TypedDict


class SecurityFinding(TypedDict):
    """
    Structured result returned by the security-analysis tool.
    """

    rule_id: str
    severity: str
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    matched_text: str


class SecurityScanResult(TypedDict):
    """
    Structured result returned by the complete security scan.
    """

    findings: list[SecurityFinding]
    files_scanned: int
    rules_executed: int


# ---------------------------------------------------------------------
# RepoGuard security rules
# ---------------------------------------------------------------------
#
# These rules intentionally remain deterministic and reproducible.
# The security tool detects candidate patterns; the agent workflow
# decides how the results are collected, evidenced, and verified.
#
# ---------------------------------------------------------------------

RULES = [
    (
        "RG001",
        "high",
        "Potential use of eval()",
        "The eval() function executes dynamically generated Python code.",
        "eval(",
        {".py"},
    ),
    (
        "RG002",
        "high",
        "Potential use of exec()",
        "The exec() function executes dynamically generated Python code.",
        "exec(",
        {".py"},
    ),
    (
        "RG003",
        "medium",
        "Hardcoded password detected",
        "A possible hardcoded password was found.",
        "password =",
        {".py", ".js", ".jsx", ".ts", ".tsx"},
    ),
    (
        "RG004",
        "medium",
        "Hardcoded secret detected",
        "A possible hardcoded secret was found.",
        "secret =",
        {".py", ".js", ".jsx", ".ts", ".tsx"},
    ),
    (
        "RG005",
        "high",
        "Potential dangerous eval() usage",
        "The eval() function can execute dynamically generated JavaScript.",
        "eval(",
        {".js", ".jsx", ".ts", ".tsx"},
    ),
    (
        "RG006",
        "high",
        "Potential command execution",
        "child_process APIs may introduce command injection risks.",
        "child_process",
        {".js", ".jsx", ".ts", ".tsx"},
    ),
    (
        "RG007",
        "high",
        "Potential unsafe HTML injection",
        "dangerouslySetInnerHTML may introduce XSS risks.",
        "dangerouslySetInnerHTML",
        {".jsx", ".tsx", ".js", ".ts"},
    ),
    (
        "RG008",
        "medium",
        "Insecure HTTP URL detected",
        "An HTTP URL may transmit data without encryption.",
        "http://",
        {".js", ".jsx", ".ts", ".tsx"},
    ),
]


def run_security_rule(
    workspace: Path,
    relative_path: str,
    rule,
) -> list[SecurityFinding]:
    """
    Execute one bounded security rule against one source file.

    Tool boundary:
        Input  -> workspace + relative source path + rule
        Output -> structured candidate findings

    This function does not:
    - create database records
    - collect evidence
    - verify findings
    - make final acceptance decisions
    - expose hidden reasoning
    """

    (
        rule_id,
        severity,
        title,
        description,
        pattern,
        extensions,
    ) = rule

    file_path = workspace / relative_path

    # -------------------------------------------------------------
    # File-type boundary
    # -------------------------------------------------------------

    if file_path.suffix.lower() not in extensions:
        return []

    if not file_path.is_file():
        return []

    try:
        content = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return []

    results: list[SecurityFinding] = []

    # -------------------------------------------------------------
    # Deterministic line-based detection
    # -------------------------------------------------------------

    for line_number, line in enumerate(
        content.splitlines(),
        start=1,
    ):
        normalized_line = line.lower().strip()

        if pattern.lower() not in normalized_line:
            continue

        results.append(
            {
                "rule_id": rule_id,
                "severity": severity,
                "title": title,
                "description": description,
                "file_path": relative_path,
                "line_start": line_number,
                "line_end": line_number,
                "matched_text": line.strip(),
            }
        )

    return results


def run_security_scan(
    workspace: Path,
    files: list[str],
) -> SecurityScanResult:
    """
    RepoGuard bounded security-analysis tool.

    The analysis agent calls this tool after repository inspection.

    Workflow position:

        Repository Inspection
                ↓
        Security Scanner  ← this tool
                ↓
        Evidence Collector
                ↓
        Verification
                ↓
        Final Result

    The scanner is deliberately deterministic. It does not pretend
    that simple pattern matching is autonomous AI reasoning.

    Parameters
    ----------
    workspace:
        Absolute or repository workspace path.

    files:
        Relative source-file paths selected by the repository
        inspection tool.

    Returns
    -------
    SecurityScanResult
        Structured scan output containing findings and execution
        metadata.
    """

    results: list[SecurityFinding] = []

    rules_executed = 0
    files_scanned = 0

    # -------------------------------------------------------------
    # Execute bounded rules against bounded files
    # -------------------------------------------------------------

    for relative_path in files:

        file_path = workspace / relative_path

        if not file_path.is_file():
            continue

        files_scanned += 1

        for rule in RULES:

            rules_executed += 1

            results.extend(
                run_security_rule(
                    workspace=workspace,
                    relative_path=relative_path,
                    rule=rule,
                )
            )

    # -------------------------------------------------------------
    # Structured tool output
    # -------------------------------------------------------------

    return {
        "findings": results,
        "files_scanned": files_scanned,
        "rules_executed": rules_executed,
    }


def scan_repository(
    workspace: Path,
    files: list[str],
) -> int:
    """
    Compatibility wrapper for the analysis agent.

    Returns only the number of findings while keeping the full
    structured result available through run_security_scan().
    """

    result = run_security_scan(
        workspace=workspace,
        files=files,
    )

    return len(result["findings"])

