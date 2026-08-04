"""Wi‑Fi set / get."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.acs.actions.base import ActionContext, action, set_parameter_values
from app.cpe.extract import extract_wifi_radios, wifi_set_parameter_values


@action("wifi_get", notes="Extrai rádios/SSID do inventário via catálogo CPE")
async def wifi_get(ctx: ActionContext) -> dict[str, Any]:
    dev = await ctx.client.get_device(ctx.device_id) or {}
    return {"ok": True, "radios": extract_wifi_radios(dev)}


@action("wifi_set", permission="acs.devices.write", notes="SPV SSID/senha; paths via catálogo")
async def wifi_set(ctx: ActionContext) -> dict[str, Any]:
    pvs = ctx.params.get("parameterValues")
    if not isinstance(pvs, list):
        root = str(ctx.params.get("root") or "").strip()
        if not root:
            raise HTTPException(status_code=400, detail="root ou parameterValues obrigatório")
        pvs = wifi_set_parameter_values(
            root,
            ssid=None if ctx.params.get("ssid") is None else str(ctx.params.get("ssid")),
            password=str(ctx.params["password"]) if ctx.params.get("password") else None,
        )
    if not pvs:
        raise HTTPException(status_code=400, detail="Nenhuma alteração Wi‑Fi")
    return await set_parameter_values(ctx.client, ctx.device_id, pvs)
