from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limit
from app.core.security import current_user, hash_token, new_share_token
from app.db import get_db, utcnow
from app.models import Trip, TripShare, TrustedContact, User

router = APIRouter(prefix="/api/v1", tags=["journeys"])
MAX_ACTIVE_TRIPS = 3
MAX_SHARES_PER_TRIP = 5


# ---------- contacts ----------
class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    contact_reference: str = Field(min_length=3, max_length=80, description="Phone or email, only used to open a message app")
    consent_confirmed: bool


class ContactOut(BaseModel):
    id: int
    name: str
    contact_reference: str
    consent_confirmed: bool


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[TrustedContact]:
    return list(db.scalars(select(TrustedContact).where(TrustedContact.user_id == user.id)))


@router.post("/contacts", response_model=ContactOut, status_code=201)
def add_contact(body: ContactIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TrustedContact:
    if not body.consent_confirmed:
        raise HTTPException(422, "Please confirm this person has agreed to be your trusted contact.")
    if db.scalar(select(func.count()).select_from(TrustedContact).where(TrustedContact.user_id == user.id)) >= 10:
        raise HTTPException(422, "You can save up to 10 trusted contacts.")
    c = TrustedContact(user_id=user.id, **body.model_dump())
    db.add(c)
    db.commit()
    return c


@router.delete("/contacts/{contact_id}", status_code=204)
def remove_contact(contact_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    c = db.get(TrustedContact, contact_id)
    if c is None or c.user_id != user.id:
        raise HTTPException(404, "Contact not found.")
    db.delete(c)
    db.commit()


# ---------- trips ----------
class TripIn(BaseModel):
    origin_name: str = Field(max_length=120)
    dest_name: str = Field(max_length=120)
    dest_lat: float = Field(ge=-90, le=90)
    dest_lng: float = Field(ge=-180, le=180)
    preference: str = Field(pattern="^(safety_first|balanced|fastest)$")
    expected_arrival: datetime


class TripOut(BaseModel):
    id: int
    origin_name: str
    dest_name: str
    preference: str
    started_at: datetime
    expected_arrival: datetime
    state: str  # on_the_way | overdue | ended
    last_checkin_at: datetime | None


class CheckIn(BaseModel):
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    expected_arrival: datetime | None = None


def trip_state(t: Trip) -> str:
    if t.status == "ended":
        return "ended"
    if utcnow() > t.expected_arrival + timedelta(minutes=settings.overdue_grace_minutes):
        return "overdue"
    return "on_the_way"


def _out(t: Trip) -> TripOut:
    return TripOut(**{k: getattr(t, k) for k in (
        "id", "origin_name", "dest_name", "preference", "started_at", "expected_arrival", "last_checkin_at")},
        state=trip_state(t))


def _own_trip(db: Session, user: User, trip_id: int) -> Trip:
    t = db.get(Trip, trip_id)
    if t is None or t.user_id != user.id:
        raise HTTPException(404, "Journey not found.")
    return t


def _check_eta(eta: datetime) -> None:
    if eta.tzinfo is None:
        raise HTTPException(422, "expected_arrival must include a timezone.")
    if not utcnow() < eta <= utcnow() + timedelta(hours=24):
        raise HTTPException(422, "Expected arrival must be within the next 24 hours.")


@router.post("/trips", response_model=TripOut, status_code=201)
def create_trip(body: TripIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TripOut:
    _check_eta(body.expected_arrival)
    active = db.scalar(select(func.count()).select_from(Trip).where(Trip.user_id == user.id, Trip.status == "active"))
    if active >= MAX_ACTIVE_TRIPS:
        raise HTTPException(422, "End one of your active journeys before starting another.")
    t = Trip(user_id=user.id, **body.model_dump())
    db.add(t)
    db.commit()
    return _out(t)


@router.get("/trips", response_model=list[TripOut])
def my_trips(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[TripOut]:
    rows = db.scalars(select(Trip).where(Trip.user_id == user.id).order_by(Trip.started_at.desc()).limit(20))
    return [_out(t) for t in rows]


@router.post("/trips/{trip_id}/check-in", response_model=TripOut)
def check_in(trip_id: int, body: CheckIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TripOut:
    t = _own_trip(db, user, trip_id)
    if t.status != "active":
        raise HTTPException(409, "This journey has ended.")
    if (body.lat is None) != (body.lng is None):
        raise HTTPException(422, "Send both lat and lng, or neither.")
    t.last_checkin_at, t.last_lat, t.last_lng = utcnow(), body.lat, body.lng
    if body.expected_arrival:
        _check_eta(body.expected_arrival)
        t.expected_arrival = body.expected_arrival
    db.commit()
    return _out(t)


@router.post("/trips/{trip_id}/end", response_model=TripOut)
def end_trip(trip_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> TripOut:
    t = _own_trip(db, user, trip_id)
    t.status, t.ended_at = "ended", utcnow()
    for s in t.shares:
        if s.revoked_at is None:
            s.revoked_at = utcnow()
    t.last_lat = t.last_lng = None  # drop precise location once the journey is over
    db.commit()
    return _out(t)


# ---------- sharing ----------
class ShareIn(BaseModel):
    contact_id: int | None = None
    hours: int = Field(default=settings.share_default_hours, ge=1, le=24)


class ShareCreated(BaseModel):
    share_id: int
    url: str
    expires_at: datetime
    contact_name: str | None


class ShareOut(BaseModel):
    id: int
    contact_name: str | None
    expires_at: datetime
    revoked: bool


@router.post("/trips/{trip_id}/share", response_model=ShareCreated, status_code=201)
def create_share(trip_id: int, body: ShareIn, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ShareCreated:
    t = _own_trip(db, user, trip_id)
    if t.status != "active":
        raise HTTPException(409, "This journey has ended.")
    if sum(1 for s in t.shares if s.revoked_at is None and s.expires_at > utcnow()) >= MAX_SHARES_PER_TRIP:
        raise HTTPException(422, "Too many active links for this journey. Turn one off first.")
    contact = None
    if body.contact_id is not None:
        contact = db.get(TrustedContact, body.contact_id)
        if contact is None or contact.user_id != user.id:
            raise HTTPException(404, "Contact not found.")
    raw, hashed = new_share_token()
    s = TripShare(trip_id=t.id, contact_id=contact.id if contact else None, token_hash=hashed,
                  expires_at=utcnow() + timedelta(hours=body.hours))
    db.add(s)
    db.commit()
    # The raw token is shown once and never stored.
    return ShareCreated(share_id=s.id, url=f"{settings.public_web_url}/s/{raw}", expires_at=s.expires_at,
                        contact_name=contact.name if contact else None)


@router.get("/trips/{trip_id}/shares", response_model=list[ShareOut])
def list_shares(trip_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ShareOut]:
    t = _own_trip(db, user, trip_id)
    out = []
    for s in t.shares:
        c = db.get(TrustedContact, s.contact_id) if s.contact_id else None
        out.append(ShareOut(id=s.id, contact_name=c.name if c else None, expires_at=s.expires_at,
                            revoked=s.revoked_at is not None))
    return out


@router.delete("/trips/{trip_id}/shares/{share_id}", status_code=204)
def revoke_share(trip_id: int, share_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    t = _own_trip(db, user, trip_id)
    s = next((x for x in t.shares if x.id == share_id), None)
    if s is None:
        raise HTTPException(404, "Link not found.")
    s.revoked_at = s.revoked_at or utcnow()
    db.commit()


# ---------- public view for a contact ----------
class SharedView(BaseModel):
    traveller: str
    destination: str
    state: str
    started_at: datetime
    expected_arrival: datetime
    last_checkin_at: datetime | None
    last_lat: float | None
    last_lng: float | None
    note: str = "Location shown is the traveller's last check-in, not live tracking."


@router.get("/shared/{token}", response_model=SharedView, dependencies=[Depends(limit("shared", 60, 60))])
def shared_view(token: str, db: Session = Depends(get_db)) -> SharedView:
    s = db.scalar(select(TripShare).where(TripShare.token_hash == hash_token(token)))
    gone = HTTPException(404, "This link is no longer active.")
    if s is None or s.revoked_at is not None or s.expires_at <= utcnow():
        raise gone
    t = db.get(Trip, s.trip_id)
    if t is None or t.status != "active":
        raise gone
    owner = db.get(User, t.user_id)
    return SharedView(
        traveller=owner.display_name.split()[0] if owner else "Traveller", destination=t.dest_name,
        state=trip_state(t), started_at=t.started_at, expected_arrival=t.expected_arrival,
        last_checkin_at=t.last_checkin_at, last_lat=t.last_lat, last_lng=t.last_lng,
    )
