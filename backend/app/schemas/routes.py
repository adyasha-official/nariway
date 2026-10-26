from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


Preference = Literal["safety_first", "balanced", "fastest"]
TravelMode = Literal["walk", "bike", "cab"]


class IndicatorValue(BaseModel):
    """One piece of evidence. value=None means UNKNOWN, which is never the same as safe."""

    key: str
    label: str
    value: float | None = Field(default=None, ge=0, le=1, description="0 = no concern, 1 = high concern")
    coverage: float = Field(default=0.0, ge=0, le=1, description="Share of the route this evidence actually covers")
    source: str = "unknown"
    note: str = ""


class NearbyReport(BaseModel):
    id: str
    category: str
    age_days: float = Field(ge=0)
    distance_m: float = Field(ge=0)
    is_demo: bool = False


class RouteEvidence(BaseModel):
    indicators: list[IndicatorValue]
    reports: list[NearbyReport] = []
    facilities_nearby: int = 0
    is_demo: bool = False


class CandidateRoute(BaseModel):
    id: str
    geometry: list[LatLng] = Field(min_length=2)
    duration_s: float = Field(gt=0)
    distance_m: float = Field(gt=0)
    evidence: RouteEvidence | None = None


class AlternativesRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    mode: TravelMode = "walk"
    depart_at: datetime | None = Field(default=None, description="Timezone-aware. Defaults to now. Drives time-of-day evidence.")


class RouteAssessment(BaseModel):
    route_id: str
    rank: int
    cost: float
    risk: float | None = Field(description="None when there is no usable evidence. Not the same as safe.")
    uncertainty: float = Field(ge=0, le=1)
    evidence_coverage: float = Field(ge=0, le=1)
    confidence_label: Literal["low", "medium", "higher"]
    labels: list[Preference] = Field(description="Which preferences this route is the pick for")
    excluded_for_detour: bool = False
    reasons: list[str]
    hazards: list[str]
    indicators: list[IndicatorValue]


class AssessResponse(BaseModel):
    model_version: str
    disclaimer: str
    is_demo: bool
    recommended: dict[Preference, str]
    assessments: list[RouteAssessment]


class AlternativesResponse(BaseModel):
    is_demo: bool
    routing_source: str
    pilot_city: str
    depart_at: datetime
    routes: list[CandidateRoute]
    result: AssessResponse


class AssessRequest(BaseModel):
    candidates: list[CandidateRoute] = Field(min_length=1, max_length=8)
    depart_at: datetime | None = None
