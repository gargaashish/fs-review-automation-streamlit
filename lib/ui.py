from datetime import datetime

import streamlit as st

SEVERITY_ORDER = ["Critical Missing", "Important Gap", "Ambiguous", "Improvement Suggestion"]

SEVERITY_COLOR = {
    "Critical Missing": "red",
    "Important Gap": "orange",
    "Ambiguous": "orange",
    "Improvement Suggestion": "green",
}

SEVERITY_ICON = {
    "Critical Missing": "🔴",
    "Important Gap": "🟠",
    "Ambiguous": "🟡",
    "Improvement Suggestion": "🟢",
}


def format_dt(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return iso


def group_by(findings: list[dict], key: str) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for f in findings:
        k = f[key]
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(f)
    return [(k, groups[k]) for k in order]


def group_by_severity(findings: list[dict]) -> list[tuple[str, list[dict]]]:
    return [(sev, [f for f in findings if f["severity"] == sev]) for sev in SEVERITY_ORDER if any(f["severity"] == sev for f in findings)]


def build_markdown_export(result: dict) -> str:
    lines: list[str] = []
    lines.append(f"# FS Review: {result['document_title']}")
    lines.append("")
    lines.append(f"- Template: {result['template_type']}")
    source_ref = f" ({result['source_reference']})" if result.get("source_reference") else ""
    lines.append(f"- Source: {result['source_type']}{source_ref}")
    lines.append(f"- Reviewed: {format_dt(result['review_timestamp'])}")
    lines.append(f"- Completeness Score: {result['completeness_score']}/100")
    lines.append("")

    fs = result["findings_summary"]
    lines.append(
        f"**Findings Summary** — Critical Missing: {fs['critical_missing']}, Important Gap: {fs['important_gap']}, "
        f"Ambiguous: {fs['ambiguous']}, Improvement Suggestion: {fs['improvement_suggestion']}"
    )
    lines.append("")

    for section, findings in group_by(result["findings"], "section_name"):
        lines.append(f"## {section}")
        for f in findings:
            lines.append(f"- **[{f['severity']}] {f['issue_type']}** — {f['description']}")
            lines.append(f"  - Why it matters: {f['why_it_matters']}")
            lines.append(f"  - Suggested question: {f['suggested_question']}")
        lines.append("")

    if result.get("risks"):
        lines.append("## Risks")
        for r in result["risks"]:
            lines.append(f"- {r}")
        lines.append("")

    if result.get("next_steps"):
        lines.append("## Next Steps")
        for n in result["next_steps"]:
            lines.append(f"- {n}")

    return "\n".join(lines)


def llm_usage_line(result: dict) -> str:
    usage = result["llm_usage"]
    if usage["used"]:
        total_tokens = usage["input_tokens"] + usage["output_tokens"]
        return f"LLM review: {usage['model']} · {total_tokens:,} tokens · ${usage['estimated_cost_usd']:.4f}"
    reason = f" — {usage['skip_reason']}" if usage.get("skip_reason") else ""
    return f"LLM review: not used (rule-based only){reason}"


def render_finding(f: dict) -> None:
    icon = SEVERITY_ICON.get(f["severity"], "⚪")
    with st.container(border=True):
        top_l, top_r = st.columns([4, 1])
        top_l.markdown(f"**{f['section_name']}**")
        top_r.markdown(f":{SEVERITY_COLOR.get(f['severity'], 'gray')}[{icon} {f['severity']}]")
        st.caption(f["issue_type"])
        st.write(f["description"])
        st.markdown(f"**Why it matters:** {f['why_it_matters']}")
        st.markdown(f"**Suggested question:** {f['suggested_question']}")


def render_results(result: dict, key_prefix: str = "") -> None:
    st.subheader(result["document_title"])
    st.caption(f"{result['template_type']} · Reviewed {format_dt(result['review_timestamp'])}")
    st.caption(llm_usage_line(result))

    score_col, chips_col = st.columns([1, 3])
    with score_col:
        st.metric("Completeness Score", f"{result['completeness_score']}/100")
    with chips_col:
        fs = result["findings_summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 Critical", fs["critical_missing"])
        c2.metric("🟠 Important", fs["important_gap"])
        c3.metric("🟡 Ambiguous", fs["ambiguous"])
        c4.metric("🟢 Improvement", fs["improvement_suggestion"])

    md = build_markdown_export(result)
    dl_col, code_col = st.columns([1, 3])
    with dl_col:
        st.download_button(
            "Export as Markdown",
            data=md,
            file_name=f"{result['document_title'][:60].replace(' ', '_')}_review.md",
            mime="text/markdown",
            key=f"{key_prefix}download",
        )
    with st.expander("Copy summary (Markdown)"):
        st.code(md, language="markdown")

    st.divider()
    st.markdown(f"### Findings ({len(result['findings'])})")

    if not result["findings"]:
        st.success("No issues detected. Document appears complete against the selected template.")
    else:
        group_mode = st.radio(
            "Group by", ["Severity", "Section"], horizontal=True, key=f"{key_prefix}group_mode"
        )
        groups = group_by_severity(result["findings"]) if group_mode == "Severity" else group_by(
            result["findings"], "section_name"
        )
        for group_name, findings in groups:
            st.markdown(f"**{group_name}** ({len(findings)})")
            for f in findings:
                render_finding(f)

    if result.get("risks"):
        st.markdown("### Implementation Risks")
        for r in result["risks"]:
            st.markdown(f"- {r}")

    if result.get("next_steps"):
        st.markdown("### Next Steps")
        for n in result["next_steps"]:
            st.markdown(f"- {n}")
