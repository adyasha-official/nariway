from datetime import datetime, timedelta, timezone

from tests.conftest import signup

A = {"lat": 22.2536, "lng": 84.9006}
B = {"lat": 22.229, "lng": 84.864}


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def report(client, auth, **kw):
    body = {"category": "poor_lighting", "description": "Street lamps are out near the gate.", **A, **kw}
    return client.post("/api/v1/safety/reports", json=body, headers=auth)


# ---------- auth ----------
def test_register_login_and_me(client):
    h = signup(client)
    assert client.get("/api/v1/auth/me", headers=h).json()["email"] == "a@example.com"
    assert client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "correct-horse"}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong-password"}).status_code == 401


def test_duplicate_email_and_weak_password(client):
    signup(client)
    r = client.post("/api/v1/auth/register", json={"email": "A@example.com", "password": "correct-horse", "display_name": "x"})
    assert r.status_code == 409
    r = client.post("/api/v1/auth/register", json={"email": "b@example.com", "password": "short", "display_name": "x"})
    assert r.status_code == 422


def test_login_is_rate_limited(client):
    codes = [client.post("/api/v1/auth/login", json={"email": "z@example.com", "password": "whatever123"}).status_code
             for _ in range(12)]
    assert codes[-1] == 429


def test_protected_endpoints_need_a_valid_token(client):
    assert client.get("/api/v1/trips").status_code == 401
    assert client.get("/api/v1/trips", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get("/api/v1/admin/stats").status_code == 401


def test_regular_user_cannot_use_admin(client, auth):
    assert client.get("/api/v1/admin/reports", headers=auth).status_code == 403


# ---------- reports ----------
def test_pending_report_is_not_public_and_does_not_affect_routes(client, auth):
    assert report(client, auth).status_code == 201
    box = {"min_lat": 22.2, "max_lat": 22.3, "min_lng": 84.8, "max_lng": 84.95}
    assert client.get("/api/v1/safety/reports", params=box).json() == []
    assert len(client.get("/api/v1/safety/reports/mine", headers=auth).json()) == 1


def test_report_rejects_personal_details(client, auth):
    for text in ("call me on 98765 43210", "mail x@y.com", "see http://bad.example", "plate OD 14 AB 1234 followed me"):
        r = report(client, auth, description=text)
        assert r.status_code == 422, text


def test_report_validation(client, auth):
    assert report(client, auth, category="nonsense").status_code == 422
    assert report(client, auth, lat=999).status_code == 422
    future = iso(datetime.now(timezone.utc) + timedelta(days=2))
    assert report(client, auth, occurred_at=future).status_code == 422
    assert report(client, auth, description="x" * 281).status_code == 422


def test_duplicates_and_daily_limit(client, auth):
    assert report(client, auth).status_code == 201
    assert report(client, auth).status_code == 409  # same place + category
    for i in range(4):
        assert report(client, auth, category="isolated", lat=22.30 + i * 0.01).status_code == 201
    assert report(client, auth, category="other", lat=22.5).status_code == 429


def test_moderation_flow_and_audit(client, auth, admin):
    rid = report(client, auth).json()["id"]
    q = client.get("/api/v1/admin/reports", headers=admin).json()
    assert [r["id"] for r in q] == [rid]
    assert client.post(f"/api/v1/admin/reports/{rid}/moderate", json={"action": "approve", "note": "ok"}, headers=auth).status_code == 403
    assert client.post(f"/api/v1/admin/reports/{rid}/moderate", json={"action": "approve", "note": "ok"}, headers=admin).status_code == 200
    box = {"min_lat": 22.2, "max_lat": 22.3, "min_lng": 84.8, "max_lng": 84.95}
    pub = client.get("/api/v1/safety/reports", params=box).json()
    assert len(pub) == 1 and "user_id" not in pub[0]
    assert client.get("/api/v1/admin/audit", headers=admin).json()[0]["action"] == "report.approve"


def test_approved_report_changes_route_evidence_and_unknown_stays_unknown(client, auth, admin):
    """Real reports reach the scorer; an unreported route is never rewarded."""
    rid = report(client, auth).json()["id"]
    client.post(f"/api/v1/admin/reports/{rid}/moderate", json={"action": "approve"}, headers=admin)
    body = {"origin": A, "destination": B, "mode": "walk"}
    j = client.post("/api/v1/routes/alternatives", json=body).json()
    nearby = [a for a in j["result"]["assessments"] if any("report" in h for h in a["hazards"])]
    assert nearby, "approved report should surface as a hazard on a route passing it"


def test_flags_auto_hide_and_one_flag_per_user(client, auth, admin):
    rid = report(client, auth).json()["id"]
    client.post(f"/api/v1/admin/reports/{rid}/moderate", json={"action": "approve"}, headers=admin)
    users = [signup(client, f"u{i}@example.com") for i in range(3)]
    assert client.post(f"/api/v1/safety/reports/{rid}/flag", json={"reason": "inaccurate"}, headers=users[0]).status_code == 204
    assert client.post(f"/api/v1/safety/reports/{rid}/flag", json={"reason": "inaccurate"}, headers=users[0]).status_code == 409
    assert client.post(f"/api/v1/safety/reports/{rid}/flag", json={"reason": "abusive"}, headers=auth).status_code == 422  # own report
    client.post(f"/api/v1/safety/reports/{rid}/flag", json={"reason": "abusive"}, headers=users[1])
    client.post(f"/api/v1/safety/reports/{rid}/flag", json={"reason": "other"}, headers=users[2])
    box = {"min_lat": 22.2, "max_lat": 22.3, "min_lng": 84.8, "max_lng": 84.95}
    assert client.get("/api/v1/safety/reports", params=box).json() == []
    assert [r["id"] for r in client.get("/api/v1/admin/reports?status=hidden", headers=admin).json()] == [rid]


def test_expired_reports_are_not_public(client, auth, admin):
    from app.models import SafetyReport
    rid = report(client, auth).json()["id"]
    client.post(f"/api/v1/admin/reports/{rid}/moderate", json={"action": "approve"}, headers=admin)
    with client.session_factory() as db:
        db.get(SafetyReport, rid).expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
    box = {"min_lat": 22.2, "max_lat": 22.3, "min_lng": 84.8, "max_lng": 84.95}
    assert client.get("/api/v1/safety/reports", params=box).json() == []


def test_bbox_too_large_rejected(client):
    r = client.get("/api/v1/safety/reports", params={"min_lat": 0, "max_lat": 20, "min_lng": 0, "max_lng": 20})
    assert r.status_code == 422


# ---------- journeys ----------
def new_trip(client, h, minutes=30):
    body = {"origin_name": "NIT", "dest_name": "Station", "dest_lat": B["lat"], "dest_lng": B["lng"],
            "preference": "balanced", "expected_arrival": iso(datetime.now(timezone.utc) + timedelta(minutes=minutes))}
    return client.post("/api/v1/trips", json=body, headers=h)


def test_contact_requires_consent(client, auth):
    body = {"name": "Mum", "contact_reference": "+919999999999", "consent_confirmed": False}
    assert client.post("/api/v1/contacts", json=body, headers=auth).status_code == 422
    body["consent_confirmed"] = True
    assert client.post("/api/v1/contacts", json=body, headers=auth).status_code == 201


def test_share_link_lifecycle(client, auth):
    tid = new_trip(client, auth).json()["id"]
    share = client.post(f"/api/v1/trips/{tid}/share", json={}, headers=auth).json()
    token = share["url"].rsplit("/", 1)[1]
    assert len(token) >= 40

    view = client.get(f"/api/v1/shared/{token}")
    assert view.status_code == 200
    v = view.json()
    assert v["traveller"] == "Asha" and v["state"] == "on_the_way"
    assert "email" not in v and "origin_name" not in v  # minimal disclosure

    client.post(f"/api/v1/trips/{tid}/check-in", json={"lat": 22.24, "lng": 84.88}, headers=auth)
    assert client.get(f"/api/v1/shared/{token}").json()["last_lat"] == 22.24

    # the raw token is never stored
    from app.models import TripShare
    with client.session_factory() as db:
        assert all(token not in s.token_hash for s in db.query(TripShare))

    assert client.delete(f"/api/v1/trips/{tid}/shares/{share['share_id']}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/shared/{token}").status_code == 404


def test_ending_trip_kills_links_and_clears_location(client, auth):
    tid = new_trip(client, auth).json()["id"]
    token = client.post(f"/api/v1/trips/{tid}/share", json={}, headers=auth).json()["url"].rsplit("/", 1)[1]
    client.post(f"/api/v1/trips/{tid}/check-in", json={"lat": 22.24, "lng": 84.88}, headers=auth)
    assert client.post(f"/api/v1/trips/{tid}/end", headers=auth).json()["state"] == "ended"
    assert client.get(f"/api/v1/shared/{token}").status_code == 404
    assert client.post(f"/api/v1/trips/{tid}/check-in", json={}, headers=auth).status_code == 409


def test_other_users_cannot_touch_my_trip(client, auth):
    tid = new_trip(client, auth).json()["id"]
    other = signup(client, "o@example.com", "Other")
    for method, url in (("post", f"/api/v1/trips/{tid}/share"), ("post", f"/api/v1/trips/{tid}/end"),
                        ("post", f"/api/v1/trips/{tid}/check-in"), ("get", f"/api/v1/trips/{tid}/shares")):
        assert getattr(client, method)(url, headers=other, **({"json": {}} if method == "post" else {})).status_code == 404


def test_guessed_tokens_get_404(client):
    assert client.get("/api/v1/shared/not-a-real-token").status_code == 404


def test_overdue_state(client, auth):
    from app.models import Trip
    tid = new_trip(client, auth).json()["id"]
    with client.session_factory() as db:
        db.get(Trip, tid).expected_arrival = datetime.now(timezone.utc) - timedelta(minutes=30)
        db.commit()
    assert client.get("/api/v1/trips", headers=auth).json()[0]["state"] == "overdue"


def test_trip_eta_must_be_near_future(client, auth):
    assert new_trip(client, auth, minutes=-5).status_code == 422
    assert new_trip(client, auth, minutes=60 * 48).status_code == 422


def test_account_deletion_erases_trips_and_anonymises_reports(client, auth, admin):
    tid = new_trip(client, auth).json()["id"]
    token = client.post(f"/api/v1/trips/{tid}/share", json={}, headers=auth).json()["url"].rsplit("/", 1)[1]
    rid = report(client, auth).json()["id"]
    client.post(f"/api/v1/admin/reports/{rid}/moderate", json={"action": "approve"}, headers=admin)
    assert client.delete("/api/v1/auth/me", headers=auth).status_code == 204
    assert client.get(f"/api/v1/shared/{token}").status_code == 404
    from app.models import SafetyReport, Trip, User
    with client.session_factory() as db:
        assert db.query(Trip).count() == 0 and db.get(SafetyReport, rid).user_id is None
        assert db.query(User).filter_by(email="a@example.com").count() == 0
