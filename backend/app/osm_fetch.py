"""Download a local OpenStreetMap extract for the pilot area and write a data-coverage audit.

    python -m app.osm_fetch                       # pilot city centre, 7 km radius
    python -m app.osm_fetch --radius 3000
    python -m app.osm_fetch --endpoint https://your-overpass/api/interpreter   # only this server

Uses the Overpass API (fair-use; please do not hammer it). Writes:
    data/osm_<city>.json        used by the route evidence code
    docs/data-audit-<city>.md   how much of the map data is actually usable
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.core.config import settings
from app.schemas.routes import LatLng
from app.services.osm.hours import parse as parse_hours
from app.services.safety.geometry import haversine_m

DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
MIRRORS = [DEFAULT_ENDPOINT, "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
RETRY_STATUS = {429, 502, 503, 504}  # busy or restarting: worth another try
DEFAULT_RADIUS_M = 7000  # NIT Rourkela is ~4.9 km from the pilot centre; leave room for its eastern edge
WALKABLE = {"primary", "secondary", "tertiary", "trunk", "residential", "living_street", "pedestrian",
            "unclassified", "service", "footway", "path", "cycleway", "steps", "track"}
AMENITIES = "restaurant|cafe|fast_food|pharmacy|bank|atm|hospital|clinic|police|marketplace|fuel|bus_station"


def ways_query(lat: float, lng: float, r: int) -> str:
    return f'[out:json][timeout:180];way["highway"](around:{r},{lat},{lng});out tags geom;'


def pois_query(lat: float, lng: float, r: int) -> str:
    a = f"(around:{r},{lat},{lng})"
    return (f'[out:json][timeout:120];(nwr["shop"]{a};nwr["amenity"~"^({AMENITIES})$"]{a};'
            f'node["highway"="bus_stop"]{a};nwr["railway"="station"]{a};);out tags center;')


def convert_ways(raw: dict) -> list[dict]:
    out = []
    for e in raw.get("elements", []):
        t, g = e.get("tags", {}), e.get("geometry")
        if e.get("type") != "way" or not g or len(g) < 2 or t.get("highway") not in WALKABLE:
            continue
        sw = t.get("sidewalk") or ("both" if t.get("sidewalk:both") == "yes" else
                                   t.get("sidewalk:left") or t.get("sidewalk:right") or "")
        out.append({"id": e["id"], "hw": t["highway"], "lit": t.get("lit", ""), "sidewalk": sw,
                    "name": t.get("name", ""), "geom": [[p["lat"], p["lon"]] for p in g]})
    return out


def convert_pois(raw: dict) -> list[dict]:
    out = []
    for e in raw.get("elements", []):
        t = e.get("tags", {})
        c = e if "lat" in e else e.get("center")
        if not c:
            continue
        kind = ("shop" if "shop" in t else t.get("amenity") or
                ("bus_stop" if t.get("highway") == "bus_stop" else "station"))
        out.append({"id": f'{e["type"][0]}{e["id"]}', "kind": kind, "name": t.get("name", ""),
                    "lat": c["lat"], "lng": c["lon"], "hours": t.get("opening_hours", "")})
    return out


def _km(geom: list[list[float]]) -> float:
    return sum(haversine_m(LatLng(lat=a[0], lng=a[1]), LatLng(lat=b[0], lng=b[1])) for a, b in zip(geom, geom[1:])) / 1000


def summarise(ways: list[dict], pois: list[dict]) -> dict:
    """Pure function: coverage statistics, weighted by road length."""
    total = known_lit = lit_yes = lit_no = known_sw = 0.0
    by_class: dict[str, list[float]] = {}
    for w in ways:
        km = _km(w["geom"])
        total += km
        row = by_class.setdefault(w["hw"], [0.0, 0.0])
        row[0] += km
        if w["lit"] in ("yes", "no", "limited", "automatic", "24/7", "sunset-sunrise"):
            known_lit += km
            row[1] += km
            if w["lit"] == "no":
                lit_no += km
            else:
                lit_yes += km
        if w["sidewalk"]:
            known_sw += km
    named = sum(1 for p in pois if p["name"])
    with_hours = [p for p in pois if p["hours"]]
    parsable = sum(1 for p in with_hours if parse_hours(p["hours"]) is not None)
    kinds: dict[str, int] = {}
    for p in pois:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    pct = lambda a, b: round(100 * a / b, 1) if b else 0.0  # noqa: E731
    return {
        "road_km": round(total, 1), "ways": len(ways),
        "lit_known_pct": pct(known_lit, total), "lit_yes_pct": pct(lit_yes, total), "lit_no_pct": pct(lit_no, total),
        "sidewalk_known_pct": pct(known_sw, total),
        "classes": {k: {"km": round(v[0], 1), "lit_known_pct": pct(v[1], v[0])}
                    for k, v in sorted(by_class.items(), key=lambda x: -x[1][0])},
        "pois": len(pois), "named_pct": pct(named, len(pois)), "with_hours": len(with_hours),
        "hours_pct": pct(len(with_hours), len(pois)), "hours_parsable_pct": pct(parsable, len(with_hours)),
        "kinds": dict(sorted(kinds.items(), key=lambda x: -x[1])),
    }


def verdicts(s: dict) -> list[str]:
    v = []
    if s["lit_known_pct"] < 30:
        v.append(f"Lighting is known for only {s['lit_known_pct']}% of road length. Lighting evidence will usually be "
                 "UNKNOWN. Do not present lighting as a strong signal. Consider a mapping walk or mapathon to add `lit` tags.")
    else:
        v.append(f"Lighting is known for {s['lit_known_pct']}% of road length: usable, with uncertainty shown.")
    if s["sidewalk_known_pct"] < 30:
        v.append(f"Footpath information covers {s['sidewalk_known_pct']}% of roads: treat as mostly unknown.")
    if s["with_hours"] < 20 or s["hours_pct"] < 20:
        v.append("Few places have mapped opening hours, so 'open places nearby' will rarely be known. "
                 "Do not use it to claim an area is busy.")
    v.append("Road type is almost always available, but it is a weak proxy. Validate it with field walks before relying on it.")
    return v


def render(s: dict, city: str, fetched: str, radius: int) -> str:
    rows = "\n".join(f"| {k} | {c['km']} | {c['lit_known_pct']}% |" for k, c in list(s["classes"].items())[:10])
    kinds = ", ".join(f"{k}: {n}" for k, n in list(s["kinds"].items())[:12])
    return f"""# Data audit: {city}

Fetched {fetched[:10]} from OpenStreetMap, {radius} m around the pilot centre. OpenStreetMap is map data, not a safety database.

## Roads
- {s['ways']} ways, {s['road_km']} km
- `lit` tag known: **{s['lit_known_pct']}%** (lit: {s['lit_yes_pct']}%, unlit: {s['lit_no_pct']}%)
- Sidewalk/footpath known: **{s['sidewalk_known_pct']}%**

| Road class | km | lighting known |
|---|---|---|
{rows}

## Places
- {s['pois']} mapped places, {s['named_pct']}% named
- {s['with_hours']} with opening hours ({s['hours_pct']}%); {s['hours_parsable_pct']}% of those can be read by NariWay
- By kind: {kinds}

## What this means
""" + "\n".join(f"- {x}" for x in verdicts(s)) + "\n"


def fetch_json(client: httpx.Client, endpoints: list[str], query: str, attempts: int = 2,
               sleep=time.sleep, log=print) -> dict:
    """POST an Overpass query, retrying busy/failed servers and falling back to the next mirror."""
    last = "no server tried"
    for ep in endpoints:
        for i in range(attempts):
            try:
                r = client.post(ep, data={"data": query})
            except httpx.TransportError as e:  # timeouts, refused connections, DNS
                last = f"{ep} ({type(e).__name__})"
            else:
                if r.status_code == 200:
                    try:
                        return r.json()
                    except ValueError:  # Overpass can answer 200 with an HTML error page
                        last = f"{ep} (reply was not JSON)"
                elif r.status_code in RETRY_STATUS:
                    last = f"{ep} (HTTP {r.status_code})"
                else:
                    r.raise_for_status()
            log(f"  {last}: " + ("retrying" if i + 1 < attempts else "trying the next server"))
            sleep(5 * (i + 1))
    raise RuntimeError(f"All map data servers failed. Last problem: {last}. Try again in a few minutes, or use a smaller --radius.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--radius", type=int, default=DEFAULT_RADIUS_M, help="metres around the pilot centre")
    ap.add_argument("--endpoint", default=None, help="use only this Overpass server (default: try several public ones)")
    ap.add_argument("--out", default=settings.osm_data_path)
    ap.add_argument("--report", default=f"../docs/data-audit-{settings.pilot_city.lower()}.md")
    a = ap.parse_args()
    lat, lng = settings.pilot_lat, settings.pilot_lng
    endpoints = [a.endpoint] if a.endpoint else MIRRORS
    print(f"Fetching {settings.pilot_city} ({a.radius} m) from {endpoints[0]} ...")
    headers = {"User-Agent": settings.geocoder_user_agent}
    with httpx.Client(timeout=240, headers=headers) as c:
        try:
            ways = convert_ways(fetch_json(c, endpoints, ways_query(lat, lng, a.radius)))
            pois = convert_pois(fetch_json(c, endpoints, pois_query(lat, lng, a.radius)))
        except (httpx.HTTPError, RuntimeError) as e:
            sys.exit(f"Could not get map data: {e}")
    fetched = datetime.now(timezone.utc).isoformat()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"fetched_at": fetched, "center": [lat, lng], "radius_m": a.radius,
                                       "ways": ways, "pois": pois}, separators=(",", ":")))
    s = summarise(ways, pois)
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(render(s, settings.pilot_city, fetched, a.radius))
    print(render(s, settings.pilot_city, fetched, a.radius))
    print(f"Saved {a.out} and {a.report}")


if __name__ == "__main__":
    main()
