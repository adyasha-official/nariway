from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db
from app.services.reports.near import attach_reports
from app.schemas.routes import (
    AlternativesRequest, AlternativesResponse, AssessRequest, AssessResponse,
)
from app.services.routing.demo import demo_routes
from app.services.routing.osrm import osrm_routes
from app.services.safety.geometry import dedupe_similar, haversine_m
from app.services.safety.scoring import assess

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])


@router.post("/assess", response_model=AssessResponse)
def assess_routes(body: AssessRequest) -> AssessResponse:
    return assess(body.candidates)


@router.post("/alternatives", response_model=AlternativesResponse)
async def alternatives(body: AlternativesRequest, db: Session = Depends(get_db)) -> AlternativesResponse:
    if haversine_m(body.origin, body.destination) < 30:
        raise HTTPException(422, "Origin and destination are too close together.")
    if settings.routing_provider_url:
        try:
            routes = dedupe_similar(
                await osrm_routes(settings.routing_provider_url, body.origin, body.destination, body.mode)
            )
        except httpx.HTTPError:
            raise HTTPException(503, "Routing service is unavailable. Please try again shortly.")
        if not routes:
            raise HTTPException(404, "No route found between these points.")
        source = "osrm"
    else:
        routes, source = demo_routes(body.origin, body.destination, body.mode), "demo"
    attach_reports(db, routes)
    return AlternativesResponse(
        is_demo=source == "demo",
        routing_source=source,
        pilot_city=settings.pilot_city,
        depart_at=body.depart_at or datetime.now(timezone.utc),
        routes=routes,
        result=assess(routes),
    )
