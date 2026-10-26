from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import admin_user
from app.db import get_db, utcnow
from app.models import AuditEvent, SafetyReport, User
from app.api.safety import ReportOut

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class AdminReport(ReportOut):
    flag_count: int
    flag_reasons: list[str]


class ModerateIn(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    note: str = Field(default="", max_length=300)


def _view(r: SafetyReport) -> AdminReport:
    base = ReportOut.model_validate(r, from_attributes=True).model_dump()
    return AdminReport(**base, flag_count=len(r.flags), flag_reasons=[f.reason for f in r.flags])


@router.get("/reports", response_model=list[AdminReport])
def queue(
    status: str = Query("pending", pattern="^(pending|approved|rejected|hidden)$"),
    _: User = Depends(admin_user), db: Session = Depends(get_db),
) -> list[AdminReport]:
    rows = db.scalars(select(SafetyReport).where(SafetyReport.status == status).order_by(SafetyReport.submitted_at).limit(200))
    return [_view(r) for r in rows]


@router.post("/reports/{report_id}/moderate", response_model=AdminReport)
def moderate(report_id: int, body: ModerateIn, admin: User = Depends(admin_user), db: Session = Depends(get_db)) -> AdminReport:
    rep = db.get(SafetyReport, report_id)
    if rep is None:
        raise HTTPException(404, "Report not found.")
    rep.status = "approved" if body.action == "approve" else "rejected"
    db.add(AuditEvent(actor_id=admin.id, action=f"report.{body.action}", target=f"report:{rep.id}", detail=body.note))
    db.commit()
    return _view(rep)


@router.get("/stats")
def stats(_: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    by_status = dict(db.execute(select(SafetyReport.status, func.count()).group_by(SafetyReport.status)).all())
    expired = db.scalar(select(func.count()).select_from(SafetyReport).where(
        SafetyReport.status == "approved", SafetyReport.expires_at <= utcnow())) or 0
    return {
        "reports_by_status": by_status, "approved_but_expired": expired,
        "users": db.scalar(select(func.count()).select_from(User)),
        "sample_reports": db.scalar(select(func.count()).select_from(SafetyReport).where(SafetyReport.is_demo)),
    }


@router.get("/audit")
def audit(_: User = Depends(admin_user), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(AuditEvent).order_by(AuditEvent.at.desc()).limit(100))
    return [{"at": e.at, "action": e.action, "target": e.target, "note": e.detail} for e in rows]
