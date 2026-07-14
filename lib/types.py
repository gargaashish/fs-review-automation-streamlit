from dataclasses import dataclass, field, asdict
from typing import Optional, Literal

Severity = Literal["Critical Missing", "Important Gap", "Ambiguous", "Improvement Suggestion"]
FindingOrigin = Literal["rule", "llm"]
SourceType = Literal["upload", "link"]


@dataclass
class Section:
    heading: str
    content: str
    level: int
    word_count: int = 0


@dataclass
class NormalizedDocument:
    title: str
    source_file_name: Optional[str]
    file_type: Optional[str]
    sections: list[Section]


@dataclass
class Finding:
    id: str
    section_name: str
    severity: Severity
    issue_type: str
    description: str
    why_it_matters: str
    suggested_question: str
    origin: FindingOrigin


@dataclass
class FindingsSummary:
    critical_missing: int = 0
    important_gap: int = 0
    ambiguous: int = 0
    improvement_suggestion: int = 0


@dataclass
class LlmUsage:
    used: bool
    provider: str
    model: Optional[str]
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    skip_reason: Optional[str] = None


@dataclass
class ReviewResult:
    id: str
    document_title: str
    source_type: SourceType
    source_reference: Optional[str]
    template_type: str
    review_timestamp: str
    completeness_score: int
    findings_summary: FindingsSummary
    findings: list[Finding]
    risks: list[str]
    next_steps: list[str]
    status: str
    llm_usage: LlmUsage
    duration_ms: int

    def to_dict(self) -> dict:
        return asdict(self)
