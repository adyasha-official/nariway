from app.schemas.routes import CandidateRoute, IndicatorValue, LatLng, NearbyReport, RouteEvidence
from app.services.safety.scoring import assess

PTS = [LatLng(lat=20.0, lng=85.0), LatLng(lat=20.01, lng=85.01)]


def route(id, t, d, light=None, cov=0.0, reports=()):
    ind = [IndicatorValue(key="lighting", label="Street lighting", value=light, coverage=cov)]
    return CandidateRoute(id=id, geometry=PTS, duration_s=t, distance_m=d,
                          evidence=RouteEvidence(indicators=ind, reports=list(reports)))


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_each_preference_picks_its_own_route():
    cands = [route("quick", 600, 3000, 0.7, 0.5), route("slow", 900, 3600, 0.1, 0.9)]
    rec = assess(cands).recommended
    assert rec["fastest"] == "quick" and rec["safety_first"] == "slow"


def test_unknown_is_not_rewarded_for_missing_data():
    result = assess([route("unknown", 600, 3000), route("evidenced", 600, 3000, 0.2, 0.9)])
    assert result.recommended["safety_first"] == "evidenced"
    u = next(a for a in result.assessments if a.route_id == "unknown")
    assert u.risk is None and u.confidence_label == "low"
    assert any("unknown, not as safe" in r for r in u.reasons)


def test_extreme_detour_never_offered_as_safer():
    cands = [route("quick", 600, 3000, 0.8, 0.8), route("huge", 3000, 9000, 0.0, 1.0)]
    r = assess(cands)
    assert r.recommended["safety_first"] == "quick"
    assert next(a for a in r.assessments if a.route_id == "huge").excluded_for_detour


def test_old_reports_decay():
    fresh = NearbyReport(id="a", category="harassment", age_days=1, distance_m=20)
    old = NearbyReport(id="b", category="harassment", age_days=400, distance_m=20)
    a = assess([route("r", 600, 3000, 0.2, 0.9, [fresh])]).assessments[0]
    b = assess([route("r", 600, 3000, 0.2, 0.9, [old])]).assessments[0]
    assert a.risk > b.risk and a.hazards and not b.hazards


def test_alternatives_demo_returns_three_labelled_routes(client):
    body = {"origin": {"lat": 22.26, "lng": 84.85}, "destination": {"lat": 22.28, "lng": 84.88}, "mode": "walk"}
    j = client.post("/api/v1/routes/alternatives", json=body).json()
    assert j["is_demo"] and len(j["routes"]) == 3
    assert set(j["result"]["recommended"]) == {"safety_first", "balanced", "fastest"}


def test_alternatives_rejects_same_point_and_bad_coords(client):
    p = {"lat": 22.26, "lng": 84.85}
    assert client.post("/api/v1/routes/alternatives", json={"origin": p, "destination": p}).status_code == 422
    bad = {"origin": {"lat": 999, "lng": 0}, "destination": p}
    assert client.post("/api/v1/routes/alternatives", json=bad).status_code == 422


def test_places_search_demo(client):
    assert any("NIT" in p["name"] for p in client.get("/api/v1/places/search", params={"q": "nit"}).json())
    assert client.get("/api/v1/places/search", params={"q": "a"}).status_code == 422


def test_demo_gives_three_distinct_picks(client):
    body = {"origin": {"lat": 22.2536, "lng": 84.9006}, "destination": {"lat": 22.229, "lng": 84.864}}
    rec = client.post("/api/v1/routes/alternatives", json=body).json()["result"]["recommended"]
    assert len(set(rec.values())) == 3
