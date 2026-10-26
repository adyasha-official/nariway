from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import current_user
from app.db import get_db, utcnow
from app.models import ReportFlag, SafetyReport, User
from app.services.reports.policy import CATEGORIES, check_description, is_duplicate, visible_filters

router = APIRouter(prefix="/api/v1/safety", tags=["safety"])


class ReportIn(BaseModel):
    category: str
    description: str = Field(default="", max_length=280)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    occurred_at: datetime | None = None

    @field_validator("category")
    @classmethod
    def _cat(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(CATEGORIES)}")
        return v


class ReportOut(BaseModel):
    id: int
    category: str
    description: str
    lat: float
    lng: float
    occurred_at: datetime
    expires_at: datetime
    status: str
    is_demo: bool


class FlagIn(BaseModel):
    reason: str = Field(pattern="^(inaccurate|abusive|identifies_person|other)$")


@router.get("/categories")
def categories() -> list[str]:
    return list(CATEGORIES)


@router.post("/reports", response_model=ReportOut, status_code=201)
def submit(body: ReportIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> SafetyReport:
    problem = check_description(body.description)
    if problem:
        raise HTTPException(422, problem)
    now = utcnow()
    when = body.occurred_at or now
    if when.tzinfo is None:
        raise HTTPException(422, "occurred_at must include a timezone.")
    if when > now + timedelta(minutes=5) or when < now - timedelta(days=30):
        raise HTTPException(422, "The time must be within the last 30 days and not in the future.")
    todays = db.scalar(
        select(func.count()).select_from(SafetyReport).where(
            SafetyReport.user_id == user.id, SafetyReport.submitted_at > now - timedelta(days=1)
        )
    )
    if todays >= settings.reports_per_user_per_day:
        raise HTTPException(429, "Daily report limit reached. Please try again tomorrow.")
    if is_duplicate(db, body.category, body.lat, body.lng):
        raise HTTPException(409, "A similar report was already made here recently.")
    rep = SafetyReport(
        user_id=user.id, category=body.category, description=body.description.strip(),
        lat=body.lat, lng=body.lng, occurred_at=when,
        expires_at=now + timedelta(days=settings.report_ttl_days),
    )
    db.add(rep)
    db.commit()
    return rep


@router.get("/reports", response_model=list[ReportOut])
def list_reports(
    min_lat: float = Query(ge=-90, le=90), max_lat: float = Query(ge=-90, le=90),
    min_lng: float = Query(ge=-180, le=180), max_lng: float = Query(ge=-180, le=180),
    db: Session = Depends(get_db),
) -> list[SafetyReport]:
    """Public: approved, unexpired reports in a bounding box. No reporter details."""
    if max_lat - min_lat > 0.5 or max_lng - min_lng > 0.5:
        raise HTTPException(422, "Please zoom in: the area is too large.")
    return list(db.scalars(
        select(SafetyReport).where(
            *visible_filters(), SafetyReport.lat.between(min_lat, max_lat),
            SafetyReport.lng.between(min_lng, max_lng),
        ).limit(500)
    ))


@router.get("/reports/mine", response_model=list[ReportOut])
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[SafetyReport]:
    return list(db.scalars(
        select(SafetyReport).where(SafetyReport.user_id == user.id).order_by(SafetyReport.submitted_at.desc())
    ))


@router.post("/reports/{report_id}/flag", status_code=204)
def flag(report_id: int, body: FlagIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    rep = db.get(SafetyReport, report_id)
    if rep is None or rep.status != "approved":
        raise HTTPException(404, "Report not found.")
    if rep.user_id == user.id:
        raise HTTPException(422, "You cannot flag your own report.")
    if db.scalar(select(ReportFlag).where(ReportFlag.report_id == rep.id, ReportFlag.user_id == user.id)):
        raise HTTPException(409, "You already flagged this report.")
    db.add(ReportFlag(report_id=rep.id, user_id=user.id, reason=body.reason))
    db.flush()
    n = db.scalar(select(func.count()).select_from(ReportFlag).where(ReportFlag.report_id == rep.id))
    if n >= settings.flags_to_auto_hide:
        rep.status = "hidden"  # pulled from routing until a moderator reviews it
    db.commit()
