_PRICING_USD = {
    "claude-sonnet-5": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
}

_DEFAULT_RATE = _PRICING_USD["claude-sonnet-5"]


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = _PRICING_USD.get(model, _DEFAULT_RATE)
    cost = (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate
    return round(cost, 6)
