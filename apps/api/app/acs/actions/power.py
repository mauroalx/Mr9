"""Handlers de energia / sync de inventário."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action


@action("reboot", permission="acs.devices.write", notes="Reboot via task GenieACS")
async def reboot(ctx: ActionContext) -> dict[str, Any]:
    res = await ctx.client.create_task(
        ctx.device_id, {"name": "reboot"}, connection_request=True, timeout_ms=20000
    )
    return {"ok": res.status_code in {200, 202}, "http": res.status_code}


@action("sync", permission="acs.devices.write", notes="refreshObject InternetGatewayDevice")
async def sync(ctx: ActionContext) -> dict[str, Any]:
    res = await ctx.client.create_task(
        ctx.device_id,
        {"name": "refreshObject", "objectName": "InternetGatewayDevice"},
        connection_request=True,
        timeout_ms=25000,
    )
    return {"ok": res.status_code in {200, 202}, "http": res.status_code}
