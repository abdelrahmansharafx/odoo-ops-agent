from evals.scoring import contains_match, number_match, parse_judge, percentile, tool_selection_ok

ALTS = [["search_leads"], ["get_pipeline_summary"]]


def test_tool_selection():
    assert tool_selection_ok(["search_leads"], ALTS)
    assert tool_selection_ok(["get_pipeline_summary", "get_pipeline_summary"], ALTS)
    assert not tool_selection_ok([], ALTS)                                   # no call
    assert not tool_selection_ok(["search_process_docs"], ALTS)              # wrong tool
    assert not tool_selection_ok(["search_leads", "search_process_docs"], ALTS)  # stray extra tool


def test_tool_selection_multi_step_needs_both():
    alts = [["search_leads", "search_process_docs"]]
    assert tool_selection_ok(["search_process_docs", "search_leads"], alts)
    assert not tool_selection_ok(["search_leads"], alts)


def test_number_match():
    assert number_match("There are 12 leads.", 12)
    assert not number_match("There are 120 leads.", 12)
    assert number_match("Total is $1,234,567.50", 1234567.5)
    assert number_match("about 1,235", 1234.8, tolerance=0.5)
    assert not number_match("none", 3)


def test_contains_match():
    assert contains_match("Email: Deco@Example.com ok", "deco@example.com")


def test_parse_judge():
    assert parse_judge('Sure: {"correct": true, "reason": "ok"}') == (True, "ok")
    assert parse_judge("garbage")[0] is False


def test_percentile():
    assert percentile([1, 2, 3, 4, 5], 0.5) == 3 and percentile([], 0.9) == 0.0
