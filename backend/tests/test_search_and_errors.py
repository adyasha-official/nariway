import asyncio
import json

import httpx

from app.osm_fetch import DEFAULT_RADIUS_M
from app.schemas.routes import LatLng
from app.services.osm.store import OsmStore
from app.services.routing import osrm
from app.services.safety.geometry import haversine_m

CENTER = LatLng(lat=22.2604, lng=84.8536)
NIT = LatLng(lat=22.2536, lng=84.9006)

WAYS = [
    {"id": 1, "hw": "primary", "lit": "", "sidewalk": "", "name": "Ring Road", "geom": [[22.25, 84.85], [22.25, 84.86], [22.25, 84.87]]},
    {"id": 2, "hw": "residential", "lit": "", "sidewalk": "", "name": "Scholars Avenue", "geom": [[22.26, 84.85], [22.26, 84.86]]},
    {"id": 3, "hw": "residential", "lit": "", "sidewalk": "", "name": "Ring Road", "geom": [[22.30, 84.90], [22.30, 84.91]]},  # same name, later segment
    {"id": 4, "hw": "path", "lit": "", "sidewalk": "", "name": "", "geom": [[22.27, 84.85], [22.27, 84.86]]},  # unnamed
]
POIS = [
    {"id": "n1", "kind": "station", "name": "Rourkela Junction", "lat": 22.229, "lng": 84.864, "hours": ""},
    {"id": "n2", "kind": "hospital", "name": "Ispat General Hospital", "lat": 22.238, "lng": 84.875, "hours": "24/7"},
    {"id": "n3", "kind": "shop", "name": "", "lat": 22.25, "lng": 84.86, "hours": ""},  # unnamed shops are not searchable
]


def store():
    return OsmStore(fetched_at="2026-10-26T00:00:00+00:00", ways=WAYS, pois=POIS)


# ---------- fetch radius ----------
def test_default_radius_covers_nit_campus_with_room_to_spare():
    assert haversine_m(CENTER, NIT) + 1500 <= DEFAULT_RADIUS_M


# ---------- local place search ----------
def test_search_ranks_prefix_then_word_start_then_substring():
    # "Rourkela Junction" starts with "ro" (prefix); "Ring Road" only has a word starting with it
    assert [h["name"] for h in store().search("ro")] == ["Rourkela Junction", "Ring Road"]
    assert [h["name"] for h in store().search("hospital")] == ["Ispat General Hospital"]  # word start
    assert [h["name"] for h in store().search("junct")] == ["Rourkela Junction"]  # substring
    assert store().search("zzzz") == []


def test_search_dedupes_street_names_and_skips_unnamed():
    hits = store().search("ring road")
    assert len(hits) == 1 and hits[0]["name"] == "Ring Road"
    assert store().search("a") == []  # one character is too short to search


def test_places_api_uses_map_data_then_demo_list(client, tmp_path, monkeypatch):
    from app.api import places as places_api
    from app.services.osm import store as store_mod

    f = tmp_path / "osm.json"
    f.write_text(json.dumps({"fetched_at": "2026-10-26T00:00:00+00:00", "ways": WAYS, "pois": POIS}))
    monkeypatch.setattr(places_api.settings, "osm_data_path", str(f))
    store_mod._cache.clear()
    got = client.get("/api/v1/places/search", params={"q": "scholars"}).json()
    assert got == [{"name": "Scholars Avenue", "lat": 22.26, "lng": 84.86}]
    assert client.get("/api/v1/places/search", params={"q": "nit"}).json() == []  # map data wins over the demo list

    monkeypatch.setattr(places_api.settings, "osm_data_path", str(tmp_path / "missing.json"))
    store_mod._cache.clear()
    assert any("NIT" in p["name"] for p in client.get("/api/v1/places/search", params={"q": "nit"}).json())


# ---------- OSRM "no road nearby" ----------
def test_no_segment_is_not_an_outage_and_skips_via_requests():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(400, json={"code": "NoSegment", "message": "Could not find a matching segment"})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            return await osrm.candidate_routes(LatLng(lat=22.25, lng=84.85), LatLng(lat=22.26, lng=84.86), "walk", client=c)

    from app.core.config import settings
    settings.routing_url_walk = "http://fake"
    try:
        assert asyncio.run(go()) == []
    finally:
        settings.routing_url_walk = ""
    assert len(calls) == 1  # no via-point retries


def test_api_returns_404_with_clear_message_for_unroutable_points(client, monkeypatch):
    from app.api import routes as api_routes

    monkeypatch.setattr(api_routes.settings, "routing_url_walk", "http://fake")

    async def none(o, d, mode):
        return []

    monkeypatch.setattr(api_routes, "candidate_routes", none)
    body = {"origin": {"lat": 22.25, "lng": 84.85}, "destination": {"lat": 22.26, "lng": 84.86}, "mode": "walk"}
    r = client.post("/api/v1/routes/alternatives", json=body)
    assert r.status_code == 404 and "near a road" in r.json()["detail"]


# ---------- Overpass retry and mirror fallback ----------
def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_falls_back_to_next_mirror_after_502s():
    from app.osm_fetch import fetch_json

    hosts, logs = [], []

    def handler(request: httpx.Request) -> httpx.Response:
        hosts.append(request.url.host)
        if request.url.host == "a.example":
            return httpx.Response(502)
        return httpx.Response(200, json={"elements": []})

    got = fetch_json(_client(handler), ["https://a.example/x", "https://b.example/x"], "q",
                     attempts=2, sleep=lambda s: None, log=logs.append)
    assert got == {"elements": []}
    assert hosts == ["a.example", "a.example", "b.example"]  # two tries, then the mirror
    assert any("trying the next server" in line for line in logs)


def test_fetch_retries_transport_errors_and_html_replies():
    from app.osm_fetch import fetch_json

    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            raise httpx.ConnectError("down")
        if len(calls) == 2:
            return httpx.Response(200, text="<html>runtime error</html>")
        return httpx.Response(200, json={"elements": [1]})

    assert fetch_json(_client(handler), ["https://a.example/x"], "q", attempts=3, sleep=lambda s: None, log=lambda m: None) == {"elements": [1]}


def test_fetch_gives_up_with_a_plain_message_and_does_not_retry_bad_queries():
    import pytest
    from app.osm_fetch import fetch_json

    with pytest.raises(RuntimeError, match="All map data servers failed"):
        fetch_json(_client(lambda r: httpx.Response(504)), ["https://a.example/x"], "q",
                   attempts=2, sleep=lambda s: None, log=lambda m: None)

    seen = []

    def bad(request: httpx.Request) -> httpx.Response:
        seen.append(1)
        return httpx.Response(400, text="bad query")

    with pytest.raises(httpx.HTTPStatusError):
        fetch_json(_client(bad), ["https://a.example/x", "https://b.example/x"], "q",
                   attempts=2, sleep=lambda s: None, log=lambda m: None)
    assert len(seen) == 1  # a malformed query would fail everywhere, so stop immediately


# ---------- honest warning when almost nothing is mapped ----------
def test_low_data_note_appears_when_evidence_is_thin(client, tmp_path, monkeypatch):
    from app.api import routes as api_routes
    from app.schemas.routes import CandidateRoute
    from app.services.osm import store as store_mod

    monkeypatch.setattr(api_routes.settings, "osm_data_path", str(tmp_path / "missing.json"))
    monkeypatch.setattr(api_routes.settings, "routing_url_walk", "http://fake")
    store_mod._cache.clear()

    async def fake(o, d, mode):
        return [CandidateRoute(id="r", geometry=[LatLng(lat=22.25, lng=84.85), LatLng(lat=22.25, lng=84.86)],
                               duration_s=600, distance_m=900)]

    monkeypatch.setattr(api_routes, "candidate_routes", fake)
    body = {"origin": {"lat": 22.25, "lng": 84.85}, "destination": {"lat": 22.25, "lng": 84.86}, "mode": "walk"}
    notes = client.post("/api/v1/routes/alternatives", json=body).json()["data_notes"]
    assert any("Very little safety data" in n for n in notes)


def test_no_low_data_note_on_demo_routes(client):
    body = {"origin": {"lat": 22.2536, "lng": 84.9006}, "destination": {"lat": 22.229, "lng": 84.864}, "mode": "walk"}
    assert client.post("/api/v1/routes/alternatives", json=body).json()["data_notes"] == []


# ---------- regression: a mapped trail must not look safer than a street ----------
SPARSE_ROAD = {"id": 1, "hw": "residential", "lit": "", "sidewalk": "", "name": "", "geom": [[22.25, 84.85], [22.25, 84.87]]}
SPARSE_PATH = {"id": 2, "hw": "path", "lit": "", "sidewalk": "", "name": "", "geom": [[22.26, 84.85], [22.26, 84.87]]}


def _sparse_routes():
    from datetime import datetime, timezone

    from app.schemas.routes import CandidateRoute
    from app.services.osm.evidence import attach_osm_evidence

    st = OsmStore(fetched_at="2026-11-01T00:00:00+00:00", ways=[SPARSE_ROAD, SPARSE_PATH], pois=[])
    mk = lambda i, lat: CandidateRoute(id=i, geometry=[LatLng(lat=lat, lng=84.851), LatLng(lat=lat, lng=84.869)],  # noqa: E731
                                       duration_s=700, distance_m=1900)
    rs = [mk("street", 22.25), mk("trail", 22.26)]
    attach_osm_evidence(rs, st, datetime.now(timezone.utc))
    return rs


def test_isolated_trail_is_not_scored_safer_than_a_street_when_only_road_class_is_mapped():
    from app.services.safety.scoring import assess

    a = {x.route_id: x for x in assess(_sparse_routes()).assessments}
    assert a["trail"].risk > a["street"].risk  # trail: 0.75 vs street: 0.4 road-class concern
    ped = {i.key: i for i in a["trail"].indicators}["pedestrian"]
    assert ped.value is None and ped.coverage == 0  # being a footpath is not footpath evidence


def test_road_class_alone_gives_low_confidence_and_triggers_the_low_data_note(client, tmp_path, monkeypatch):
    from app.api import routes as api_routes
    from app.services.osm import store as store_mod

    f = tmp_path / "osm.json"
    f.write_text(json.dumps({"fetched_at": "2026-11-01T00:00:00+00:00", "ways": [SPARSE_ROAD, SPARSE_PATH], "pois": []}))
    monkeypatch.setattr(api_routes.settings, "osm_data_path", str(f))
    monkeypatch.setattr(api_routes.settings, "routing_url_walk", "http://fake")
    store_mod._cache.clear()

    async def fake(o, d, mode):
        rs = _sparse_routes()
        return rs

    # attach_osm_evidence runs again inside the API, which is fine: it replaces evidence from the same map
    monkeypatch.setattr(api_routes, "candidate_routes", fake)
    body = {"origin": {"lat": 22.25, "lng": 84.851}, "destination": {"lat": 22.25, "lng": 84.869}, "mode": "walk"}
    j = client.post("/api/v1/routes/alternatives", json=body).json()
    assert all(a["confidence_label"] == "low" for a in j["result"]["assessments"])
    assert any("Very little safety data" in n for n in j["data_notes"])
