"""Turn a route plus a local OSM extract into evidence indicators.

Principles:
- Every indicator carries coverage = the share of the route where it is actually known.
- Nothing in OSM about a spot means UNKNOWN, never "fine" and never "dangerous".
- The road-type concern values below are a documented heuristic, not a measurement.
"""

from datetime import datetime, timedelta, timezone

from app.schemas.routes import CandidateRoute, IndicatorValue, LatLng, RouteEvidence
from app.services.osm.hours import is_open
from app.services.osm.store import OsmStore
from app.services.safety.geometry import haversine_m, interpolate

IST = timezone(timedelta(hours=5, minutes=30))  # India has no daylight saving
SAMPLE_M = 30.0
MATCH_M = 25.0
POI_M = 60.0
FACILITY_M = 150.0
FACILITY_KINDS = {"police", "hospital", "pharmacy"}

# Heuristic concern by road class (0 = fewer concerns, 1 = more). Busy main roads have more people
# around; paths and tracks are more isolated. Tune against field validation.
ROAD_CONCERN = {
    "primary": 0.25, "secondary": 0.25, "tertiary": 0.3, "trunk": 0.35, "residential": 0.4,
    "living_street": 0.35, "pedestrian": 0.3, "unclassified": 0.5, "service": 0.65,
    "footway": 0.6, "path": 0.75, "cycleway": 0.6, "steps": 0.6, "track": 0.85,
}
LIT_YES = {"yes", "24/7", "automatic", "sunset-sunrise"}
SIDEWALK_YES = {"both", "left", "right", "yes", "separate"}
SIDEWALK_NO = {"no", "none"}


def _lighting(w: dict) -> float | None:
    lit = (w.get("lit") or "").lower()
    if lit in LIT_YES:
        return 0.0
    if lit == "no":
        return 1.0
    if lit == "limited":
        return 0.5
    return None


def _sidewalk(w: dict) -> float | None:
    # Only explicit `sidewalk` tags count. A way that is itself a footpath or trail says nothing about
    # safety (it may be isolated), and that isolation is already reflected in the road-type heuristic.
    sw = (w.get("sidewalk") or "").lower()
    if sw in SIDEWALK_YES:
        return 0.0
    if sw in SIDEWALK_NO:
        return 0.7
    return None


def build_evidence(route: CandidateRoute, store: OsmStore, when: datetime) -> RouteEvidence:
    local = when.astimezone(IST)
    samples = interpolate(route.geometry, SAMPLE_M)
    n = len(samples)
    src = f"osm:{store.fetched_at[:10]}"

    light, side, road, places = [], [], [], []
    facilities: set[str] = set()
    for s in samples:
        w = store.nearest_way(s, MATCH_M)
        if w is not None:
            if (v := _lighting(w)) is not None:
                light.append(v)
            if (v := _sidewalk(w)) is not None:
                side.append(v)
            if w.get("hw") in ROAD_CONCERN:
                road.append(ROAD_CONCERN[w["hw"]])
        near = store.pois_near(s, max(POI_M, FACILITY_M))
        for p in near:
            if p["kind"] in FACILITY_KINDS:
                facilities.add(p["id"])  # pois_near already limits to FACILITY_M
        states = [is_open(p["hours"], local) for p in near if p.get("hours") and haversine_m(s, LatLng(lat=p["lat"], lng=p["lng"])) <= POI_M]
        states = [x for x in states if x is not None]
        if states:  # at least one nearby place whose hours we can read
            places.append(0.0 if any(states) else 0.7)

    def ind(key: str, label: str, vals: list[float], note: str) -> IndicatorValue:
        return IndicatorValue(
            key=key, label=label, value=round(sum(vals) / len(vals), 3) if vals else None,
            coverage=round(len(vals) / n, 3), source=src if vals else "unknown",
            note=note if vals else "No map data for this route",
        )

    return RouteEvidence(
        indicators=[
            ind("lighting", "Street lighting", light, "From OpenStreetMap `lit` tags"),
            ind("pedestrian", "Footpaths", side, "From `sidewalk` tags on roads"),
            ind("road_type", "Road type", road, "Heuristic by road class"),
            ind("open_places", "Open places nearby", places, f"Shops open at {local:%H:%M} IST, where hours are mapped"),
        ],
        facilities_nearby=len(facilities),
        is_demo=False,
    )


def attach_osm_evidence(routes: list[CandidateRoute], store: OsmStore, when: datetime) -> None:
    for r in routes:
        built = build_evidence(r, store, when)
        if r.evidence is None:
            r.evidence = built
        else:  # keep reports already attached
            built.reports = r.evidence.reports
            r.evidence = built
