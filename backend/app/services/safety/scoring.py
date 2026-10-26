"""Transparent, rules-based route scoring (model v0.2).

C(r) = w_t*T + w_d*D + w_r*R + w_u*U, lower is better.

- T, D: normalised against the best candidate, so only relative differences matter.
- R: evidence-based concern in [0,1]. Missing evidence is NOT safe: R is None when
  nothing is known, and U (uncertainty) rises instead.
- U = 1 - evidence_coverage, so a route is never rewarded for silence.
- Reports decay with a per-category half-life.
These numbers are a decision aid, not a probability of harm.
"""

from app.core.config import settings
from app.schemas.routes import (
    AssessResponse, CandidateRoute, IndicatorValue, Preference, RouteAssessment,
)

MODEL_VERSION = "rules-v0.2"
DISCLAIMER = "Assessments reflect available evidence only. No route can be guaranteed safe."

# (w_time, w_distance, w_risk, w_uncertainty)
WEIGHTS: dict[Preference, tuple[float, float, float, float]] = {
    "fastest": (0.75, 0.20, 0.04, 0.01),
    "balanced": (0.35, 0.15, 0.30, 0.20),
    "safety_first": (0.12, 0.08, 0.45, 0.35),
}
PREFERENCES: tuple[Preference, ...] = ("safety_first", "balanced", "fastest")

UNKNOWN_RISK = 0.5  # used only inside the cost; never shown as a risk value
HALF_LIFE_DAYS = {"harassment": 30.0, "poor_lighting": 90.0, "isolated": 60.0, "other": 14.0}
REPORT_RADIUS_M = 150.0


def _norm(value: float, best: float) -> float:
    return (value - best) / best if best > 0 else 0.0


def _report_concern(c: CandidateRoute) -> tuple[float | None, list[str]]:
    if not c.evidence or not c.evidence.reports:
        return None, []
    total, hazards = 0.0, []
    for r in c.evidence.reports:
        if r.distance_m > REPORT_RADIUS_M:
            continue
        hl = HALF_LIFE_DAYS.get(r.category, HALF_LIFE_DAYS["other"])
        weight = 0.5 ** (r.age_days / hl)
        total += 0.3 * weight
        if weight > 0.25:
            tag = " (sample data)" if r.is_demo else ""
            hazards.append(f"Recent {r.category.replace('_', ' ')} report within {round(r.distance_m)} m{tag}")
    return (min(1.0, total) if hazards or total else None), hazards


def summarise(c: CandidateRoute) -> tuple[float | None, float, list[IndicatorValue], list[str]]:
    """Return (risk, coverage, indicators, hazards). risk None == unknown."""
    inds = c.evidence.indicators if c.evidence else []
    known = [i for i in inds if i.value is not None and i.coverage > 0]
    num = sum(i.value * i.coverage for i in known)  # type: ignore[operator]
    den = sum(i.coverage for i in known)
    base = num / den if den else None
    rep, hazards = _report_concern(c)
    if base is None and rep is None:
        risk = None
    else:
        risk = min(1.0, (base or 0.0) + (rep or 0.0) * 0.5)
    coverage = sum(i.coverage if i.value is not None else 0.0 for i in inds) / len(inds) if inds else 0.0
    for i in known:
        if i.value >= 0.7:  # type: ignore[operator]
            hazards.append(f"{i.label}: concern on part of this route")
    return risk, round(min(1.0, coverage), 3), inds, hazards


def _confidence(coverage: float) -> str:
    return "higher" if coverage >= 0.7 else "medium" if coverage >= 0.4 else "low"


def assess(candidates: list[CandidateRoute]) -> AssessResponse:
    best_t = min(c.duration_s for c in candidates)
    best_d = min(c.distance_m for c in candidates)
    info = {c.id: summarise(c) for c in candidates}
    too_slow = {c.id for c in candidates if c.duration_s > best_t * settings.max_detour_ratio}

    def cost(c: CandidateRoute, pref: Preference) -> float:
        w_t, w_d, w_r, w_u = WEIGHTS[pref]
        risk, cov, _, _ = info[c.id]
        return (w_t * _norm(c.duration_s, best_t) + w_d * _norm(c.distance_m, best_d)
                + w_r * (risk if risk is not None else UNKNOWN_RISK) + w_u * (1 - cov))

    recommended: dict[Preference, str] = {}
    for pref in PREFERENCES:
        pool = [c for c in candidates if pref == "fastest" or c.id not in too_slow] or candidates
        recommended[pref] = min(pool, key=lambda c: cost(c, pref)).id

    order = sorted(candidates, key=lambda c: cost(c, "balanced"))
    out: list[RouteAssessment] = []
    for rank, c in enumerate(order, 1):
        risk, cov, inds, hazards = info[c.id]
        labels = [p for p in PREFERENCES if recommended[p] == c.id]
        reasons = [f"{round(c.duration_s / 60)} min, {c.distance_m / 1000:.1f} km"]
        if risk is None:
            reasons.append("No safety evidence found for this route; treated as unknown, not as safe.")
        if cov < 0.4:
            reasons.append("Low data coverage: treat this assessment with caution.")
        if c.id in too_slow:
            reasons.append(f"Much slower than the fastest option, so not offered as a safer pick.")
        out.append(RouteAssessment(
            route_id=c.id, rank=rank, cost=round(cost(c, "balanced"), 4),
            risk=None if risk is None else round(risk, 3), uncertainty=round(1 - cov, 3),
            evidence_coverage=cov, confidence_label=_confidence(cov),  # type: ignore[arg-type]
            labels=labels, excluded_for_detour=c.id in too_slow,
            reasons=reasons, hazards=hazards, indicators=inds,
        ))
    return AssessResponse(
        model_version=MODEL_VERSION, disclaimer=DISCLAIMER,
        is_demo=any(c.evidence and c.evidence.is_demo for c in candidates),
        recommended=recommended, assessments=out,
    )
