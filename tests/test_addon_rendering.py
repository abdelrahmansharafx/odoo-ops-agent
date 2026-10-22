import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "rendering", Path(__file__).parent.parent / "odoo_addons/agent_chat/models/rendering.py")
rendering = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rendering)


def test_thinking_uses_animated_class_and_minimal_text():
    html = str(rendering.thinking_html())
    assert 'class="o_agent_thinking"' in html and ">Thinking<" in html
    assert "o_agent_spark" in html and "o_agent_skeleton" in html
    assert html.count(">Thinking<") == 1 and "…" not in html  # one word, nothing else


def test_answer_has_chips_for_model_rag_odoo_and_time():
    data = {"answer_html": "<p>13</p>", "model": "Gemini · m", "sources": ["refund-policy.md"],
            "tools": ["search_leads", "search_process_docs", "search_leads"], "latency_s": 14.33}
    html = str(rendering.answer_html(data))
    assert html.startswith("<p>13</p>")
    assert "Gemini · m" in html and "RAG · refund-policy.md" in html and "14.3s" in html
    assert not any(icon in html for icon in "✨📚🗄⏱")  # coloured tags, no icons
    assert "background-color:rgba(66,133,244" in html
    assert "color:#1a56db" in html and "color:#137333" in html and "color:#714b67" in html
    assert html.count("Odoo · search_leads") == 1 and "Odoo · search_process_docs" not in html


def test_answer_without_rag_has_no_rag_chip():
    html = str(rendering.answer_html({"answer_html": "x", "model": "", "sources": [], "tools": [], "latency_s": 1}))
    assert "RAG" not in html


def test_values_are_escaped():
    assert "<script>" not in str(rendering.error_html("<script>x</script>"))
