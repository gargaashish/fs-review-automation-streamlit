import streamlit as st

from lib.db import get_usage_stats
from lib.ui import format_dt

st.set_page_config(page_title="Usage · FS Review Utility", page_icon="📊", layout="centered")

st.title("LLM Usage & Cost")

stats = get_usage_stats()

top_l, top_r = st.columns([3, 1])
with top_l:
    st.caption(f"Data refreshed {format_dt(stats['data_refreshed_at'])}")
    if stats["llm_enabled"]:
        st.success("LLM enabled", icon="✨")
    else:
        st.info("LLM disabled · rule-based only", icon="🛡️")
with top_r:
    if st.button("Refresh"):
        st.rerun()

st.divider()

row1 = st.columns(4)
row1[0].metric("Analyses (24h)", stats["analyses_24h"], help=f"avg {stats['avg_duration_seconds_24h']}s per run")
row1[0].caption(f"avg {stats['avg_duration_seconds_24h']}s per run")

llm_used_pct = round((stats["llm_used_runs_24h"] / stats["analyses_24h"]) * 100) if stats["analyses_24h"] > 0 else 0
row1[1].metric("LLM Used (24h)", f"{llm_used_pct}%")
row1[1].caption(f"{stats['llm_used_runs_24h']} of {stats['analyses_24h']} analyses")

row1[2].metric("Rule-Only Runs (Total)", stats["rule_only_runs"])
row1[2].caption("deterministic engine — no LLM call")

row1[3].metric("LLM Tokens (Total)", f"{stats['llm_tokens_total']:,}")
row1[3].caption(f"{stats['llm_input_tokens_total']:,} in · {stats['llm_output_tokens_total']:,} out")

row2 = st.columns(4)
row2[0].metric("Est. Cost (Total)", f"${stats['estimated_cost_usd_total']:.4f}")
row2[0].caption(f"${stats['estimated_cost_usd_24h']:.4f} in the last 24h")

row2[1].metric("Total Analyses (All Time)", stats["total_analyses"])
row2[1].caption(f"{stats['llm_used_runs']} used the LLM stage")
