import json
import re

from lib.llm.provider import LlmReviewOutcome, LlmSectionInput
from lib.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from lib.types import Finding
from lib.util import random_id

_VALID_SEVERITIES = {"Ambiguous", "Improvement Suggestion"}
_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```")


def _extract_json(text: str) -> dict:
    fenced = _FENCE_RE.search(text)
    json_text = fenced.group(1) if fenced else text
    parsed = json.loads(json_text)
    return {
        "findings": parsed.get("findings") if isinstance(parsed.get("findings"), list) else [],
        "risks": parsed.get("risks") if isinstance(parsed.get("risks"), list) else [],
    }


class AnthropicLlmProvider:
    def __init__(self, api_key: str, model: str):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def review_sections(
        self, sections: list[LlmSectionInput], document_title: str, template_name: str
    ) -> LlmReviewOutcome:
        if not sections:
            return LlmReviewOutcome(
                provider="anthropic",
                model=self.model,
                skipped=True,
                skip_reason="No sections were eligible for LLM review.",
            )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": build_user_prompt(
                            [(s.section_name, s.content) for s in sections], document_title, template_name
                        ),
                    }
                ],
            )

            text_block = next((b for b in response.content if b.type == "text"), None)
            if text_block is None:
                raise ValueError("LLM response contained no text content.")

            parsed = _extract_json(text_block.text)
            findings: list[Finding] = []
            for f in parsed["findings"]:
                if f.get("severity") not in _VALID_SEVERITIES:
                    continue
                findings.append(
                    Finding(
                        id=random_id(),
                        section_name=f.get("sectionName", ""),
                        severity=f["severity"],
                        issue_type=f.get("issueType", ""),
                        description=f.get("description", ""),
                        why_it_matters=f.get("whyItMatters", ""),
                        suggested_question=f.get("suggestedQuestion", ""),
                        origin="llm",
                    )
                )

            usage = response.usage
            return LlmReviewOutcome(
                findings=findings,
                risks=parsed["risks"],
                provider="anthropic",
                model=self.model,
                input_tokens=getattr(usage, "input_tokens", 0) or 0,
                output_tokens=getattr(usage, "output_tokens", 0) or 0,
                skipped=False,
            )
        except Exception as err:
            return LlmReviewOutcome(
                provider="anthropic",
                model=self.model,
                skipped=True,
                skip_reason=f"LLM review failed: {err}. Falling back to rule-based findings only.",
            )
