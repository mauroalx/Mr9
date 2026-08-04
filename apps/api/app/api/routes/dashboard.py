from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth, optional_acs_server_id
from app.models.acs_server import AcsServer
from app.models.diagnostic import DiagnosticRun
from app.models.settings import AppSettings
from app.services.acs_factory import build_client

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("dashboard.view")
    servers = db.query(AcsServer).count()
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)
    diag_24h = db.query(DiagnosticRun).filter(DiagnosticRun.created_at >= since_24h).count()
    avg_score = db.query(func.avg(DiagnosticRun.score)).filter(DiagnosticRun.created_at >= since_24h).scalar()

    settings = db.query(AppSettings).first()
    threshold = settings.online_threshold_s if settings else 300

    online = offline = 0
    product_counts: dict[str, int] = {}
    try:
        client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
        try:
            rows = await client.search_devices(
                query={},
                projection=["_id", "_deviceId", "_lastInform"],
                limit=200,
            )
        finally:
            await client.aclose()
        thr = server.online_threshold_s or threshold
        for r in rows:
            last = r.get("_lastInform")
            last_s = last.get("_value") if isinstance(last, dict) else last
            is_online = False
            if last_s:
                try:
                    ts = datetime.fromisoformat(str(last_s).replace("Z", "+00:00"))
                    is_online = (now - ts).total_seconds() <= thr
                except Exception:
                    pass
            if is_online:
                online += 1
            else:
                offline += 1
            pc = ((r.get("_deviceId") or {}).get("_ProductClass")) or "desconhecido"
            product_counts[pc] = product_counts.get(pc, 0) + 1
    except Exception:
        pass

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
        key = r.created_at.astimezone(timezone.utc).strftime("%H:00")
        hourly[key].append(int(r.score))
    series_24h = [{"hour": k, "avg_score": round(sum(v) / len(v), 1), "count": len(v)} for k, v in sorted(hourly.items())]

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
        key = r.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d")
        daily[key].append(int(r.score))
    series_7d = [{"day": k, "avg_score": round(sum(v) / len(v), 1), "count": len(v)} for k, v in sorted(daily.items())]

    top_models = sorted(
        [{"product_class": k, "count": v} for k, v in product_counts.items()],
        key=lambda x: -x["count"],
    )[:8]
    return {
        "kpis": {
            "acs_servers": servers,
            "online": online,
            "offline": offline,
            "diagnostics_24h": diag_24h,
            "avg_score_24h": round(float(avg_score or 0), 1),
        },
        "top_models": top_models,
        "series_24h": series_24h,
        "series_7d": series_7d,
    }
