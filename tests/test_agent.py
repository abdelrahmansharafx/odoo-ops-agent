from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from odoo_agent.agent import ask


class ScriptedLLM:
    """Stands in for a chat model: replays scripted AIMessages in order."""

    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.calls += 1
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def ai(text="", calls=(), tin=10, tout=5):
    return AIMessage(content=text, tool_calls=[{"name": n, "args": a, "id": f"c{i}"} for i, (n, a) in enumerate(calls)],
                     usage_metadata={"input_tokens": tin, "output_tokens": tout, "total_tokens": tin + tout})


@tool
def echo(x: int) -> dict:
    """Echo a number."""
    return {"x": x}


@tool
def boom() -> dict:
    """Always fails."""
    raise RuntimeError("kaput")




def test_tool_then_answer(monkeypatch):
    monkeypatch.setattr("odoo_agent.agent.ALL_TOOLS", [echo])
    llm = ScriptedLLM([ai(calls=[("echo", {"x": 3})]), ai("The answer is 3")])
    r = ask("q", llm=llm)
    assert r.answer == "The answer is 3"
    assert r.tool_calls == [{"name": "echo", "args": {"x": 3}}]
    assert r.steps == 2 and (r.input_tokens, r.output_tokens) == (20, 10) and not r.hit_step_limit


def test_no_tool_direct_answer(monkeypatch):
    monkeypatch.setattr("odoo_agent.agent.ALL_TOOLS", [echo])
    r = ask("q", llm=ScriptedLLM([ai("hi")]))
    assert r.tools_called == [] and r.answer == "hi"


def test_tool_error_is_returned_to_model(monkeypatch):
    monkeypatch.setattr("odoo_agent.agent.ALL_TOOLS", [boom])
    llm = ScriptedLLM([ai(calls=[("boom", {})]), ai("sorry")])
    r = ask("q", llm=llm)
    tool_msg = next(m for m in r.messages if m.type == "tool")
    assert "kaput" in tool_msg.content and r.answer == "sorry"


def test_max_steps_guard_forces_answer(monkeypatch):
    monkeypatch.setattr("odoo_agent.agent.ALL_TOOLS", [echo])
    # Model asks for a tool forever; the final reply (last item repeats) is only reachable via the guard.
    looping = ai(calls=[("echo", {"x": 1})])
    llm = ScriptedLLM([looping, looping, ai("forced")])
    r = ask("q", llm=llm, max_steps=2)
    assert r.hit_step_limit and r.answer == "forced"
    assert r.steps == 2
