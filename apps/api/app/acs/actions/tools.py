"""Ping / traceroute — enfileira DiagnosticsState=Requested."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action, require_str, set_parameter_values
from app.cpe.extract import diag_roots


@action("ping", permission="acs.devices.write", notes="IPPingDiagnostics via Cap.diag.ping")
async def ping(ctx: ActionContext) -> dict[str, Any]:
    host = require_str(ctx.params, "host")
    roots = diag_roots(await ctx.client.get_device(ctx.device_id) or {})
    diagnostics_root = roots.get("ping") or "InternetGatewayDevice.IPPingDiagnostics"
    pvs = [
        [f"{diagnostics_root}.Host", host, "xsd:string"],
        [f"{diagnostics_root}.NumberOfRepetitions", int(ctx.params.get("count") or 3), "xsd:unsignedInt"],
        [f"{diagnostics_root}.DiagnosticsState", "Requested", "xsd:string"],
    ]
    return await set_parameter_values(ctx.client, ctx.device_id, pvs)


@action("traceroute", permission="acs.devices.write", notes="TraceRouteDiagnostics via Cap.diag.traceroute")
async def traceroute(ctx: ActionContext) -> dict[str, Any]:
    host = require_str(ctx.params, "host")
    roots = diag_roots(await ctx.client.get_device(ctx.device_id) or {})
    root = roots.get("traceroute") or "InternetGatewayDevice.TraceRouteDiagnostics"
    pvs = [
        [f"{root}.Host", host, "xsd:string"],
        [f"{root}.DiagnosticsState", "Requested", "xsd:string"],
    ]
    return await set_parameter_values(ctx.client, ctx.device_id, pvs)
