"""Rules for what a community report may contain. Observations about places, never about people."""

import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import utcnow
from app.models import SafetyReport
from app.services.safety.geometry import haversine_m
from app.schemas.routes import LatLng

CATEGORIES = ("poor_lighting", "isolated", "harassment", "unsafe_crossing", "obstruction", "other")

_PII = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email addresses"),
    (re.compile(r"(?:\d[\s-]?){6,}"), "phone numbers or long numbers (including vehicle plates)"),
    (re.compile(r"\b[A-Za-z]{2}[\s-]?\d{1,2}[\s-]?[A-Za-z]{1,3}[\s-]?\d{3,4}\b"), "vehicle registration numbers"),
    (re.compile(r"https?://|www\.", re.I), "links"),
]


def check_description(text: str) -> str | None:
    """Return a user-facing problem, or None if the text is acceptable."""
    for rx, what in _PII:
        if rx.search(text):
            return f"Please remove {what}. Reports describe places, not people."
    return None


def visible_filters(now: datetime | None = None):
    now = now or utcnow()
    return (SafetyReport.status == "approved", SafetyReport.expires_at > now)


def is_duplicate(db: Session, category: str, lat: float, lng: float) -> bool:
    since = utcnow() - timedelta(hours=24)
    pad = settings.duplicate_radius_m / 111_000 * 1.5
    rows = db.scalars(
        select(SafetyReport).where(
            SafetyReport.category == category,
            SafetyReport.submitted_at > since,
            SafetyReport.status.in_(("pending", "approved")),
            SafetyReport.lat.between(lat - pad, lat + pad),
            SafetyReport.lng.between(lng - pad, lng + pad),
        )
    )
    here = LatLng(lat=lat, lng=lng)
    return any(haversine_m(here, LatLng(lat=r.lat, lng=r.lng)) <= settings.duplicate_radius_m for r in rows)
