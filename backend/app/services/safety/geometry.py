"""Small, dependency-free geometry helpers (metres, WGS84). PostGIS replaces these at scale."""

from math import asin, cos, radians, sin, sqrt

from app.schemas.routes import LatLng

EARTH_R = 6_371_000.0


def haversine_m(a: LatLng, b: LatLng) -> float:
    dlat, dlng = radians(b.lat - a.lat), radians(b.lng - a.lng)
    h = sin(dlat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(dlng / 2) ** 2
    return 2 * EARTH_R * asin(sqrt(h))


def polyline_length_m(pts: list[LatLng]) -> float:
    return sum(haversine_m(a, b) for a, b in zip(pts, pts[1:]))


def _to_xy(p: LatLng, ref: LatLng) -> tuple[float, float]:
    return (
        radians(p.lng - ref.lng) * EARTH_R * cos(radians(ref.lat)),
        radians(p.lat - ref.lat) * EARTH_R,
    )


def point_segment_distance_m(p: LatLng, a: LatLng, b: LatLng) -> float:
    px, py = _to_xy(p, a)
    bx, by = _to_xy(b, a)
    seg2 = bx * bx + by * by
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, (px * bx + py * by) / seg2))
    return sqrt((px - t * bx) ** 2 + (py - t * by) ** 2)


def point_polyline_distance_m(p: LatLng, pts: list[LatLng]) -> float:
    return min(point_segment_distance_m(p, a, b) for a, b in zip(pts, pts[1:]))


def interpolate(pts: list[LatLng], step_m: float) -> list[LatLng]:
    """Sample points along a polyline roughly every step_m metres."""
    out = [pts[0]]
    carry = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = haversine_m(a, b)
        if seg == 0:
            continue
        d = step_m - carry
        while d <= seg:
            f = d / seg
            out.append(LatLng(lat=a.lat + (b.lat - a.lat) * f, lng=a.lng + (b.lng - a.lng) * f))
            d += step_m
        carry = seg - (d - step_m)
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


def overlap_fraction(a: list[LatLng], b: list[LatLng], tol_m: float = 30.0) -> float:
    """Share of route a (by sampled length) that lies within tol_m of route b."""
    samples = interpolate(a, 40.0)
    near = sum(1 for p in samples if point_polyline_distance_m(p, b) <= tol_m)
    return near / len(samples)


def dedupe_similar(routes: list, threshold: float = 0.9) -> list:
    """Drop alternatives that are near-copies of an earlier one (OSRM often returns these)."""
    kept: list = []
    for r in routes:
        if all(overlap_fraction(r.geometry, k.geometry) < threshold for k in kept):
            kept.append(r)
    return kept
