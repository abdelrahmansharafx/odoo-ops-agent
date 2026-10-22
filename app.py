"""Minimal chat UI: streamlit run app.py"""
import streamlit as st

from odoo_agent.graph import ask
from odoo_agent.config import setup_logging

setup_logging()
st.set_page_config(page_title="Odoo Agent", page_icon="💬")
st.title("Odoo business assistant")
st.caption("Ask about leads, pipeline, orders, customers, or internal processes.")

if "history" not in st.session_state:
    st.session_state.history = []

for role, text, meta in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)
        if meta:
            st.caption(meta)

if question := st.chat_input("e.g. How many leads are in the Qualified stage?"):
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                r = ask(question)
                text = r.answer
                meta = f"Tools: {', '.join(r.tools_called) or 'none'} · {r.steps} steps · {r.latency_s}s"
            except Exception as exc:
                text, meta = f"Error: {exc}", ""
        st.markdown(text)
        if meta:
            st.caption(meta)
    st.session_state.history += [("user", question, ""), ("assistant", text, meta)]
