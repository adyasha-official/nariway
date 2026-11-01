"""Minimal OpenStreetMap `opening_hours` evaluator.

Supports the common patterns: "24/7", "Mo-Sa 09:00-21:00", "Mo-Fr 09:00-13:00,16:00-21:00; Su off",
overnight ranges ("20:00-02:00") and later rules overriding earlier ones.
Anything else (PH, sunrise, months, week numbers...) returns None = unknown. Never a guess.
"""

import re
from datetime import datetime

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
_TIME = r"\d{1,2}:\d{2}"
_RANGE = re.compile(rf"^({_TIME})-({_TIME})$")
_DAYTOK = re.compile(r"^(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?$")


def _mins(t: str) -> int | None:
    h, m = map(int, t.split(":"))
    return h * 60 + m if 0 <= h <= 24 and 0 <= m < 60 else None


def _days(tok: str) -> set[int] | None:
    out: set[int] = set()
    for part in tok.split(","):
        m = _DAYTOK.match(part)
        if not m:
            return None
        a = DAYS.index(m.group(1))
        b = DAYS.index(m.group(2)) if m.group(2) else a
        out |= set(range(a, b + 1)) if a <= b else set(range(a, 7)) | set(range(0, b + 1))
    return out


def parse(spec: str):
    """Return 'always', or a list of (days, intervals) rules, or None if unsupported."""
    spec = (spec or "").strip()
    if not spec:
        return None
    if spec == "24/7":
        return "always"
    rules = []
    for raw in spec.split(";"):
        raw = raw.strip()
        if not raw:
            continue
        tokens = raw.split(None, 1)
        if _days(tokens[0]) is not None:
            days, rest = _days(tokens[0]), (tokens[1].strip() if len(tokens) > 1 else "")
        else:
            days, rest = set(range(7)), raw
        if rest in ("off", "closed"):
            rules.append((days, []))
            continue
        intervals = []
        for r in rest.split(","):
            m = _RANGE.match(r.strip())
            if not m:
                return None
            a, b = _mins(m.group(1)), _mins(m.group(2))
            if a is None or b is None:
                return None
            intervals.append((a, b if b > a else b + 1440))  # overnight wraps past midnight
        rules.append((days, intervals))
    return rules or None


def _intervals_for(rules, day: int) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for days, intervals in rules:  # later matching rules override earlier ones
        if day in days:
            result = intervals
    return result


def is_open(spec: str, when: datetime) -> bool | None:
    """True/False if we can tell, None if the spec is unsupported. `when` must be in local time."""
    rules = parse(spec)
    if rules is None:
        return None
    if rules == "always":
        return True
    t, day = when.hour * 60 + when.minute, when.weekday()
    if any(a <= t < b for a, b in _intervals_for(rules, day)):
        return True
    # still open from yesterday's overnight range?
    return any(b > 1440 and t < b - 1440 for _, b in _intervals_for(rules, (day - 1) % 7))
