import streamlit as st

from lib.parsers import parse_file, UnsupportedFileTypeError
from lib.templates.definitions import TEMPLATES
from lib.review.run_review import run_review
from lib.db import save_review_run
from lib.ui import render_results

st.set_page_config(page_title="FS Review Utility", page_icon="📋", layout="centered")

st.title("FS Review Utility")
st.caption("Upload a document and select a template to run a structured completeness review.")

if "result" not in st.session_state:
    st.session_state.result = None

if st.session_state.result is not None:
    if st.button("← New Review"):
        st.session_state.result = None
        st.rerun()
    render_results(st.session_state.result, key_prefix="main_")
else:
    template_options = {t.name: t.id for t in TEMPLATES}
    template_name = st.selectbox("Template", list(template_options.keys()), index=len(template_options) - 1)
    template_id = template_options[template_name]

    uploaded = st.file_uploader("Document (.docx, .pdf, .txt, .md)", type=["docx", "pdf", "txt", "md"])

    if st.button("Review Document", type="primary", disabled=uploaded is None):
        if uploaded is None:
            st.error("Please select a file to review.")
        else:
            try:
                with st.spinner("Reviewing…"):
                    data = uploaded.getvalue()
                    normalized = parse_file(data, uploaded.name)
                    result = run_review(normalized, template_id, "upload", uploaded.name)
                    save_review_run(result)
                st.session_state.result = result.to_dict()
                st.rerun()
            except UnsupportedFileTypeError as err:
                st.error(str(err))
            except Exception as err:
                st.error(f"Review failed: {err}")
