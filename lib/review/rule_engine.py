import re
from dataclasses import dataclass, field

from lib.types import Finding, NormalizedDocument, Section
from lib.templates.types import RequiredSectionDef, TemplateDefinition
from lib.util import random_id as _random_id


def _normalize_heading(h: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", h.lower()).strip()


def _find_matching_section(doc: NormalizedDocument, definition: RequiredSectionDef) -> Section | None:
    alias_set = [_normalize_heading(a) for a in definition.aliases]
    for s in doc.sections:
        h = _normalize_heading(s.heading)
        if any(h == alias or alias in h or h in alias for alias in alias_set):
            return s
    return None


def _word_count(text: str) -> int:
    return len(text.split())


def _strip_placeholders(content: str, patterns: list[re.Pattern]) -> str:
    if not patterns:
        return content
    stripped = content
    for p in patterns:
        stripped = p.sub(" ", stripped)
    return stripped.strip()


@dataclass
class RuleEngineOutput:
    findings: list[Finding] = field(default_factory=list)
    matched_section_keys: set[str] = field(default_factory=set)
    weak_section_headings: list[str] = field(default_factory=list)


def run_rule_engine(doc: NormalizedDocument, template: TemplateDefinition) -> RuleEngineOutput:
    findings: list[Finding] = []
    matched_section_keys: set[str] = set()
    weak_section_headings: list[str] = []
    matched_section_ids: set[int] = set()

    for definition in template.required_sections:
        match = _find_matching_section(doc, definition)

        if match is None:
            findings.append(
                Finding(
                    id=_random_id(),
                    section_name=definition.aliases[0],
                    severity=definition.severity_if_missing,
                    issue_type="Missing Section",
                    description=f'The document does not appear to contain a "{definition.aliases[0]}" section.',
                    why_it_matters=definition.why_it_matters,
                    suggested_question=definition.suggested_question,
                    origin="rule",
                )
            )
            continue

        matched_section_keys.add(definition.key)
        matched_section_ids.add(id(match))

        stripped_content = _strip_placeholders(match.content, definition.placeholder_patterns)
        stripped_word_count = _word_count(stripped_content)

        if stripped_word_count < definition.min_word_count:
            is_placeholder_only = stripped_word_count == 0 and bool(definition.placeholder_patterns)
            severity = (
                "Critical Missing"
                if is_placeholder_only and definition.severity_if_missing == "Critical Missing"
                else "Important Gap"
            )
            issue_type = (
                "Section Not Filled (Placeholder Text Only)"
                if is_placeholder_only
                else "Section Too Short / Likely Incomplete"
            )
            description = (
                f'The "{match.heading}" section still contains only the template\'s instructional/placeholder '
                f"text — no real content has been added."
                if is_placeholder_only
                else (
                    f'The "{match.heading}" section has only {stripped_word_count} word(s) of real content, '
                    f"which is likely too brief to be complete (expected at least {definition.min_word_count})."
                )
            )
            findings.append(
                Finding(
                    id=_random_id(),
                    section_name=match.heading,
                    severity=severity,
                    issue_type=issue_type,
                    description=description,
                    why_it_matters=definition.why_it_matters,
                    suggested_question=f'Can you fill in the "{match.heading}" section with concrete detail?',
                    origin="rule",
                )
            )
            weak_section_headings.append(match.heading)

        for check in definition.content_checks:
            if not check.test(stripped_content, match.content):
                findings.append(
                    Finding(
                        id=_random_id(),
                        section_name=match.heading,
                        severity=check.severity_if_failed,
                        issue_type=check.issue_type,
                        description=check.description,
                        why_it_matters=check.why_it_matters,
                        suggested_question=check.suggested_question,
                        origin="rule",
                    )
                )

    if template.disallow_extra_sections:
        top_level_sections = [s for s in doc.sections if s.level == 1 and s.word_count > 0]
        for s in top_level_sections:
            if id(s) not in matched_section_ids:
                findings.append(
                    Finding(
                        id=_random_id(),
                        section_name=s.heading,
                        severity="Important Gap",
                        issue_type="Unexpected Section - Not Part of Approved Template",
                        description=f'"{s.heading}" is not one of the approved sections for this template.',
                        why_it_matters=(
                            "This template requires a fixed section structure so that reviews and audits stay "
                            "consistent across documents. New or renamed top-level sections break that consistency."
                        ),
                        suggested_question=(
                            f'Should the content under "{s.heading}" be moved into an existing approved section, '
                            f"or does the template need to be formally updated to include it?"
                        ),
                        origin="rule",
                    )
                )

    non_empty_real_sections = [s for s in doc.sections if s.word_count > 0]
    if not non_empty_real_sections:
        findings.append(
            Finding(
                id=_random_id(),
                section_name="Document",
                severity="Critical Missing",
                issue_type="No Structured Content Detected",
                description="The document could not be broken into distinct sections. It may be unstructured free text.",
                why_it_matters="Without clear section structure, this review cannot verify completeness against the template.",
                suggested_question="Can the document be reformatted with clear section headings?",
                origin="rule",
            )
        )

    return RuleEngineOutput(
        findings=findings, matched_section_keys=matched_section_keys, weak_section_headings=weak_section_headings
    )
