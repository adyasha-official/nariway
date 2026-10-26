"""Clearly-labelled demo routing provider: synthetic paths + synthetic evidence.

Used when ROUTING_PROVIDER_URL is empty, so the UI works offline. Everything it
returns carries is_demo=True and must be shown as sample data.
"""

from math import cos, hypot, radians

from app.schemas.routes import (
    CandidateRoute, IndicatorValue, LatLng, NearbyReport, RouteEvidence,
)
from app.services.safety.geometry import polyline_length_m

SPEED_MPS = {"walk": 1.3, "bike": 4.2, "cab": 8.0}


def _bend(o: LatLng, d: LatLng, offset: float, n: int = 24) -> list[LatLng]:
    """Quadratic curve from o to d, bulging sideways by `offset` (fraction of length)."""
    dx, dy = d.lng - o.lng, d.lat - o.lat
    nx, ny = -dy, dx
    mx, my = (o.lng + d.lng) / 2 + nx * offset, (o.lat + d.lat) / 2 + ny * offset
    pts = []
    for i in range(n + 1):
        t = i / n
        lng = (1 - t) ** 2 * o.lng + 2 * (1 - t) * t * mx + t ** 2 * d.lng
        lat = (1 - t) ** 2 * o.lat + 2 * (1 - t) * t * my + t ** 2 * d.lat
        pts.append(LatLng(lat=lat, lng=lng))
    return pts


def demo_routes(o: LatLng, d: LatLng, mode: str) -> list[CandidateRoute]:
    speed = SPEED_MPS[mode]
    specs = [  # id, bend, (lighting concern, cov), (main-road concern, cov), report
        ("fast", 0.0, (0.70, 0.5), (0.60, 0.5), True),
        ("balanced", 0.2, (0.40, 0.6), (0.35, 0.7), False),
        ("safe", -0.6, (0.15, 0.8), (0.15, 0.8), False),
    ]
    out = []
    for rid, bend, light, road, with_report in specs:
        pts = _bend(o, d, bend)
        dist = polyline_length_m(pts)
        ev = RouteEvidence(
            is_demo=True,
            indicators=[
                IndicatorValue(key="lighting", label="Street lighting", value=light[0], coverage=light[1],
                               source="demo", note="Sample data"),
                IndicatorValue(key="road_type", label="Main-road share", value=road[0], coverage=road[1],
                               source="demo", note="Sample data"),
                IndicatorValue(key="open_places", label="Open places nearby", value=None, coverage=0.0,
                               source="unknown", note="No opening-hours data for this area"),
            ],
            reports=[NearbyReport(id="demo-1", category="poor_lighting", age_days=6, distance_m=60, is_demo=True)]
            if with_report else [],
            facilities_nearby=1 if rid == "safe" else 0,
        )
        out.append(CandidateRoute(id=rid, geometry=pts, duration_s=dist / speed, distance_m=dist, evidence=ev))
    return out
