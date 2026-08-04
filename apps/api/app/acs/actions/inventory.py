"""Leituras de inventário (hosts)."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action
from app.cpe.extract import extract_hosts


@action("hosts_get", notes="Clientes LAN (Hosts.Host)")
async def hosts_get(ctx: ActionContext) -> dict[str, Any]:
    dev = await ctx.client.get_device(ctx.device_id) or {}
    return {"ok": True, "hosts": extract_hosts(dev)}
