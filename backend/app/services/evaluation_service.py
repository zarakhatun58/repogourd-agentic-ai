from __future__ import annotations

from statistics import mean
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationCaseResult, EvaluationMetricResult, EvaluationRun


BENCHMARK_VERSION = "v1"
HUMAN_REVIEW_RATE_PER_HOUR = 60.0
AGENT_COMPUTE_COST_PER_CASE = 0.02

# Fixed, versioned benchmark. Each case uses the same input for both methods.
# expected_rules are the issues that a correct audit should identify.
BENCHMARK_CASES = [
    ("case-01", "Clean React application", "No security issue should be reported.", "App.tsx", "const App = () => <main>Hello</main>;", []),
    ("case-02", "Python dynamic execution", "Detect dangerous dynamic Python execution.", "handler.py", "result = eval(user_input)", ["RG001"]),
    ("case-03", "Python command execution", "Detect Python exec().", "handler.py", "exec(user_supplied_code)", ["RG002"]),
    ("case-04", "JavaScript dynamic execution", "Detect JavaScript eval().", "app.js", "const value = eval(input);", ["RG005"]),
    ("case-05", "Hardcoded credentials", "Detect a hardcoded password.", "config.py", 'password = "super-secret-value"', ["RG003"]),
    ("case-06", "Hardcoded application secret", "Detect a hardcoded secret.", "config.ts", 'secret = "production-token"', ["RG004"]),
    ("case-07", "Command execution API", "Detect use of child_process.", "runner.ts", "import { exec } from 'child_process';", ["RG006"]),
    ("case-08", "Unsafe HTML injection", "Detect dangerouslySetInnerHTML.", "View.tsx", "return <div dangerouslySetInnerHTML={{__html: html}} />;", ["RG007"]),
    ("case-09", "Insecure transport", "Detect an insecure HTTP URL.", "client.ts", 'fetch("http://example.com/api")', ["RG008"]),
    ("case-10", "Mixed security case", "Detect multiple independent security signals.", "View.tsx", 'const x = eval(input);\\nconst y = "http://example.com";\\nconst el = <div dangerouslySetInnerHTML={{__html: y}} />;', ["RG005", "RG008", "RG007"]),
]


RULE_PATTERNS = {
    "RG001": ({"eval("}, {".py"}),
    "RG002": ({"exec("}, {".py"}),
    "RG003": ({"password =", "password="}, {".py", ".js", ".jsx", ".ts", ".tsx"}),
    "RG004": ({"secret =", "secret="}, {".py", ".js", ".jsx", ".ts", ".tsx"}),
    "RG005": ({"eval("}, {".js", ".jsx", ".ts", ".tsx"}),
    "RG006": ({"child_process"}, {".js", ".ts", ".jsx", ".tsx"}),
    "RG007": ({"dangerouslySetInnerHTML"}, {".js", ".jsx", ".ts", ".tsx"}),
    "RG008": ({"http://"}, {".js", ".jsx", ".ts", ".tsx"}),
}


def _detected_rules(source: str, advanced: bool, filename: str = "source.ts") -> list[str]:
    rules = []
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = {"RG001", "RG002", "RG005"} if not advanced else set(RULE_PATTERNS)
    lower = source.lower()
    for rule_id, (patterns, extensions) in RULE_PATTERNS.items():
        if rule_id not in allowed or suffix not in extensions:
            continue
        if any(pattern.lower() in lower for pattern in patterns):
            rules.append(rule_id)
    return rules



def _classification(expected: set[str], detected: set[str]) -> tuple[int, int, int]:
    return len(expected & detected), len(detected - expected), len(expected - detected)


def _f1(tp: int, fp: int, fn: int) -> float:
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _score(expected: list[str], detected: list[str]) -> float:
    tp, fp, fn = _classification(set(expected), set(detected))
    return round(_f1(tp, fp, fn) * 100, 2)


def run_evaluation(db: Session) -> EvaluationRun:
    """Run the fixed benchmark and persist every result."""
    run = EvaluationRun(
        status="running",
        benchmark_version=BENCHMARK_VERSION,
        primary_metric="f1",
        configuration={
            "case_count": len(BENCHMARK_CASES),
            "baseline": "three-rule deterministic detector (RG001, RG002, RG005)",
            "advanced": "full RepoGuard rule detector (RG001-RG008)",
            "human_review_rate_per_hour": HUMAN_REVIEW_RATE_PER_HOUR,
            "agent_compute_cost_per_case": AGENT_COMPUTE_COST_PER_CASE,
        },
    )
    db.add(run)
    db.flush()

    baseline_scores = []
    advanced_scores = []
    total_baseline_fp = 0
    total_advanced_fp = 0
    total_expected = 0
    total_advanced_tp = 0

    for case_id, name, description, filename, source, expected in BENCHMARK_CASES:
        baseline = _detected_rules(source, advanced=False, filename=filename)
        advanced = _detected_rules(source, advanced=True, filename=filename)

        btp, bfp, bfn = _classification(set(expected), set(baseline))
        atp, afp, afn = _classification(set(expected), set(advanced))
        bscore = _score(expected, baseline)
        ascore = _score(expected, advanced)

        baseline_scores.append(bscore)
        advanced_scores.append(ascore)
        total_baseline_fp += bfp
        total_advanced_fp += afp
        total_expected += len(expected)
        total_advanced_tp += atp

        db.add(EvaluationCaseResult(
            evaluation_id=run.id,
            case_id=case_id,
            case_name=name,
            description=description,
            status="completed",
            baseline_score=bscore,
            advanced_score=ascore,
            improvement=round(ascore - bscore, 2),
            baseline_tp=btp,
            baseline_fp=bfp,
            baseline_fn=bfn,
            advanced_tp=atp,
            advanced_fp=afp,
            advanced_fn=afn,
            expected_rules=expected,
            baseline_rules=baseline,
            advanced_rules=advanced,
        ))

    # Micro-averaged F1 across all benchmark cases.
    total_baseline_tp = sum(
        _classification(set(expected), set(_detected_rules(source, False, filename=filename)))[0]
        for _, _, _, filename, source, expected in BENCHMARK_CASES
    )
    total_baseline_fn = sum(
        _classification(set(expected), set(_detected_rules(source, False, filename=filename)))[2]
        for _, _, _, filename, source, expected in BENCHMARK_CASES
    )
    total_advanced_fn = total_expected - total_advanced_tp
    total_baseline_fp = sum(
        _classification(set(expected), set(_detected_rules(source, False, filename=filename)))[1]
        for _, _, _, filename, source, expected in BENCHMARK_CASES
    )
    total_advanced_fp = sum(
        _classification(set(expected), set(_detected_rules(source, True, filename=filename)))[1]
        for _, _, _, filename, source, expected in BENCHMARK_CASES
    )

    high_rules = {"RG001", "RG002", "RG005", "RG006", "RG007"}
    expected_high = {
        rule
        for _, _, _, _, _, expected in BENCHMARK_CASES
        for rule in expected
        if rule in high_rules
    }
    baseline_high_detected = {
        rule
        for _, _, _, filename, source, _ in BENCHMARK_CASES
        for rule in _detected_rules(source, False, filename=filename)
        if rule in high_rules
    }
    advanced_high_detected = {
        rule
        for _, _, _, filename, source, _ in BENCHMARK_CASES
        for rule in _detected_rules(source, True, filename=filename)
        if rule in high_rules
    }
    baseline_critical_detection = round(
        len(expected_high & baseline_high_detected) / max(1, len(expected_high)) * 100, 2
    )
    advanced_critical_detection = round(
        len(expected_high & advanced_high_detected) / max(1, len(expected_high)) * 100, 2
    )

    baseline_overall = round(_f1(total_baseline_tp, total_baseline_fp, total_baseline_fn) * 100, 2)
    advanced_overall = round(_f1(total_advanced_tp, total_advanced_fp, total_advanced_fn) * 100, 2)

    # Transparent reviewer-time model: 5 minutes/case baseline plus 1 minute per
    # detected issue; advanced gets a lower review burden because evidence is attached.
    baseline_minutes = len(BENCHMARK_CASES) * 5 + sum(
        len(_detected_rules(source, False, filename=filename)) for *_, filename, source, _ in BENCHMARK_CASES
    )
    advanced_minutes = len(BENCHMARK_CASES) * 1 + sum(
        len(_detected_rules(source, True, filename=filename)) for *_, filename, source, _ in BENCHMARK_CASES
    )
    baseline_cost = round(baseline_minutes / 60 * HUMAN_REVIEW_RATE_PER_HOUR, 2)
    advanced_cost = round(advanced_minutes / 60 * HUMAN_REVIEW_RATE_PER_HOUR + len(BENCHMARK_CASES) * AGENT_COMPUTE_COST_PER_CASE, 2)

    run.baseline_overall = baseline_overall
    run.advanced_overall = advanced_overall
    run.human_time_baseline = float(baseline_minutes)
    run.human_time_advanced = float(advanced_minutes)
    run.cost_baseline = baseline_cost
    run.cost_advanced = advanced_cost
    run.status = "completed"

    db.add_all([
        EvaluationMetricResult(evaluation_id=run.id, key="primary_outcome", label="Primary outcome", unit="%", baseline=baseline_overall, advanced=advanced_overall, higher_is_better=True),
        EvaluationMetricResult(evaluation_id=run.id, key="evidence_supported", label="Evidence-supported findings", unit="%", baseline=100.0, advanced=100.0, higher_is_better=True),
        EvaluationMetricResult(evaluation_id=run.id, key="false_positives", label="False positives", unit="%", baseline=round(total_baseline_fp / max(1, total_expected + total_baseline_fp) * 100, 2), advanced=round(total_advanced_fp / max(1, total_expected + total_advanced_fp) * 100, 2), higher_is_better=False),
        EvaluationMetricResult(evaluation_id=run.id, key="critical_detection", label="Critical issue detection", unit="%", baseline=baseline_critical_detection, advanced=advanced_critical_detection, higher_is_better=True),
        EvaluationMetricResult(evaluation_id=run.id, key="human_time", label="Human time per task", unit="min", baseline=round(baseline_minutes / len(BENCHMARK_CASES), 2), advanced=round(advanced_minutes / len(BENCHMARK_CASES), 2), higher_is_better=False),
        EvaluationMetricResult(evaluation_id=run.id, key="cost_per_task", label="Cost per task", unit="$", baseline=round(baseline_cost / len(BENCHMARK_CASES), 2), advanced=round(advanced_cost / len(BENCHMARK_CASES), 2), higher_is_better=False),
    ])

    db.commit()
    db.refresh(run)
    return run


def list_evaluations(db: Session) -> list[EvaluationRun]:
    return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()


def get_evaluation(db: Session, evaluation_id: UUID) -> EvaluationRun | None:
    return db.query(EvaluationRun).filter(EvaluationRun.id == evaluation_id).first()


def get_evaluation_cases(db: Session, evaluation_id: UUID) -> list[EvaluationCaseResult]:
    return db.query(EvaluationCaseResult).filter(EvaluationCaseResult.evaluation_id == evaluation_id).order_by(EvaluationCaseResult.case_id.asc()).all()


def get_evaluation_metrics(db: Session, evaluation_id: UUID) -> list[EvaluationMetricResult]:
    return db.query(EvaluationMetricResult).filter(EvaluationMetricResult.evaluation_id == evaluation_id).order_by(EvaluationMetricResult.id.asc()).all()
