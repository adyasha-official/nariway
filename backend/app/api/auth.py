import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limit
from app.core.security import current_user, hash_password, make_token, verify_password
from app.db import get_db
from app.models import ReportFlag, SafetyReport, TrustedContact, Trip, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL.match(v):
            raise ValueError("Enter a valid email address.")
        return v


class RegisterBody(Credentials):
    display_name: str = Field(min_length=1, max_length=60)


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    is_admin: bool


class TokenOut(BaseModel):
    access_token: str
    user: UserOut


def _out(u: User) -> TokenOut:
    return TokenOut(access_token=make_token(u), user=UserOut.model_validate(u, from_attributes=True))


@router.post("/register", response_model=TokenOut, status_code=201, dependencies=[Depends(limit("auth", 10, 60))])
def register(body: RegisterBody, db: Session = Depends(get_db)) -> TokenOut:
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "An account with this email already exists.")
    u = User(
        email=body.email,
        display_name=body.display_name.strip(),
        password_hash=hash_password(body.password),
        is_admin=body.email in [e.lower() for e in settings.admin_emails],
    )
    db.add(u)
    db.commit()
    return _out(u)


@router.post("/login", response_model=TokenOut, dependencies=[Depends(limit("auth", 10, 60))])
def login(body: Credentials, db: Session = Depends(get_db)) -> TokenOut:
    u = db.scalar(select(User).where(User.email == body.email))
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Incorrect email or password.")
    return _out(u)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@router.delete("/me", status_code=204)
def delete_account(user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    """Erase the account and everything tied to it. Approved reports stay, but anonymised."""
    for t in db.scalars(select(Trip).where(Trip.user_id == user.id)):
        db.delete(t)  # ORM cascade removes its share tokens
    db.execute(delete(TrustedContact).where(TrustedContact.user_id == user.id))
    db.execute(delete(ReportFlag).where(ReportFlag.user_id == user.id))
    for r in db.scalars(select(SafetyReport).where(SafetyReport.user_id == user.id)):
        r.user_id = None
    db.delete(user)
    db.commit()
