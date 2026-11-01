import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.services.osm.store import get_store

router = APIRouter(prefix="/api/v1/places", tags=["places"])


class Place(BaseModel):
    name: str
    lat: float
    lng: float


# Small gazetteer of pilot-city landmarks (approximate coordinates), used offline and to fill gaps in map data.
DEMO_PLACES = [
    Place(name="NIT Rourkela", lat=22.2536, lng=84.9006),
    Place(name="Rourkela Railway Station", lat=22.2290, lng=84.8640),
    Place(name="Rourkela Steel Plant Gate", lat=22.2370, lng=84.8660),
    Place(name="Ispat General Hospital", lat=22.2380, lng=84.8750),
    Place(name="Sector 2 Market", lat=22.2500, lng=84.8830),
    Place(name="City Centre, Udit Nagar", lat=22.2420, lng=84.8730),
]


@router.get("/search", response_model=list[Place])
async def search(q: str = Query(min_length=2, max_length=100)) -> list[Place]:
    if not settings.geocoder_url:
        # Search the downloaded map data first. This avoids hitting public geocoders, whose policy forbids
        # search-as-you-type. Without map data, fall back to the small demo list.
        store = get_store(settings.osm_data_path)
        hits = [Place(**h) for h in store.search(q)] if store else []
        # Landmarks such as campuses and stations are often not tagged as places in the map data, so add the
        # small list of known pilot-city landmarks after the map hits.
        seen = {h.name.lower() for h in hits}
        hits += [p for p in DEMO_PLACES if q.lower() in p.name.lower() and p.name.lower() not in seen]
        return hits[:6]
    try:
        async with httpx.AsyncClient(timeout=8, headers={"User-Agent": settings.geocoder_user_agent}) as c:
            r = await c.get(f"{settings.geocoder_url.rstrip('/')}/search",
                            params={"q": q, "format": "jsonv2", "limit": 6, "countrycodes": "in"})
            r.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(503, "Search is unavailable right now.")
    return [Place(name=x["display_name"], lat=float(x["lat"]), lng=float(x["lon"])) for x in r.json()]
