"""Run the eval set: python -m evals.run [--ids d01 p02] [--out evals/REPORT.md]

Data questions get their expected value computed live from Odoo (the `truth` spec), so the
set stays correct whatever the demo data contains. Process questions use a fixed expected answer.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage

from odoo_agent.agent import ask
from odoo_agent.config import get_llm, resolve_provider, setup_logging
from odoo_agent.odoo_client import OdooClient

from .scoring import contains_match, number_match, parse_judge, percentile, tool_selection_ok

QUESTIONS = Path(__file__).parent / "questions.jsonl"
DEFAULT_REPORT = Path(__file__).parent / "REPORT.md"

JUDGE_PROMPT = """You are grading an AI assistant's answer.
Question: {question}
Reference answer: {expected}
Assistant answer: {answer}

The assistant is correct if it conveys every key fact in the reference answer without contradicting it
(extra detail is fine; wording may differ). Reply with ONLY JSON: {{"correct": true|false, "reason": "<one sentence>"}}"""


def resolve_truth(client: OdooClient, spec: dict):
    """Compute the ground-truth value for a question straight from Odoo."""
    kind, model = spec["kind"], spec["model"]
    if kind == "count":
        return len(client.search_read(model, spec["domain"], ["id"]))
    if kind == "sum":
        return round(sum(r[spec["field"]] for r in client.search_read(model, spec["domain"], [spec["field"]])), 2)
    if kind == "field":
        return client.search_read(model, spec["domain"], [spec["field"]], limit=1)[0][spec["field"]]
    if kind == "top_group_count":
        rows = client.read_group(model, [], ["id:count"], [spec["groupby"]])
        named = [r for r in rows if r[spec["groupby"]]]
        return max(named, key=lambda r: r["__count"])[spec["groupby"]][1]
    raise ValueError(f"unknown truth kind {kind!r}")


def judge(llm, question: str, expected: str, answer: str) -> tuple[bool, str]:
    reply = llm.invoke([HumanMessage(JUDGE_PROMPT.format(question=question, expected=expected, answer=answer))])
    text = reply.content if isinstance(reply.content, str) else "".join(
        b.get("text", "") for b in reply.content if isinstance(b, dict))
    return parse_judge(text)


def grade(q: dict, value, answer: str, judge_llm) -> tuple[bool, str]:
    kind = q["answer_type"]
    if kind == "number":
        return number_match(answer, value, q.get("tolerance", 0.0)), f"expected {value}"
    if kind == "contains":
        return contains_match(answer, value), f"expected {value!r}"
    expected = q["expected_answer"].format(value=value)
    return judge(judge_llm, q["question"], expected, answer)


def load_questions(ids: list[str] | None) -> list[dict]:
    rows = [json.loads(l) for l in QUESTIONS.read_text().splitlines() if l.strip()]
    return [r for r in rows if not ids or r["id"] in ids]


def render_report(results: list[dict], provider: str) -> str:
    n = len(results)
    pct = lambda k: f"{100 * sum(r[k] for r in results) / n:.0f}%"
    lat = [r["latency_s"] for r in results]
    lines = [
        "# Evaluation report", "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} · provider `{provider}` · {n} questions", "",
        "| Metric | Result |", "|---|---|",
        f"| Tool-selection accuracy | {pct('tool_ok')} |",
        f"| Answer correctness | {pct('answer_ok')} |",
        f"| Latency p50 / p95 | {statistics.median(lat):.1f}s / {percentile(lat, 0.95):.1f}s |",
        f"| Avg tokens per question (in + out) | {sum(r['in'] for r in results) // n} + {sum(r['out'] for r in results) // n} |",
        "", "## By category", "", "| Category | n | Tool selection | Answer correct |", "|---|---|---|---|",
    ]
    by_cat = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)
    for cat, rs in by_cat.items():
        lines.append(f"| {cat} | {len(rs)} | {sum(r['tool_ok'] for r in rs)}/{len(rs)} | {sum(r['answer_ok'] for r in rs)}/{len(rs)} |")
    lines += ["", "## Per question", "", "| ID | Tools called | Tools OK | Answer OK | Latency | Note |", "|---|---|---|---|---|---|"]
    for r in results:
        note = r["note"].replace("|", "/").replace("\n", " ")[:100]
        lines.append(f"| {r['id']} | {', '.join(r['tools']) or '-'} | {'✅' if r['tool_ok'] else '❌'} | "
                     f"{'✅' if r['answer_ok'] else '❌'} | {r['latency_s']}s | {note} |")
    lines += ["", "_Tokens are agent usage only (judge calls excluded). Numbers: exact match "
              "(0.5 tolerance for currency sums). Text: LLM-as-judge._", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*", help="only run these question ids")
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        setup_logging()

    client, judge_llm = OdooClient.from_env(), get_llm("JUDGE_MODEL")
    results = []
    for q in load_questions(args.ids):
        value = resolve_truth(client, q["truth"]) if "truth" in q else None
        res = ask(q["question"])
        ok, note = grade(q, value, res.answer, judge_llm)
        results.append({
            "id": q["id"], "category": q["category"], "tools": res.tools_called,
            "tool_ok": tool_selection_ok(res.tools_called, q["expected_tools"]), "answer_ok": ok,
            "latency_s": res.latency_s, "in": res.input_tokens, "out": res.output_tokens, "note": note,
            "answer": res.answer,
        })
        print(f"{q['id']}: tools={'OK' if results[-1]['tool_ok'] else 'WRONG'} answer={'OK' if ok else 'WRONG'} ({res.latency_s}s)")

    args.out.write_text(render_report(results, resolve_provider()))
    raw = args.out.with_suffix(".json")
    raw.write_text(json.dumps(results, indent=2))
    print(f"\nReport written to {args.out}")


if __name__ == "__main__":
    main()
