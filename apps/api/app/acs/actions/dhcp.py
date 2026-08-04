"""DHCP LAN get / set (paths via catálogo CPE)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.acs.actions.base import ActionContext, action, set_parameter_values
from app.cpe.extract import dhcp_paths, extract_dhcp_lan


@action("dhcp_get", notes="Lê LANHostConfigManagement via catálogo")
async def dhcp_get(ctx: ActionContext) -> dict[str, Any]:
    dev = await ctx.client.get_device(ctx.device_id) or {}
    return {"ok": True, "config": extract_dhcp_lan(dev)}


@action("dhcp_set", permission="acs.devices.write", notes="SPV DNS/pool/lease usando Cap.DHCP_*")
async def dhcp_set(ctx: ActionContext) -> dict[str, Any]:
    paths = dhcp_paths(await ctx.client.get_device(ctx.device_id) or {})
    p = ctx.params
    pvs: list[list[Any]] = []
    if "enabled" in p:
        pvs.append([paths["enabled"], bool(p["enabled"]), "xsd:boolean"])
    if p.get("lanIp"):
        ip = str(p["lanIp"]).strip()
        pvs.append([paths["lanIp"], ip, "xsd:string"])
        pvs.append([paths["ipRouters"], ip, "xsd:string"])
    if p.get("subnetMask"):
        mask = str(p["subnetMask"]).strip()
        pvs.append([paths["lanSubnetMask"], mask, "xsd:string"])
        pvs.append([paths["subnetMask"], mask, "xsd:string"])
    if p.get("minAddress"):
        pvs.append([paths["minAddress"], str(p["minAddress"]).strip(), "xsd:string"])
    if p.get("maxAddress"):
        pvs.append([paths["maxAddress"], str(p["maxAddress"]).strip(), "xsd:string"])
    if p.get("dnsServers"):
        pvs.append([paths["dnsServers"], str(p["dnsServers"]).strip(), "xsd:string"])
    if p.get("leaseTime") is not None:
        pvs.append([paths["leaseTime"], int(p["leaseTime"]), "xsd:int"])
    if not pvs:
        raise HTTPException(status_code=400, detail="Nenhuma alteração DHCP")
    return await set_parameter_values(ctx.client, ctx.device_id, pvs)
