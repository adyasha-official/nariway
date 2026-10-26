import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import limiter
from app.core.config import settings
from app.db import Base, get_db
from app.main import app
import app.models as _models  # noqa: F401


@pytest.fixture()
def client():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng, expire_on_commit=False)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    limiter.reset()
    settings.admin_emails = ["admin@example.com"]
    with TestClient(app) as c:
        c.session_factory = Session  # type: ignore[attr-defined]
        yield c
    app.dependency_overrides.clear()


def signup(client, email="a@example.com", name="Asha Rao", password="correct-horse"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "display_name": name})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client):
    return signup(client)


@pytest.fixture()
def admin(client):
    return signup(client, "admin@example.com", "Admin")
