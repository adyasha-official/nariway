"""OSRM-compatible client with route diversity.

OSRM's own alternatives are often near-duplicates, and many streets give only one. So we also
ask for routes forced through via-points offset to either side of the midpoint, then drop
near-copies and anything much slower than the best route.

The public demo servers are fair-use and not for production. Self-host for the pilot.
"""

from math import cos, radians

import httpx

from app.core.config import settings
from app.schemas.routes import CandidateRoute, LatLng
from app.services.safety.geometry import dedupe_similar, haversine_m

MAX_ROUTES = 4
VIA_OFFSETS = (0.22, -0.22)  # sideways offset as a fraction of the trip length


def base_url_for(mode: str) -> str:
    return getattr(settings, f"routing_url_{mode}", "") or settings.routing_provider_url


def _parse(data: dict, prefix: str) -> list[CandidateRoute]:
    return [
        CandidateRoute(
            id=f"{prefix}-{i}",
            geometry=[LatLng(lat=lat, lng=lng) for lng, lat in rt["geometry"]["coordinates"]],
            duration_s=max(rt["duration"], 1.0),
            distance_m=max(rt["distance"], 1.0),
        )
        for i, rt in enumerate(data.get("routes", []))
        if len(rt["geometry"]["coordinates"]) >= 2
    ]


def via_points(o: LatLng, d: LatLng) -> list[LatLng]:
    """Points on either side of the midpoint, perpendicular to the straight line."""
    mid_lat, mid_lng = (o.lat + d.lat) / 2, (o.lng + d.lng) / 2
    k = cos(radians(mid_lat))
    dx, dy = (d.lng - o.lng) * k, d.lat - o.lat  # local planar approximation
    nx, ny = -dy, dx
    return [LatLng(lat=mid_lat + ny * f, lng=mid_lng + nx * f / k) for f in VIA_OFFSETS]


async def _fetch(client: httpx.AsyncClient, base: str, coords: list[LatLng], alternatives: bool) -> list[CandidateRoute]:
    path = ";".join(f"{c.lng},{c.lat}" for c in coords)
    r = await client.get(
        f"{base.rstrip('/')}/route/v1/{settings.routing_path_profile}/{path}",
        params={"alternatives": "3" if alternatives else "false", "overview": "full", "geometries": "geojson"},
    )
    if r.status_code == 400:  # OSRM says "NoSegment" when a point is not near any road it knows
        try:
            code = r.json().get("code")
        except ValueError:
            code = None
        if code in ("NoSegment", "NoRoute"):
            return []
    r.raise_for_status()
    data = r.json()
    if data.get("code") not in (None, "Ok", "NoRoute"):
        raise httpx.HTTPError(f"routing error: {data.get('code')}")
    return _parse(data, "r")


async def candidate_routes(
    o: LatLng, d: LatLng, mode: str, client: httpx.AsyncClient | None = None
) -> list[CandidateRoute]:
    base = base_url_for(mode)
    own = client is None
    client = client or httpx.AsyncClient(timeout=12, headers={"User-Agent": settings.geocoder_user_agent})
    try:
        routes = await _fetch(client, base, [o, d], alternatives=True)
        if not routes:
            return []  # nothing near a road, or no connection: via-points cannot help
        if len(dedupe_similar(routes)) < 3:
            for v in via_points(o, d):
                try:
                    routes += await _fetch(client, base, [o, v, d], alternatives=False)
                except httpx.HTTPError:
                    continue  # via-point may not snap to a road; the direct routes are still valid
    finally:
        if own:
            await client.aclose()
    routes.sort(key=lambda r: r.duration_s)
    if not routes:
        return []
    kept = [r for r in dedupe_similar(routes) if r.duration_s <= routes[0].duration_s * settings.max_detour_ratio]
    kept = kept[:MAX_ROUTES]
    for i, r in enumerate(kept):
        r.id = f"route-{i + 1}"
    return kept


def trip_length_m(o: LatLng, d: LatLng) -> float:
    return haversine_m(o, d)
