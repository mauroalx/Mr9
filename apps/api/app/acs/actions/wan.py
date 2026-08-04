"""WAN PPPoE get / set."""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException

from app.acs.actions.base import ActionContext, action, require_str, set_parameter_values
from app.cpe.extract import extract_wan_profiles

PPP_ROOT_RE = re.compile(
    r"^InternetGatewayDevice\.WANDevice\.\d+\.WANConnectionDevice\.\d+\.WANPPPConnection\.\d+$"
)


@action("wan_get", notes="Lista perfis WAN PPP/IP do inventário")
async def wan_get(ctx: ActionContext) -> dict[str, Any]:
    dev = await ctx.client.get_device(ctx.device_id) or {}
    return {"ok": True, "profiles": extract_wan_profiles(dev)}


@action("wan_set_pppoe", permission="acs.devices.write", notes="SPV user/pass/vlan/NAT; VLAN path do catálogo")
async def wan_set_pppoe(ctx: ActionContext) -> dict[str, Any]:
    root = require_str(ctx.params, "root", detail="WAN PPP root obrigatório")
    if not PPP_ROOT_RE.match(root):
        raise HTTPException(status_code=400, detail="WAN PPP root inválido")

    dev = await ctx.client.get_device(ctx.device_id) or {}
    profile = next((p for p in extract_wan_profiles(dev) if str(p.get("root")) == root), None)

    pvs: list[list[Any]] = []
    if ctx.params.get("username") is not None:
        pvs.append([f"{root}.Username", str(ctx.params["username"]).strip(), "xsd:string"])
    if ctx.params.get("password"):
        pvs.append([f"{root}.Password", str(ctx.params["password"]), "xsd:string"])
    if ctx.params.get("vlan") is not None:
        vlan = str(ctx.params["vlan"]).strip()
        vlan_path = str(
            ctx.params.get("vlan_path") or (profile or {}).get("vlan_path") or f"{root}.X_VT_VLANID"
        )
        pvs.append([vlan_path, int(vlan), "xsd:unsignedInt"])
    if "natEnabled" in ctx.params:
        nat_path = str((profile or {}).get("nat_path") or f"{root}.NATEnabled")
        pvs.append([nat_path, bool(ctx.params["natEnabled"]), "xsd:boolean"])
    if not pvs:
        raise HTTPException(status_code=400, detail="Nenhuma alteração WAN")
    return await set_parameter_values(ctx.client, ctx.device_id, pvs)
