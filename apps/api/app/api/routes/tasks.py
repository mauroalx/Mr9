"""Fila de tarefas GenieACS exposta com contrato próprio do Mr9."""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth, optional_acs_server_id
from app.services.acs_factory import build_client

router = APIRouter(prefix="/acs/tasks", tags=["acs-tasks"])


@router.get("")
async def list_tasks(
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.access")
    query: dict[str, Any] = {}
    if q:
        search = re.escape(q.strip())
        query = {
            "$or": [
                {"device": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
            ]
        }
    client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
    try:
        rows = await client.list_tasks(query=query, limit=limit + 1, skip=skip)
    finally:
        await client.aclose()
    return {
        "acs_server_id": str(server.id),
        "items": rows[:limit],
        "has_more": len(rows) > limit,
        "skip": skip,
        "limit": limit,
    }


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.devices.write")
    client, _ = build_client(db, server_id or auth.user.preferred_acs_server_id)
    try:
        result = await client.retry_task(task_id)
    finally:
        await client.aclose()
    if result.status_code not in {200, 202}:
        raise HTTPException(status_code=502, detail=f"GenieACS recusou retry (HTTP {result.status_code})")
    return {"ok": True, "queued": result.status_code == 202}


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.devices.write")
    client, _ = build_client(db, server_id or auth.user.preferred_acs_server_id)
    try:
        result = await client.delete_task(task_id)
    finally:
        await client.aclose()
    if result.status_code not in {200, 204}:
        raise HTTPException(status_code=502, detail=f"GenieACS recusou exclusão (HTTP {result.status_code})")
    return Response(status_code=204)
