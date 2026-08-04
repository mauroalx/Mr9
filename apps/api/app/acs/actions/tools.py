"""Ping / traceroute com execução imediata via connection request."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.acs.actions.base import (
    ActionContext,
    action,
    require_str,
    set_parameter_values_immediately,
)
from app.cpe.extract import diag_roots


@action("ping", permission="acs.devices.write", notes="IPPingDiagnostics via Cap.diag.ping")
async def ping(ctx: ActionContext) -> dict[str, Any]:
    host = require_str(ctx.params, "host")
    roots = diag_roots(await ctx.load_device())
    diagnostics_root = roots.get("ping")
    if not diagnostics_root:
        raise HTTPException(status_code=400, detail="Path de ping não resolvido no catálogo CPE")
    pvs = [
        [f"{diagnostics_root}.Host", host, "xsd:string"],
        [f"{diagnostics_root}.NumberOfRepetitions", int(ctx.params.get("count") or 3), "xsd:unsignedInt"],
        [f"{diagnostics_root}.DiagnosticsState", "Requested", "xsd:string"],
    ]
    return await set_parameter_values_immediately(ctx.client, ctx.device_id, pvs)


@action("traceroute", permission="acs.devices.write", notes="TraceRouteDiagnostics via Cap.diag.traceroute")
async def traceroute(ctx: ActionContext) -> dict[str, Any]:
    host = require_str(ctx.params, "host")
    roots = diag_roots(await ctx.load_device())
    root = roots.get("traceroute")
    if not root:
        raise HTTPException(status_code=400, detail="Path de traceroute não resolvido no catálogo CPE")
    pvs = [
        [f"{root}.Host", host, "xsd:string"],
        [f"{root}.DiagnosticsState", "Requested", "xsd:string"],
    ]
    return await set_parameter_values_immediately(ctx.client, ctx.device_id, pvs)
