"""LangGraph agent: agent (LLM + tool routing) -> tools -> agent ... -> final answer."""
from __future__ import annotations

import json
import logging
import operator
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from .rag import search_process_docs
from .tools import DATA_TOOLS

log = logging.getLogger("odoo_agent.agent")

ALL_TOOLS = [*DATA_TOOLS, search_process_docs]
MAX_STEPS = 6

SYSTEM_PROMPT = """You are a business analyst assistant for an Odoo instance (CRM and Sales).
Today is {today}.
- For live data (leads, pipeline, orders, customers) call the Odoo tools. Never guess numbers.
- For policy/process questions call search_process_docs and answer only from what it returns.
- Combine several tools when a question needs both data and policy.
- Pipeline stages are: New, Qualified, Proposition, Won.
- Answer concisely. State exact numbers. If a tool returns nothing, say so plainly."""


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    steps: int
    tool_calls: Annotated[list[dict], operator.add]
    usage: Annotated[list[dict], operator.add]
    limit_hit: bool


@dataclass
class AgentResult:
    answer: str
    tools_called: list[str]
    tool_calls: list[dict]
    steps: int
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    hit_step_limit: bool = False
    messages: list[BaseMessage] = field(default_factory=list, repr=False)


def _usage(msg: AIMessage) -> list[dict]:
    u = getattr(msg, "usage_metadata", None) or {}
    return [{"in": u.get("input_tokens", 0), "out": u.get("output_tokens", 0)}]


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def build_graph(llm, tools=None, max_steps: int = MAX_STEPS):
    tools = tools or ALL_TOOLS
    by_name = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState) -> dict:
        start = time.perf_counter()
        msgs = [SystemMessage(SYSTEM_PROMPT.format(today=date.today().isoformat())), *state["messages"]]
        reply = llm_with_tools.invoke(msgs)
        log.info("step=%d node=agent tool_requests=%s duration=%.2fs",
                 state["steps"] + 1, [c["name"] for c in reply.tool_calls], time.perf_counter() - start)
        return {"messages": [reply], "steps": state["steps"] + 1, "usage": _usage(reply)}

    def tool_node(state: AgentState) -> dict:
        out_msgs, calls = [], []
        for call in state["messages"][-1].tool_calls:
            start = time.perf_counter()
            try:
                result = json.dumps(by_name[call["name"]].invoke(call["args"]), default=str)
                status = "ok"
            except Exception as exc:  # surfaced to the model so it can recover
                result, status = f"Error: {exc}", "error"
            log.info("node=tool name=%s args=%s status=%s duration=%.2fs",
                     call["name"], call["args"], status, time.perf_counter() - start)
            out_msgs.append(ToolMessage(content=result, tool_call_id=call["id"], name=call["name"]))
            calls.append({"name": call["name"], "args": call["args"]})
        return {"messages": out_msgs, "tool_calls": calls}

    def route(state: AgentState) -> str:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None) and state["steps"] < max_steps:
            return "tools"
        return "final"

    def final_node(state: AgentState) -> dict:
        last = state["messages"][-1]
        if not getattr(last, "tool_calls", None):
            return {"messages": []}  # model already answered; nothing more to do
        # Step guard tripped with tool calls still pending: force an answer from what we have.
        log.warning("node=final max_steps=%d reached, forcing answer", max_steps)
        gathered = [m for m in state["messages"] if not isinstance(m, AIMessage) or not m.tool_calls]
        nudge = HumanMessage("Step limit reached. Answer now using only the information gathered so far, "
                             "and say what is missing if it is incomplete.")
        reply = llm.invoke([SystemMessage(SYSTEM_PROMPT.format(today=date.today().isoformat())), *gathered, nudge])
        return {"messages": [reply], "usage": _usage(reply), "limit_hit": True}

    g = StateGraph(AgentState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tool_node)
    g.add_node("final", final_node)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, {"tools": "tools", "final": "final"})
    g.add_edge("tools", "agent")
    g.add_edge("final", END)
    return g.compile()


def ask(question: str, llm=None, max_steps: int = MAX_STEPS) -> AgentResult:
    if llm is None:
        from .config import get_llm

        llm = get_llm()
    graph = build_graph(llm, max_steps=max_steps)
    start = time.perf_counter()
    state = graph.invoke(
        {"messages": [HumanMessage(question)], "steps": 0, "tool_calls": [], "usage": [], "limit_hit": False},
        {"recursion_limit": 2 * max_steps + 5},
    )
    final = next(m for m in reversed(state["messages"]) if isinstance(m, AIMessage) and not m.tool_calls)
    latency = time.perf_counter() - start
    calls = state["tool_calls"]
    result = AgentResult(
        answer=_text(final.content).strip(),
        tools_called=[c["name"] for c in calls],
        tool_calls=calls,
        steps=state["steps"],
        input_tokens=sum(u["in"] for u in state["usage"]),
        output_tokens=sum(u["out"] for u in state["usage"]),
        latency_s=round(latency, 2),
        hit_step_limit=state["limit_hit"],
        messages=state["messages"],
    )
    log.info("done steps=%d tools=%s tokens_in=%d tokens_out=%d latency=%.2fs",
             result.steps, result.tools_called, result.input_tokens, result.output_tokens, result.latency_s)
    return result
