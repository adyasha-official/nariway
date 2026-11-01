import asyncio

import httpx

from app.schemas.routes import LatLng
from app.services.routing import osrm
from app.services.safety.geometry import overlap_fraction

O = LatLng(lat=22.2536, lng=84.9006)
D = LatLng(lat=22.2290, lng=84.8640)


def line(points, secs, metres):
    return {"duration": secs, "distance": metres, "geometry": {"coordinates": [[lng, lat] for lat, lng in points]}}


def handler(request: httpx.Request) -> httpx.Response:
    """Fake OSRM: direct request returns one route (+ a near-copy); via requests return a detour each side."""
    coords = request.url.path.rsplit("/", 1)[1].split(";")
    direct = [(O.lat, O.lng), (22.241, 84.882), (D.lat, D.lng)]
    if len(coords) == 2:
        near_copy = [(a + 0.00005, b + 0.00005) for a, b in direct]
        return httpx.Response(200, json={"code": "Ok", "routes": [line(direct, 900, 4800), line(near_copy, 905, 4810)]})
    vlng, vlat = map(float, coords[1].split(","))
    return httpx.Response(200, json={"code": "Ok", "routes": [line([(O.lat, O.lng), (vlat, vlng), (D.lat, D.lng)], 1100, 5600)]})


def run(transport=None):
    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport or handler)) as c:
            return await osrm.candidate_routes(O, D, "walk", client=c)
    return asyncio.run(go())


def test_via_points_are_on_opposite_sides_of_the_line():
    a, b = osrm.via_points(O, D)
    mid_lat, mid_lng = (O.lat + D.lat) / 2, (O.lng + D.lng) / 2
    assert abs((a.lat + b.lat) / 2 - mid_lat) < 1e-9 and abs((a.lng + b.lng) / 2 - mid_lng) < 1e-9
    assert a != b


def test_near_duplicates_dropped_and_diverse_routes_added(monkeypatch):
    monkeypatch.setattr(osrm.settings, "routing_provider_url", "http://osrm.test")
    routes = run()
    assert len(routes) == 3  # direct + two via detours; the near-copy is gone
    assert [r.id for r in routes] == ["route-1", "route-2", "route-3"]
    assert routes[0].duration_s == 900
    for i, a in enumerate(routes):
        for b in routes[i + 1:]:
            assert overlap_fraction(a.geometry, b.geometry) < 0.9


def test_much_slower_routes_are_discarded(monkeypatch):
    monkeypatch.setattr(osrm.settings, "routing_provider_url", "http://osrm.test")

    def slow_via(request):
        coords = request.url.path.rsplit("/", 1)[1].split(";")
        if len(coords) == 2:
            return handler(request)
        vlng, vlat = map(float, coords[1].split(","))
        return httpx.Response(200, json={"code": "Ok", "routes": [line([(O.lat, O.lng), (vlat, vlng), (D.lat, D.lng)], 5000, 20000)]})

    routes = run(slow_via)
    assert len(routes) == 1  # 5000 s > 1.6 x 900 s, so the detours are not offered


def test_failed_via_requests_do_not_break_direct_routes(monkeypatch):
    monkeypatch.setattr(osrm.settings, "routing_provider_url", "http://osrm.test")

    def flaky(request):
        if len(request.url.path.rsplit("/", 1)[1].split(";")) == 3:
            return httpx.Response(500)
        return handler(request)

    assert len(run(flaky)) == 1


def test_per_mode_url_falls_back_to_default(monkeypatch):
    monkeypatch.setattr(osrm.settings, "routing_provider_url", "http://default")
    monkeypatch.setattr(osrm.settings, "routing_url_walk", "http://foot")
    assert osrm.base_url_for("walk") == "http://foot"
    assert osrm.base_url_for("cab") == "http://default"
