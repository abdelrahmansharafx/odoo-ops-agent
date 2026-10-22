import json
from unittest.mock import MagicMock

from evals import run


def test_questions_file_is_well_formed():
    qs = run.load_questions(None)
    assert 18 <= len(qs) <= 25
    assert len({q["id"] for q in qs}) == len(qs)
    assert {q["category"] for q in qs} == {"data", "process", "multi"}
    for q in qs:
        assert q["expected_tools"] and q["answer_type"] in {"number", "contains", "judge"}
        if q["answer_type"] == "judge":
            assert "expected_answer" in q
        else:
            assert "truth" in q


def test_resolve_truth_kinds():
    c = MagicMock()
    c.search_read.return_value = [{"id": 1, "amount_total": 10.5}, {"id": 2, "amount_total": 4.25}]
    assert run.resolve_truth(c, {"kind": "count", "model": "m", "domain": []}) == 2
    assert run.resolve_truth(c, {"kind": "sum", "model": "m", "domain": [], "field": "amount_total"}) == 14.75
    c.read_group.return_value = [{"user_id": False, "__count": 9}, {"user_id": [3, "Ann"], "__count": 4}, {"user_id": [4, "Bo"], "__count": 2}]
    assert run.resolve_truth(c, {"kind": "top_group_count", "model": "m", "groupby": "user_id"}) == "Ann"


def test_grade_number_and_judge():
    q = {"answer_type": "number", "tolerance": 0.5}
    assert run.grade(q, 100.0, "Total: 100", None)[0]
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content='{"correct": true, "reason": "fine"}')
    q = {"answer_type": "judge", "question": "q", "expected_answer": "{value} leads"}
    ok, _ = run.grade(q, 7, "seven leads", llm)
    assert ok and "7 leads" in llm.invoke.call_args.args[0][0].content


def test_report_renders():
    rs = [{"id": "d01", "category": "data", "tools": ["search_leads"], "tool_ok": True, "answer_ok": False,
           "latency_s": 1.5, "in": 100, "out": 20, "note": "expected 3", "answer": "x"}]
    md = run.render_report(rs, "anthropic")
    assert "| Tool-selection accuracy | 100% |" in md and "| Answer correctness | 0% |" in md
