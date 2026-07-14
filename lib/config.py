import os

try:
    import streamlit as st

    _secrets = st.secrets if hasattr(st, "secrets") else {}
except Exception:
    _secrets = {}


def _get(key: str, default: str = "") -> str:
    if key in os.environ:
        return os.environ[key]
    try:
        if key in _secrets:
            return str(_secrets[key])
    except Exception:
        pass
    return default


LLM_REVIEW_ENABLED = _get("LLM_REVIEW_ENABLED", "false").lower() == "true"
LLM_PROVIDER = _get("LLM_PROVIDER", "none")
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = _get("ANTHROPIC_MODEL", "claude-sonnet-5")
LLM_SELECTIVE_SECTIONS_ONLY = _get("LLM_SELECTIVE_SECTIONS_ONLY", "true").lower() != "false"
DATABASE_PATH = _get("DATABASE_PATH", "./data/fs-review.db")
