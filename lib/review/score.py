from lib.types import Finding, FindingsSummary

_SEVERITY_WEIGHT = {
    "Critical Missing": 12,
    "Important Gap": 6,
    "Ambiguous": 3,
    "Improvement Suggestion": 1,
}


def summarize_findings(findings: list[Finding]) -> FindingsSummary:
    return FindingsSummary(
        critical_missing=sum(1 for f in findings if f.severity == "Critical Missing"),
        important_gap=sum(1 for f in findings if f.severity == "Important Gap"),
        ambiguous=sum(1 for f in findings if f.severity == "Ambiguous"),
        improvement_suggestion=sum(1 for f in findings if f.severity == "Improvement Suggestion"),
    )


def compute_completeness_score(findings: list[Finding]) -> int:
    penalty = sum(_SEVERITY_WEIGHT[f.severity] for f in findings)
    score = round(100 - penalty)
    return max(0, min(100, score))
