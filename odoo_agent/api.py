"""HTTP wrapper so other systems (the Odoo chat addon) can call the agent: uvicorn odoo_agent.api:app"""
from __future__ import annotations

import logging

import json

import markdown
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .graph import AgentResult, ask, ask_events
from .config import setup_logging

setup_logging()
log = logging.getLogger("odoo_agent.api")
app = FastAPI(title="Odoo Agent API")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    answer_html: str  # markdown rendered to HTML for clients that can't render markdown (Odoo chat)
    tools: list[str]
    sources: list[str]  # RAG documents used
    model: str
    steps: int
    latency_s: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _response(r: AgentResult) -> AskResponse:
    html = markdown.markdown(r.answer, extensions=["extra", "sane_lists"])
    return AskResponse(answer=r.answer, answer_html=html, tools=r.tools_called, sources=r.sources,
                       model=r.model, steps=r.steps, latency_s=r.latency_s)


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest) -> AskResponse:
    try:
        r = ask(req.question)
    except Exception as exc:  # provider outage, Odoo down, bad key...
        log.exception("ask failed")
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}"[:300]) from exc
    return _response(r)


@app.post("/ask/stream")
def ask_stream(req: AskRequest) -> StreamingResponse:
    """Newline-delimited JSON: {"type":"status",...} lines, then one {"type":"result",...} or {"type":"error",...}."""

    def lines():
        try:
            for event in ask_events(req.question):
                if event["type"] == "result":
                    event = {"type": "result", **_response(event["result"]).model_dump()}
                yield json.dumps(event) + "\n"
        except Exception as exc:
            log.exception("ask failed")
            yield json.dumps({"type": "error", "detail": f"{type(exc).__name__}: {exc}"[:300]}) + "\n"

    return StreamingResponse(lines(), media_type="application/x-ndjson")
