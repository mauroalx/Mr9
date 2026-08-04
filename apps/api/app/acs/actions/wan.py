"""WAN PPPoE get / set."""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException

from app.acs.actions.base import ActionContext, action, require_str, set_parameter_values
from app.cpe.extract import extract_wan_profiles
from app.cpe.params import Cap
from app.cpe.profiles import candidates_for
from app.cpe.tree import first_existing_path

PPP_ROOT_RE = re.compile(
    r"^.+\.WANDevice\.\d+\.WANConnectionDevice\.\d+\.WANPPPConnection\.\d+$"
)


@action("wan_get", notes="Lista perfis WAN PPP/IP do inventário")
async def wan_get(ctx: ActionContext) -> dict[str, Any]:
    return {"ok": True, "profiles": extract_wan_profiles(await ctx.load_device())}


@action("wan_set_pppoe", permission="acs.devices.write", notes="SPV user/pass/vlan/NAT via catálogo")
async def wan_set_pppoe(ctx: ActionContext) -> dict[str, Any]:
    root = require_str(ctx.params, "root", detail="WAN PPP root obrigatório")
    if not PPP_ROOT_RE.match(root):
        raise HTTPException(status_code=400, detail="WAN PPP root inválido")

    dev = await ctx.load_device()
    profile = next((p for p in extract_wan_profiles(dev) if str(p.get("root")) == root), None)

    pvs: list[list[Any]] = []
    if ctx.params.get("username") is not None:
        user_tmpl = (candidates_for(dev, Cap.WAN_USERNAME) or ["{root}.Username"])[0]
        pvs.append([user_tmpl.replace("{root}", root), str(ctx.params["username"]).strip(), "xsd:string"])
    if ctx.params.get("password"):
        pass_tmpl = (candidates_for(dev, Cap.WAN_PASSWORD) or ["{root}.Password"])[0]
        pvs.append([pass_tmpl.replace("{root}", root), str(ctx.params["password"]), "xsd:string"])
    if ctx.params.get("vlan") is not None:
        vlan = str(ctx.params["vlan"]).strip()
        vlan_path = str(ctx.params.get("vlan_path") or "").strip() or (profile or {}).get("vlan_path")
        if not vlan_path:
            vlan_path = first_existing_path(
                dev,
                [t.replace("{root}", root) for t in candidates_for(dev, Cap.WAN_VLAN)],
            )
        if not vlan_path:
            raise HTTPException(status_code=400, detail="Path de VLAN não encontrado no catálogo/inventário")
        pvs.append([str(vlan_path), int(vlan), "xsd:unsignedInt"])
    if "natEnabled" in ctx.params:
        nat_path = (profile or {}).get("nat_path")
        if not nat_path:
            nat_path = first_existing_path(
                dev,
                [t.replace("{root}", root) for t in candidates_for(dev, Cap.WAN_NAT)],
            )
        if not nat_path:
            raise HTTPException(status_code=400, detail="Path de NAT não encontrado no catálogo/inventário")
        pvs.append([str(nat_path), bool(ctx.params["natEnabled"]), "xsd:boolean"])
    if not pvs:
        raise HTTPException(status_code=400, detail="Nenhuma alteração WAN")
    return await set_parameter_values(ctx.client, ctx.device_id, pvs)
