from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import utcnow
from app.models import SafetyReport
from app.schemas.routes import CandidateRoute, NearbyReport, RouteEvidence
from app.services.reports.policy import visible_filters
from app.services.safety.geometry import point_polyline_distance_m
from app.schemas.routes import LatLng

RADIUS_M = 150.0


def attach_reports(db: Session, routes: list[CandidateRoute]) -> None:
    """Add approved, unexpired community reports to each route's evidence (in place)."""
    pts = [p for r in routes for p in r.geometry]
    pad = 0.0015
    rows = list(
        db.scalars(
            select(SafetyReport).where(
                *visible_filters(),
                SafetyReport.lat.between(min(p.lat for p in pts) - pad, max(p.lat for p in pts) + pad),
                SafetyReport.lng.between(min(p.lng for p in pts) - pad, max(p.lng for p in pts) + pad),
            )
        )
    )
    now = utcnow()
    for r in routes:
        found = []
        for rep in rows:
            d = point_polyline_distance_m(LatLng(lat=rep.lat, lng=rep.lng), r.geometry)
            if d <= RADIUS_M:
                found.append(
                    NearbyReport(
                        id=str(rep.id), category=rep.category, distance_m=d, is_demo=rep.is_demo,
                        age_days=max(0.0, (now - rep.occurred_at).total_seconds() / 86400),
                    )
                )
        if r.evidence is None:
            r.evidence = RouteEvidence(indicators=[])
        r.evidence.reports = r.evidence.reports + found
