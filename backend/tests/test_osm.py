import json
from datetime import datetime, timedelta, timezone

import pytest

from app.osm_fetch import convert_pois, convert_ways, summarise, verdicts
from app.schemas.routes import CandidateRoute, LatLng
from app.services.osm.evidence import IST, build_evidence
from app.services.osm.hours import is_open, parse
from app.services.osm.store import OsmStore
from app.services.safety.scoring import assess


def at(day_offset_from_monday: int, hh: int, mm: int = 0) -> datetime:
    return datetime(2026, 10, 26, hh, mm, tzinfo=IST) + timedelta(days=day_offset_from_monday)  # 2026-10-26 is a Monday


# ---------- opening hours ----------
@pytest.mark.parametrize("spec,when,expected", [
    ("24/7", at(2, 3), True),
    ("Mo-Sa 09:00-21:00", at(0, 10), True),
    ("Mo-Sa 09:00-21:00", at(0, 22), False),
    ("Mo-Sa 09:00-21:00", at(6, 12), False),            # Sunday not listed
    ("Mo-Fr 09:00-13:00,16:00-21:00", at(1, 14), False),  # lunch break
    ("Mo-Fr 09:00-13:00,16:00-21:00", at(1, 17), True),
    ("09:00-18:00", at(5, 9, 30), True),                # no days = every day
    ("Mo-Su 09:00-21:00; Su off", at(6, 12), False),    # later rule overrides
    ("Mo-Su 09:00-21:00; Su off", at(5, 12), True),
    ("Mo-Sa 20:00-02:00", at(1, 1), True),              # overnight, from Monday night
    ("Mo-Sa 20:00-02:00", at(1, 3), False),
    ("Fr-Mo 10:00-12:00", at(6, 11), True),             # range wrapping the week
])
def test_opening_hours(spec, when, expected):
    assert is_open(spec, when) is expected


@pytest.mark.parametrize("spec", ["", "sunrise-sunset", "Mo-Fr 09:00-17:00; PH off", "Jan-Mar 09:00-17:00", "garbage", "Mo 25:00-26:00"])
def test_unsupported_hours_are_unknown_not_guessed(spec):
    assert is_open(spec, at(0, 12)) is None
    assert parse(spec) is None


# ---------- fixture map: one unlit road west->east at lat 22.25 ----------
ROAD = {"id": 1, "hw": "residential", "lit": "no", "sidewalk": "none", "name": "Test Road",
        "geom": [[22.25, 84.850], [22.25, 84.860]]}
SHOP = {"id": "n1", "kind": "shop", "name": "Corner Store", "lat": 22.2503, "lng": 84.855, "hours": "Mo-Su 09:00-21:00"}
POLICE = {"id": "n2", "kind": "police", "name": "Outpost", "lat": 22.2505, "lng": 84.853, "hours": ""}


def store(ways=(ROAD,), pois=(SHOP, POLICE)) -> OsmStore:
    return OsmStore(fetched_at="2026-10-26T00:00:00+00:00", ways=list(ways), pois=list(pois))


def route(points) -> CandidateRoute:
    return CandidateRoute(id="r", geometry=[LatLng(lat=a, lng=b) for a, b in points], duration_s=700, distance_m=1000)


def by_key(ev):
    return {i.key: i for i in ev.indicators}


def test_evidence_reads_tags_along_the_route():
    ev = build_evidence(route([(22.25, 84.850), (22.25, 84.860)]), store(), at(0, 14))
    k = by_key(ev)
    assert k["lighting"].value == 1.0 and k["lighting"].coverage > 0.95   # lit=no everywhere
    assert k["pedestrian"].value == 0.7                                     # sidewalk=none
    assert k["road_type"].value == 0.4                                      # residential heuristic
    assert 0 < k["open_places"].coverage < 0.5 and k["open_places"].value == 0.0  # shop open at 14:00
    assert ev.facilities_nearby == 1 and not ev.is_demo


def test_open_places_depends_on_time_of_day():
    r = route([(22.25, 84.850), (22.25, 84.860)])
    assert by_key(build_evidence(r, store(), at(0, 14)))["open_places"].value == 0.0
    assert by_key(build_evidence(r, store(), at(0, 23)))["open_places"].value == 0.7  # shop closed


def test_nothing_mapped_means_unknown_never_safe():
    far = route([(22.30, 84.90), (22.30, 84.91)])
    ev = build_evidence(far, store(), at(0, 14))
    assert all(i.value is None and i.coverage == 0 for i in ev.indicators)
    assert ev.facilities_nearby == 0
    a = assess([CandidateRoute(**{**far.model_dump(), "evidence": ev})]).assessments[0]
    assert a.risk is None and a.confidence_label == "low"


def test_untagged_lighting_is_unknown_even_where_road_is_mapped():
    plain = {**ROAD, "lit": ""}
    ev = build_evidence(route([(22.25, 84.850), (22.25, 84.860)]), store(ways=[plain]), at(0, 14))
    k = by_key(ev)
    assert k["lighting"].value is None and k["lighting"].coverage == 0
    assert k["road_type"].coverage > 0.95  # road class is still known


def test_unlit_route_scores_riskier_than_lit_route():
    lit = {**ROAD, "id": 2, "lit": "yes", "geom": [[22.26, 84.850], [22.26, 84.860]]}
    s = store(ways=[ROAD, lit])
    a = route([(22.25, 84.850), (22.25, 84.860)])
    b = route([(22.26, 84.850), (22.26, 84.860)])
    a.id, b.id = "unlit", "lit"
    a.evidence, b.evidence = build_evidence(a, s, at(0, 14)), build_evidence(b, s, at(0, 14))
    res = assess([a, b])
    assert res.recommended["safety_first"] == "lit"


# ---------- fetch / audit helpers ----------
RAW_WAYS = {"elements": [
    {"type": "way", "id": 1, "tags": {"highway": "residential", "lit": "yes", "sidewalk:both": "yes"},
     "geometry": [{"lat": 22.25, "lon": 84.85}, {"lat": 22.25, "lon": 84.86}]},
    {"type": "way", "id": 2, "tags": {"highway": "service"}, "geometry": [{"lat": 22.26, "lon": 84.85}, {"lat": 22.26, "lon": 84.86}]},
    {"type": "way", "id": 3, "tags": {"highway": "motorway"}, "geometry": [{"lat": 22.27, "lon": 84.85}, {"lat": 22.27, "lon": 84.86}]},
]}
RAW_POIS = {"elements": [
    {"type": "node", "id": 10, "lat": 22.25, "lon": 84.85, "tags": {"shop": "kiosk", "name": "K", "opening_hours": "Mo-Su 09:00-21:00"}},
    {"type": "way", "id": 11, "center": {"lat": 22.26, "lon": 84.85}, "tags": {"amenity": "pharmacy", "opening_hours": "PH off"}},
    {"type": "node", "id": 12, "lat": 22.27, "lon": 84.85, "tags": {"highway": "bus_stop"}},
]}


def test_convert_and_summarise_counts_what_is_actually_mapped():
    ways, pois = convert_ways(RAW_WAYS), convert_pois(RAW_POIS)
    assert [w["hw"] for w in ways] == ["residential", "service"]  # motorway excluded
    assert ways[0]["sidewalk"] == "both"
    assert {p["kind"] for p in pois} == {"shop", "pharmacy", "bus_stop"}
    s = summarise(ways, pois)
    assert s["lit_known_pct"] == pytest.approx(50.0, abs=1)  # equal-length ways, one tagged
    assert s["sidewalk_known_pct"] == pytest.approx(50.0, abs=1)
    assert s["with_hours"] == 2 and s["hours_parsable_pct"] == 50.0  # "PH off" cannot be read
    assert any("Lighting is known" in v for v in verdicts({**s, "lit_known_pct": 60}))
    assert any("UNKNOWN" in v for v in verdicts({**s, "lit_known_pct": 5}))


# ---------- API: real-routing path with a fake router and a tiny map file ----------
def test_alternatives_uses_osm_and_reports_unknowns(client, tmp_path, monkeypatch):
    from app.api import routes as api_routes
    from app.services.osm import store as store_mod

    f = tmp_path / "osm.json"
    f.write_text(json.dumps({"fetched_at": "2026-10-26T00:00:00+00:00", "ways": [ROAD], "pois": [SHOP, POLICE]}))
    monkeypatch.setattr(api_routes.settings, "osm_data_path", str(f))
    monkeypatch.setattr(api_routes.settings, "routing_url_walk", "http://fake")
    store_mod._cache.clear()

    async def fake(o, d, mode):
        a, b = route([(22.25, 84.850), (22.25, 84.860)]), route([(22.30, 84.90), (22.30, 84.91)])
        a.id, b.id = "on-map", "off-map"
        return [a, b]

    monkeypatch.setattr(api_routes, "candidate_routes", fake)
    body = {"origin": {"lat": 22.25, "lng": 84.85}, "destination": {"lat": 22.25, "lng": 84.86}, "mode": "walk"}
    j = client.post("/api/v1/routes/alternatives", json=body).json()
    assert j["routing_source"] == "osrm" and j["is_demo"] is False
    assert any("OpenStreetMap" in n for n in j["data_notes"])
    ass = {a["route_id"]: a for a in j["result"]["assessments"]}
    assert ass["on-map"]["risk"] is not None and ass["off-map"]["risk"] is None
    assert ass["off-map"]["confidence_label"] == "low"


def test_alternatives_without_map_file_says_so(client, tmp_path, monkeypatch):
    from app.api import routes as api_routes
    from app.services.osm import store as store_mod

    monkeypatch.setattr(api_routes.settings, "osm_data_path", str(tmp_path / "missing.json"))
    monkeypatch.setattr(api_routes.settings, "routing_url_walk", "http://fake")
    store_mod._cache.clear()

    async def fake(o, d, mode):
        return [route([(22.25, 84.850), (22.25, 84.860)])]

    monkeypatch.setattr(api_routes, "candidate_routes", fake)
    body = {"origin": {"lat": 22.25, "lng": 84.85}, "destination": {"lat": 22.25, "lng": 84.86}, "mode": "walk"}
    j = client.post("/api/v1/routes/alternatives", json=body).json()
    assert any("osm_fetch" in n for n in j["data_notes"])
    assert j["result"]["assessments"][0]["risk"] is None


def test_routing_outage_returns_503(client, monkeypatch):
    import httpx
    from app.api import routes as api_routes

    monkeypatch.setattr(api_routes.settings, "routing_url_walk", "http://fake")

    async def boom(o, d, mode):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(api_routes, "candidate_routes", boom)
    body = {"origin": {"lat": 22.25, "lng": 84.85}, "destination": {"lat": 22.26, "lng": 84.86}, "mode": "walk"}
    assert client.post("/api/v1/routes/alternatives", json=body).status_code == 503
