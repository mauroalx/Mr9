from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth, optional_acs_server_id
from app.cpe.profiles import manufacturer_distribution_groups
from app.models.acs_server import AcsServer
from app.models.diagnostic import DiagnosticRun
from app.models.settings import AppSettings
from app.services.acs_factory import build_client
from app.services.dashboard_service import collect_acs_metrics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)


@router.get("/summary")
async def dashboard_summary(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("dashboard.view")
    servers = db.query(AcsServer).count()
    now = datetime.now(UTC)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)
    diag_24h = db.query(DiagnosticRun).filter(DiagnosticRun.created_at >= since_24h).count()
    avg_score = db.query(func.avg(DiagnosticRun.score)).filter(DiagnosticRun.created_at >= since_24h).scalar()

    settings = db.query(AppSettings).first()
    threshold = settings.online_threshold_s if settings else 300

    online = offline = stale_24h = firmware_known = 0
    acs_metrics_available = False
    manufacturer_counts: list[dict[str, int | str]] = []
    acs_error: str | None = None
    try:
        client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
        try:
            thr = server.online_threshold_s or threshold
            metrics = await collect_acs_metrics(
                client,
                now=now,
                online_threshold_s=thr,
                manufacturer_groups=manufacturer_distribution_groups(),
            )
        finally:
            await client.aclose()
        online = metrics["online"]
        offline = metrics["offline"]
        stale_24h = metrics["stale_24h"]
        firmware_known = metrics["firmware_known"]
        manufacturer_counts = metrics["manufacturers"]
        acs_metrics_available = True
    except Exception as exc:
        logger.exception("Falha ao coletar métricas ACS do dashboard")
        acs_error = str(exc)

    runs_24h = (
        db.query(DiagnosticRun)
        .filter(DiagnosticRun.created_at >= since_24h)
        .order_by(DiagnosticRun.created_at.asc())
        .all()
    )
    hourly: dict[str, list[int]] = defaultdict(list)
    for r in runs_24h:
        if not r.created_at:
            continue
        key = r.created_at.astimezone(UTC).strftime("%H:00")
        hourly[key].append(int(r.score))
    series_24h = [
        {"hour": k, "avg_score": round(sum(v) / len(v), 1), "count": len(v)}
        for k, v in sorted(hourly.items())
    ]

    runs_7d = (
        db.query(DiagnosticRun)
        .filter(DiagnosticRun.created_at >= since_7d)
        .order_by(DiagnosticRun.created_at.asc())
        .all()
    )
    daily: dict[str, list[int]] = defaultdict(list)
    for r in runs_7d:
        if not r.created_at:
            continue
        key = r.created_at.astimezone(UTC).strftime("%Y-%m-%d")
        daily[key].append(int(r.score))
    series_7d = [
        {"day": k, "avg_score": round(sum(v) / len(v), 1), "count": len(v)} for k, v in sorted(daily.items())
    ]

    return {
        "kpis": {
            "acs_servers": servers,
            "online": online,
            "offline": offline,
            "stale_24h": stale_24h,
            "firmware_known": firmware_known,
            "acs_metrics_available": acs_metrics_available,
            "acs_error": acs_error,
            "diagnostics_24h": diag_24h,
            "avg_score_24h": round(float(avg_score or 0), 1),
        },
        "top_models": [],
        "manufacturers": manufacturer_counts,
        "series_24h": series_24h,
        "series_7d": series_7d,
    }
