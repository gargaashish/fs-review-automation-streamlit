import streamlit as st

from lib.db import list_review_runs, get_review_run
from lib.ui import render_results, format_dt

st.set_page_config(page_title="History · FS Review Utility", page_icon="🗂️", layout="centered")

st.title("Review History")
st.caption("Past review runs, most recent first.")

runs = list_review_runs()

if not runs:
    st.info("No reviews yet. Run one from the Review page.")
else:
    labels = [f"{r['document_title']} · {r['template_type']} · {r['completeness_score']}/100 · {format_dt(r['review_timestamp'])}" for r in runs]
    selected = st.selectbox("Select a past review", labels)
    selected_run = runs[labels.index(selected)]

    st.dataframe(
        [
            {
                "Document": r["document_title"],
                "Template": r["template_type"],
                "Score": f"{r['completeness_score']}/100",
                "Reviewed": format_dt(r["review_timestamp"]),
            }
            for r in runs
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.divider()
    full_result = get_review_run(selected_run["id"])
    if full_result:
        render_results(full_result, key_prefix=f"hist_{selected_run['id']}_")
    else:
        st.error("Could not load this review run.")
