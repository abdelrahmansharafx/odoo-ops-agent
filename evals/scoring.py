"""Pure scoring helpers (no network), unit-tested in tests/test_scoring.py."""
from __future__ import annotations

import json
import re


def tool_selection_ok(called: list[str], alternatives: list[list[str]]) -> bool:
    """Correct if the calls cover at least one acceptable tool-set and use nothing outside any of them."""
    used = set(called)
    allowed = {t for alt in alternatives for t in alt}
    return used <= allowed and any(set(alt) <= used for alt in alternatives)


def extract_numbers(text: str) -> list[float]:
    cleaned = re.sub(r"(?<=\d)[, ](?=\d{3}\b)", "", text)  # 1,234.5 -> 1234.5
    return [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", cleaned)]


def number_match(answer: str, expected: float, tolerance: float = 0.0) -> bool:
    return any(abs(n - expected) <= tolerance for n in extract_numbers(answer))


def contains_match(answer: str, expected: str) -> bool:
    return str(expected).strip().lower() in answer.lower()


def parse_judge(raw: str) -> tuple[bool, str]:
    """Extract {"correct": bool, "reason": str} from a judge reply, tolerating surrounding prose."""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            return bool(data.get("correct")), str(data.get("reason", ""))
        except json.JSONDecodeError:
            pass
    return False, f"unparseable judge output: {raw[:80]!r}"


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, round(p * (len(s) - 1)))]
