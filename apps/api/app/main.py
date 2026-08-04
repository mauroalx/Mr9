from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    acs_servers,
    dashboard,
    devices,
    firmwares,
    health,
    security,
    settings,
    setup,
)
from app.core.config import get_settings
from app.core.database import init_db
import app.models  # noqa: F401 — register ORM tables


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Mr9 API", version="0.1.0", lifespan=lifespan)
settings_obj = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_obj.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API = "/api/v1"
app.include_router(health.router, prefix=API)
app.include_router(setup.router, prefix=API)
app.include_router(auth.router, prefix=API)
app.include_router(settings.router, prefix=API)
app.include_router(security.router, prefix=API)
app.include_router(acs_servers.router, prefix=API)
app.include_router(devices.router, prefix=API)
app.include_router(firmwares.router, prefix=API)
app.include_router(dashboard.router, prefix=API)
