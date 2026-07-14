from lib import config
from lib.llm.provider import LlmProvider, LlmReviewOutcome, LlmSectionInput, pick_sections_for_llm_review
from lib.llm.noop_provider import NoopLlmProvider


def get_llm_provider() -> LlmProvider:
    if not config.LLM_REVIEW_ENABLED:
        return NoopLlmProvider()

    if config.LLM_PROVIDER == "anthropic":
        if not config.ANTHROPIC_API_KEY:
            return NoopLlmProvider()
        from lib.llm.anthropic_provider import AnthropicLlmProvider

        return AnthropicLlmProvider(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)

    return NoopLlmProvider()
