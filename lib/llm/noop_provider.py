from lib.llm.provider import LlmReviewOutcome, LlmSectionInput


class NoopLlmProvider:
    def review_sections(
        self, sections: list[LlmSectionInput], document_title: str, template_name: str
    ) -> LlmReviewOutcome:
        return LlmReviewOutcome(
            provider="none",
            skipped=True,
            skip_reason="LLM review is disabled (LLM_REVIEW_ENABLED=false or no provider configured).",
        )
