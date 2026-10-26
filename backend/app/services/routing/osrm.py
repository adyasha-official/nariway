"""OSRM-compatible client. Point ROUTING_PROVIDER_URL at a self-hosted instance.

The public demo server is not for production use. Alternatives from OSRM are often
near-duplicates, so callers should run dedupe_similar() on the result.
"""

import httpx

from app.schemas.routes import CandidateRoute, LatLng

PROFILE = {"walk": "foot", "bike": "bike", "cab": "driving"}


async def osrm_routes(base_url: str, o: LatLng, d: LatLng, mode: str) -> list[CandidateRoute]:
    url = f"{base_url.rstrip('/')}/route/v1/{PROFILE[mode]}/{o.lng},{o.lat};{d.lng},{d.lat}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params={"alternatives": "3", "overview": "full", "geometries": "geojson"})
        r.raise_for_status()
    return [
        CandidateRoute(
            id=f"osrm-{i}",
            geometry=[LatLng(lat=lat, lng=lng) for lng, lat in rt["geometry"]["coordinates"]],
            duration_s=max(rt["duration"], 1.0),
            distance_m=max(rt["distance"], 1.0),
        )
        for i, rt in enumerate(r.json().get("routes", []))
    ]
