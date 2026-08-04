"""Rotas HTTP de dispositivos ACS — finas; lógica em `app.acs.*` / `app.cpe.*`."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.acs.actions import ActionContext, dispatch, ensure_handlers_loaded, get_action, list_actions
from app.acs.summary import DEVICE_DETAIL_PROJECTION, build_workbench, device_summary
from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth, optional_acs_server_id
from app.cpe.extract import extract_wan_profiles
from app.cpe.params import Cap
from app.cpe.profiles import discovery_candidates
from app.models.audit import AuditEvent
from app.models.diagnostic import DiagnosticRun
from app.models.settings import AppSettings
from app.services.acs_factory import build_client
from app.services.device_inventory import build_inventory_query

router = APIRouter(prefix="/acs", tags=["acs-devices"])


class ActionIn(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("/actions")
def catalog_actions(auth: AuthContext = Depends(get_current_auth)):
    """Catálogo legível para contribuidores / UI (debug)."""
    auth.require("acs.access")
    ensure_handlers_loaded()
    return {"items": [{"name": a.name, "permission": a.permission, "notes": a.notes} for a in list_actions()]}


@router.get("/devices")
async def list_devices(
    q: str | None = None,
    online: bool | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
    firmware: str | None = None,
    tag: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.access")
    settings = db.query(AppSettings).first()
    threshold = settings.online_threshold_s if settings else 300
    client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
    query = build_inventory_query(
        q=q,
        online=online,
        manufacturer=manufacturer,
        model=model,
        firmware=firmware,
        tag=tag,
        now=datetime.now(UTC),
        online_threshold_s=server.online_threshold_s or threshold,
    )
    try:
        rows, total = await asyncio.gather(
            client.search_devices(
                query=query or {},
                projection=[
                    "_id",
                    "_deviceId",
                    "_lastInform",
                    "_tags",
                    "InternetGatewayDevice.DeviceInfo.SoftwareVersion",
                    *[path for path in discovery_candidates(Cap.WAN_DEVICE) if "{" not in path],
                ],
                limit=limit,
                skip=skip,
            ),
            client.count_devices(query=query or {}),
        )
    finally:
        await client.aclose()
    items = []
    for row in rows:
        item = device_summary(row, online_threshold_s=server.online_threshold_s or threshold)
        ppp_profiles = [
            profile
            for profile in extract_wan_profiles(row)
            if profile["kind"] == "ppp" and profile["username"]
        ]
        item["pppoe_username"] = ppp_profiles[0]["username"] if ppp_profiles else None
        items.append(item)
    return {
        "acs_server_id": str(server.id),
        "items": items,
        "count": len(items),
        "total": total,
        "has_more": skip + len(items) < total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/devices/{device_id:path}/actions")
async def device_actions(
    device_id: str,
    body: ActionIn,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.access")
    client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
    try:
        ctx = ActionContext(
            device_id=device_id,
            params=body.params or {},
            client=client,
            db=db,
            auth=auth,
            server=server,
        )
        action_name = body.action.strip()
        action_spec = get_action(action_name)
        try:
            result = await dispatch(ctx, action_name)
            if action_spec is None or action_spec.audit:
                db.add(
                    AuditEvent(
                        actor=auth.user.email,
                        action=action_name,
                        target=device_id,
                        status="queued" if result.get("queued") else "success",
                        details={"acs_server_id": str(server.id)},
                    )
                )
                db.commit()
            return result
        except Exception as exc:
            db.rollback()
            if action_spec is None or action_spec.audit:
                db.add(
                    AuditEvent(
                        actor=auth.user.email,
                        action=action_name,
                        target=device_id,
                        status="failed",
                        details={"error_type": type(exc).__name__, "acs_server_id": str(server.id)},
                    )
                )
                db.commit()
            raise
    finally:
        await client.aclose()


@router.get("/devices/{device_id:path}/diagnostics")
def list_diagnostics(
    device_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    auth.require("acs.access")
    rows = (
        db.query(DiagnosticRun)
        .filter(DiagnosticRun.device_id == device_id)
        .order_by(DiagnosticRun.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "items": [
            {
                "id": str(r.id),
                "score": r.score,
                "grade": r.grade,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "created_by": r.created_by,
                "report": r.report,
            }
            for r in rows
        ]
    }


# A rota catch-all deve permanecer por último para não capturar `/diagnostics`.
@router.get("/devices/{device_id:path}")
async def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.access")
    client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
    try:
        dev = await client.get_device(device_id, projection=DEVICE_DETAIL_PROJECTION)
    finally:
        await client.aclose()
    if not dev:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    settings = db.query(AppSettings).first()
    threshold = settings.online_threshold_s if settings else 300
    return {
        "acs_server_id": str(server.id),
        "summary": device_summary(dev, online_threshold_s=server.online_threshold_s or threshold),
        "device": dev,
        "workbench": build_workbench(dev),
    }
