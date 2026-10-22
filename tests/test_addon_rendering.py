import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rendering", Path(__file__).parent.parent / "odoo_addons/agent_chat/models/rendering.py")
rendering = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rendering)


def test_status_marks_finished_and_active_steps():
    html = str(rendering.status_html([
        {"stage": "gemini", "label": "Asking Gemini (m)"},
        {"stage": "rag", "label": "Searching process docs (RAG)"},
    ]))
    assert html.index("✅") < html.index("⏳")
    assert "Searching process docs (RAG)…" in html and "Asking Gemini (m)…" not in html


def test_answer_has_chips_for_model_rag_odoo_and_time():
    data = {"answer_html": "<p>13</p>", "model": "Gemini · m", "sources": ["refund-policy.md"],
            "tools": ["search_leads", "search_process_docs", "search_leads"], "latency_s": 14.33}
    html = str(rendering.answer_html(data))
    assert html.startswith("<p>13</p>")
    assert "Gemini · m" in html and "RAG · refund-policy.md" in html and "14.3s" in html
    assert html.count("Odoo · search_leads") == 1 and "Odoo · search_process_docs" not in html


def test_answer_without_rag_has_no_rag_chip():
    html = str(rendering.answer_html({"answer_html": "x", "model": "", "sources": [], "tools": [], "latency_s": 1}))
    assert "RAG" not in html


def test_values_are_escaped():
    assert "<script>" not in str(rendering.error_html("<script>x</script>"))
    assert "<script>" not in str(rendering.status_html([{"stage": "odoo", "label": "<script>x</script>"}]))
