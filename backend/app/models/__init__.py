from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, UTCDateTime, utcnow


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(60))
    password_hash: Mapped[str] = mapped_column(String(100))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class SafetyReport(Base):
    __tablename__ = "safety_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text, default="")
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    # pending -> approved | rejected ; approved -> expired | hidden (flags)
    status: Mapped[str] = mapped_column(String(12), default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    flags: Mapped[list["ReportFlag"]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (Index("ix_reports_geo", "lat", "lng"),)


class ReportFlag(Base):
    __tablename__ = "report_flags"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("safety_reports.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("report_id", "user_id"),)


class AuditEvent(Base):
    """Moderation and sensitive actions. Never stores reporter identity in `detail`."""

    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    target: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(Text, default="")
    at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class TrustedContact(Base):
    __tablename__ = "trusted_contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(60))
    contact_reference: Mapped[str] = mapped_column(String(80))  # phone or email, used only to open WhatsApp/SMS links
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    origin_name: Mapped[str] = mapped_column(String(120))
    dest_name: Mapped[str] = mapped_column(String(120))
    dest_lat: Mapped[float] = mapped_column(Float)
    dest_lng: Mapped[float] = mapped_column(Float)
    preference: Mapped[str] = mapped_column(String(14))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    expected_arrival: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(10), default="active")  # active | ended
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_checkin_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    shares: Mapped[list["TripShare"]] = relationship(cascade="all, delete-orphan")


class TripShare(Base):
    __tablename__ = "trip_shares"
    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("trusted_contacts.id", ondelete="SET NULL"), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
