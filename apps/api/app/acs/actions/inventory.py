"""Leituras de inventário (hosts)."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action
from app.cpe.extract import extract_hosts


@action("hosts_get", notes="Clientes LAN (Hosts.Host)")
async def hosts_get(ctx: ActionContext) -> dict[str, Any]:
    return {"ok": True, "hosts": extract_hosts(await ctx.load_device())}
