from fastapi.testclient import TestClient

from odoo_agent import api
from odoo_agent.agent import AgentResult

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_ok(monkeypatch):
    monkeypatch.setattr(api, "ask", lambda q: AgentResult("13 leads", ["search_leads"], [], 2, latency_s=1.5))
    r = client.post("/ask", json={"question": "how many?"})
    assert r.status_code == 200
    assert r.json() == {"answer": "13 leads", "tools": ["search_leads"], "steps": 2, "latency_s": 1.5}


def test_ask_validation():
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_provider_error_is_502(monkeypatch):
    def boom(q):
        raise RuntimeError("quota")
    monkeypatch.setattr(api, "ask", boom)
    r = client.post("/ask", json={"question": "x"})
    assert r.status_code == 502 and "quota" in r.json()["detail"]
