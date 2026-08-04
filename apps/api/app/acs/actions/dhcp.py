"""DHCP LAN get / set (paths via catálogo CPE)."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any

from fastapi import HTTPException

from app.acs.actions.base import ActionContext, action, set_parameter_values
from app.cpe.extract import dhcp_paths, extract_dhcp_lan


def _ipv4(raw: Any, label: str) -> str:
    try:
        return str(IPv4Address(str(raw).strip()))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{label} inválido") from exc


def validate_dhcp_params(raw: dict[str, Any]) -> dict[str, Any]:
    """Normaliza configuração antes de criar a tarefa TR-069."""
    values: dict[str, Any] = {}
    if "enabled" in raw:
        values["enabled"] = bool(raw["enabled"])
    for key, label in (
        ("lanIp", "Gateway"),
        ("minAddress", "Início do pool"),
        ("maxAddress", "Fim do pool"),
    ):
        if raw.get(key):
            values[key] = _ipv4(raw[key], label)
    if raw.get("subnetMask"):
        values["subnetMask"] = _ipv4(raw["subnetMask"], "Máscara")
    if raw.get("dnsServers"):
        dns = [
            _ipv4(item, "Servidor DNS")
            for item in str(raw["dnsServers"]).split(",")
            if item.strip()
        ]
        if not dns:
            raise HTTPException(status_code=400, detail="Informe ao menos um servidor DNS")
        values["dnsServers"] = ",".join(dns)
    if raw.get("leaseTime") is not None:
        try:
            lease = int(raw["leaseTime"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="Lease inválido") from exc
        if lease < 60:
            raise HTTPException(status_code=400, detail="Lease deve ser de pelo menos 60 segundos")
        values["leaseTime"] = lease

    if values.get("lanIp") and values.get("subnetMask"):
        try:
            network = IPv4Network(
                f'{values["lanIp"]}/{values["subnetMask"]}', strict=False
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Gateway e máscara incompatíveis") from exc
        for key, label in (("minAddress", "Início do pool"), ("maxAddress", "Fim do pool")):
            if values.get(key) and IPv4Address(values[key]) not in network:
                raise HTTPException(status_code=400, detail=f"{label} está fora da sub-rede")
    if (
        values.get("minAddress")
        and values.get("maxAddress")
        and IPv4Address(values["minAddress"]) > IPv4Address(values["maxAddress"])
    ):
        raise HTTPException(status_code=400, detail="Início do pool deve ser menor que o fim")
    return values


@action("dhcp_get", notes="Lê LANHostConfigManagement via catálogo")
async def dhcp_get(ctx: ActionContext) -> dict[str, Any]:
    return {"ok": True, "config": extract_dhcp_lan(await ctx.load_device())}


@action("dhcp_set", permission="acs.devices.write", notes="SPV DNS/pool/lease usando Cap.DHCP_*")
async def dhcp_set(ctx: ActionContext) -> dict[str, Any]:
    paths = dhcp_paths(await ctx.load_device())
    p = validate_dhcp_params(ctx.params)
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
