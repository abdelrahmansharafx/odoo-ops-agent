import json

from fastapi.testclient import TestClient

from odoo_agent import api
from odoo_agent.graph import AgentResult

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_ok(monkeypatch):
    monkeypatch.setattr(api, "ask", lambda q: AgentResult("13 leads", ["search_leads"], [], 2, latency_s=1.5, model="Gemini · m", sources=["a.md"]))
    r = client.post("/ask", json={"question": "how many?"})
    assert r.status_code == 200
    assert r.json() == {"answer": "13 leads", "answer_html": "<p>13 leads</p>", "tools": ["search_leads"],
                        "sources": ["a.md"], "model": "Gemini · m", "steps": 2, "latency_s": 1.5}


def test_markdown_is_rendered_to_html(monkeypatch):
    md = "Salespeople:\n\n* **Marc**: 8 leads\n* **Mitchell**: 18 leads"
    monkeypatch.setattr(api, "ask", lambda q: AgentResult(md, [], [], 1))
    html = client.post("/ask", json={"question": "x"}).json()["answer_html"]
    assert "<strong>Marc</strong>" in html and html.count("<li>") == 2 and "**" not in html


def test_ask_validation():
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_provider_error_is_502(monkeypatch):
    def boom(q):
        raise RuntimeError("quota")
    monkeypatch.setattr(api, "ask", boom)
    r = client.post("/ask", json={"question": "x"})
    assert r.status_code == 502 and "quota" in r.json()["detail"]


def test_stream_emits_status_then_result(monkeypatch):
    def fake_events(q):
        yield {"type": "status", "stage": "rag", "label": "Searching process docs (RAG)"}
        yield {"type": "result", "result": AgentResult("**hi**", [], [], 1, model="Gemini · m")}

    monkeypatch.setattr(api, "ask_events", fake_events)
    lines = [json.loads(l) for l in client.post("/ask/stream", json={"question": "x"}).text.splitlines()]
    assert lines[0]["stage"] == "rag"
    assert lines[1]["type"] == "result" and "<strong>hi</strong>" in lines[1]["answer_html"]


def test_stream_error_event(monkeypatch):
    def boom(q):
        raise RuntimeError("quota")
        yield

    monkeypatch.setattr(api, "ask_events", boom)
    lines = [json.loads(l) for l in client.post("/ask/stream", json={"question": "x"}).text.splitlines()]
    assert lines == [{"type": "error", "detail": "RuntimeError: quota"}]
