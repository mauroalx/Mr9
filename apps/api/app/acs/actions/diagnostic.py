"""Diagnóstico scored + limpeza de histórico."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action
from app.cpe.extract import extract_neighbor_networks
from app.models.diagnostic import DiagnosticRun
from app.models.settings import AppSettings
from app.services.diagnostic_service import run_router_diagnostic


@action("diagnostic_clear", permission="acs.diagnostic-clear", notes="Apaga runs do device no Postgres")
async def diagnostic_clear(ctx: ActionContext) -> dict[str, Any]:
    ctx.db.query(DiagnosticRun).filter(DiagnosticRun.device_id == ctx.device_id).delete()
    ctx.db.commit()
    return {"ok": True}


@action("diagnostic_full", permission="acs.diagnostic", notes="Score settings-driven + neighbors do catálogo")
async def diagnostic_full(ctx: ActionContext) -> dict[str, Any]:
    settings = ctx.db.query(AppSettings).first()
    approved = list(settings.approved_dns or []) if settings else []
    dev = await ctx.client.get_device(ctx.device_id) or {}
    report = run_router_diagnostic(
        dev,
        approved_dns=approved,
        ping_results=ctx.params.get("ping_results"),
    )
    report["neighbors"] = extract_neighbor_networks(dev)
    run = DiagnosticRun(
        device_id=ctx.device_id,
        acs_server_id=ctx.server.id,
        score=int(report["score"]),
        grade=str(report["grade"]),
        report=report,
        created_by=ctx.auth.user.email,
    )
    ctx.db.add(run)
    ctx.db.commit()
    ctx.db.refresh(run)
    return {"ok": True, "run_id": str(run.id), "report": report}
