from dataclasses import dataclass, field
from typing import Protocol

from lib.types import Finding, Section


@dataclass
class LlmSectionInput:
    section_name: str
    content: str


@dataclass
class LlmReviewOutcome:
    findings: list[Finding] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    provider: str = "none"
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    skipped: bool = True
    skip_reason: str | None = None


class LlmProvider(Protocol):
    def review_sections(
        self, sections: list[LlmSectionInput], document_title: str, template_name: str
    ) -> LlmReviewOutcome: ...


def pick_sections_for_llm_review(
    all_sections: list[Section], weak_section_headings: list[str], selective_only: bool
) -> list[LlmSectionInput]:
    non_empty = [s for s in all_sections if s.content.strip()]

    source = non_empty
    if selective_only:
        weak = [s for s in non_empty if s.heading in weak_section_headings]
        rest = sorted(
            (s for s in non_empty if s.heading not in weak_section_headings),
            key=lambda s: s.word_count,
            reverse=True,
        )[: max(0, 5 - len(weak))]
        source = [*weak, *rest]

    return [LlmSectionInput(section_name=s.heading, content=s.content[:4000]) for s in source]
