from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, places, safety, trips
from app.api.routes import router as routes_router
from app.core.config import settings
from app.db import Base, engine
import app.models  # noqa: F401  (register tables)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment != "development" and settings.jwt_secret == "dev-only-change-me-dev-only-change-me-0000":
        raise RuntimeError("Set JWT_SECRET before running outside development.")
    # Dev convenience. Production should use migrations (Alembic) instead.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

for r in (routes_router, places.router, auth.router, safety.router, admin.router, trips.router):
    app.include_router(r)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
