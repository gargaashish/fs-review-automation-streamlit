import time
from datetime import datetime, timezone

from lib import config
from lib.types import LlmUsage, NormalizedDocument, ReviewResult
from lib.templates.definitions import get_template_by_id
from lib.review.rule_engine import run_rule_engine
from lib.review.score import compute_completeness_score, summarize_findings
from lib.llm import get_llm_provider, pick_sections_for_llm_review
from lib.llm.pricing import estimate_cost_usd
from lib.util import random_id


def run_review(
    doc: NormalizedDocument, template_id: str, source_type: str, source_reference: str | None = None
) -> ReviewResult:
    started_at = time.monotonic()
    template = get_template_by_id(template_id)

    rule_output = run_rule_engine(doc, template)

    llm_provider = get_llm_provider()
    sections_for_llm = pick_sections_for_llm_review(
        doc.sections, rule_output.weak_section_headings, config.LLM_SELECTIVE_SECTIONS_ONLY
    )
    llm_outcome = llm_provider.review_sections(sections_for_llm, doc.title, template.name)

    all_findings = [*rule_output.findings, *llm_outcome.findings]
    completeness_score = compute_completeness_score(all_findings)
    findings_summary = summarize_findings(all_findings)

    next_steps: list[str] = []
    if findings_summary.critical_missing > 0:
        next_steps.append("Resolve all Critical Missing items before this specification proceeds to development.")
    if findings_summary.important_gap > 0:
        next_steps.append("Follow up with the author on Important Gap items to reduce rework risk.")
    if llm_outcome.skipped and llm_outcome.skip_reason:
        next_steps.append(f"Note: {llm_outcome.skip_reason}")
    if not all_findings:
        next_steps.append("No issues detected. Document appears complete against the selected template.")

    estimated_cost_usd = (
        estimate_cost_usd(llm_outcome.model, llm_outcome.input_tokens, llm_outcome.output_tokens)
        if llm_outcome.model
        else 0.0
    )

    return ReviewResult(
        id=random_id(),
        document_title=doc.title,
        source_type=source_type,
        source_reference=source_reference,
        template_type=template.name,
        review_timestamp=datetime.now(timezone.utc).isoformat(),
        completeness_score=completeness_score,
        findings_summary=findings_summary,
        findings=all_findings,
        risks=llm_outcome.risks,
        next_steps=next_steps,
        status="completed",
        duration_ms=round((time.monotonic() - started_at) * 1000),
        llm_usage=LlmUsage(
            used=not llm_outcome.skipped,
            provider=llm_outcome.provider,
            model=llm_outcome.model,
            input_tokens=llm_outcome.input_tokens,
            output_tokens=llm_outcome.output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            skip_reason=llm_outcome.skip_reason if llm_outcome.skipped else None,
        ),
    )
