"""Handlers de energia / sync de inventário."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action, create_named_task
from app.cpe.params import Cap
from app.cpe.profiles import candidates_for


@action("reboot", permission="acs.devices.write", notes="Reboot via task GenieACS")
async def reboot(ctx: ActionContext) -> dict[str, Any]:
    return await create_named_task(ctx, {"name": "reboot"}, timeout_ms=20000)


@action("sync", permission="acs.devices.write", notes="refreshObject no IGD root do catálogo")
async def sync(ctx: ActionContext) -> dict[str, Any]:
    return await _refresh_inventory(ctx)


@action(
    "inventory_refresh",
    permission="acs.access",
    notes="Atualiza o inventário ausente sem alterar a configuração do CPE",
)
async def inventory_refresh(ctx: ActionContext) -> dict[str, Any]:
    return await _refresh_inventory(ctx)


async def _refresh_inventory(ctx: ActionContext) -> dict[str, Any]:
    dev = await ctx.load_device()
    igd = (candidates_for(dev, Cap.IGD_ROOT) or ["InternetGatewayDevice"])[0]
    return await create_named_task(
        ctx,
        {"name": "refreshObject", "objectName": igd},
        timeout_ms=25000,
    )
