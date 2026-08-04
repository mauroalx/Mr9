from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models
from app.api.routes import (
    acs_servers,
    audit,
    auth,
    dashboard,
    devices,
    firmwares,
    health,
    security,
    settings,
    setup,
    tasks,
)
from app.core.config import get_settings
from app.core.crypto import is_weak_secret_key
from app.core.database import SessionLocal, init_db
from app.core.exceptions import AcsConfigError, AcsUpstreamError
from app.services.crypto_integrity import check_crypto_on_boot


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if get_settings().environment.lower() == "production" and is_weak_secret_key():
        raise RuntimeError("MR9_SECRET_KEY fraca ou ausente em ambiente de produção")
    init_db()
    db = SessionLocal()
    try:
        check_crypto_on_boot(db)
    finally:
        db.close()
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


@app.exception_handler(AcsConfigError)
async def acs_config_error_handler(_request: Request, exc: AcsConfigError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(AcsUpstreamError)
async def acs_upstream_error_handler(_request: Request, exc: AcsUpstreamError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


API = "/api/v1"
app.include_router(health.router, prefix=API)
app.include_router(setup.router, prefix=API)
app.include_router(auth.router, prefix=API)
app.include_router(audit.router, prefix=API)
app.include_router(settings.router, prefix=API)
app.include_router(security.router, prefix=API)
app.include_router(acs_servers.router, prefix=API)
app.include_router(devices.router, prefix=API)
app.include_router(tasks.router, prefix=API)
app.include_router(firmwares.router, prefix=API)
app.include_router(dashboard.router, prefix=API)
