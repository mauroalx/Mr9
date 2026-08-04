"""Port mapping get / add / delete."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.acs.actions.base import ActionContext, action, create_named_task, require_str, set_parameter_values
from app.cpe.extract import extract_port_mappings


def _mapping_values(root: str | None, params: dict[str, Any]) -> list[list[Any]]:
    external = int(params.get("externalPort") or 0)
    internal = int(params.get("internalPort") or 0)
    if not 1 <= external <= 65535 or not 1 <= internal <= 65535:
        raise HTTPException(status_code=400, detail="Portas devem estar entre 1 e 65535")
    prefix = f"{root}." if root else ""
    return [
        [f"{prefix}PortMappingEnabled", bool(params.get("enabled", True)), "xsd:boolean"],
        [f"{prefix}ExternalPort", external, "xsd:unsignedInt"],
        [f"{prefix}InternalPort", internal, "xsd:unsignedInt"],
        [f"{prefix}InternalClient", str(params.get("internalClient") or ""), "xsd:string"],
        [f"{prefix}PortMappingProtocol", str(params.get("protocol") or "TCP"), "xsd:string"],
        [f"{prefix}PortMappingDescription", str(params.get("description") or ""), "xsd:string"],
    ]


@action("port_mapping_get", notes="Extrai PortMapping.* das WANs")
async def port_mapping_get(ctx: ActionContext) -> dict[str, Any]:
    return {"ok": True, "mappings": extract_port_mappings(await ctx.load_device())}


@action(
    "port_mapping_add", permission="acs.devices.write", notes="addObject + SPV opcional se index informado"
)
async def port_mapping_add(ctx: ActionContext) -> dict[str, Any]:
    wan_root = require_str(ctx.params, "wanRoot", detail="wanRoot obrigatório")
    return await create_named_task(
        ctx,
        {
            "name": "addObject",
            "objectName": f"{wan_root}.PortMapping",
            "parameterValues": _mapping_values(None, ctx.params),
        },
        timeout_ms=25000,
    )


@action(
    "port_mapping_set", permission="acs.devices.write", notes="Atualiza uma instância PortMapping existente"
)
async def port_mapping_set(ctx: ActionContext) -> dict[str, Any]:
    root = require_str(ctx.params, "root", detail="root do mapping obrigatório")
    return await set_parameter_values(ctx.client, ctx.device_id, _mapping_values(root, ctx.params))


@action("port_mapping_delete", permission="acs.devices.write", notes="deleteObject no root do mapping")
async def port_mapping_delete(ctx: ActionContext) -> dict[str, Any]:
    mapping_root = require_str(ctx.params, "root", detail="root do mapping obrigatório")
    return await create_named_task(
        ctx,
        {"name": "deleteObject", "objectName": mapping_root},
        timeout_ms=25000,
    )
