from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.services.osm.evidence import attach_osm_evidence
from app.services.osm.store import get_store
from app.services.reports.near import attach_reports
from app.schemas.routes import (
    AlternativesRequest, AlternativesResponse, AssessRequest, AssessResponse,
)
from app.services.routing.demo import demo_routes
from app.services.routing.osrm import base_url_for, candidate_routes
from app.services.safety.geometry import haversine_m
from app.services.safety.scoring import assess

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])

LOW_COVERAGE = 0.4
LOW_DATA_NOTE = (
    "Very little safety data is mapped for this trip: lighting, footpaths and opening hours are mostly unknown. "
    "Routes differ mainly by road type and community reports, so treat the Safest and Balanced labels as weak guidance."
)


@router.post("/assess", response_model=AssessResponse)
def assess_routes(body: AssessRequest) -> AssessResponse:
    return assess(body.candidates)


@router.post("/alternatives", response_model=AlternativesResponse)
async def alternatives(body: AlternativesRequest, db: Session = Depends(get_db)) -> AlternativesResponse:
    if haversine_m(body.origin, body.destination) < 30:
        raise HTTPException(422, "Origin and destination are too close together.")
    notes: list[str] = []
    if base_url_for(body.mode):
        try:
            routes = await candidate_routes(body.origin, body.destination, body.mode)
        except httpx.HTTPError:
            raise HTTPException(503, "Routing service is unavailable. Please try again shortly.")
        if not routes:
            raise HTTPException(404, "No route found. Both points need to be near a road or path inside the covered area.")
        source = "osrm"
        store = get_store(settings.osm_data_path)
        if store:
            attach_osm_evidence(routes, store, body.depart_at or datetime.now(timezone.utc))
            notes.append(f"Map data from OpenStreetMap, fetched {store.fetched_at[:10]}. Missing tags are shown as unknown.")
        else:
            notes.append("No local map data found, so safety evidence is limited to community reports. "
                         "Run `python -m app.osm_fetch` to download it.")
    else:
        routes, source = demo_routes(body.origin, body.destination, body.mode), "demo"
    attach_reports(db, routes)
    result = assess(routes)
    if source != "demo" and max(a.evidence_coverage for a in result.assessments) < LOW_COVERAGE:
        notes.append(LOW_DATA_NOTE)
    return AlternativesResponse(
        is_demo=source == "demo",
        routing_source=source,
        pilot_city=settings.pilot_city,
        depart_at=body.depart_at or datetime.now(timezone.utc),
        routes=routes,
        data_notes=notes,
        result=result,
    )
