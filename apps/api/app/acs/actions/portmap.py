"""Port mapping get / add / delete."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action, create_named_task, require_str, set_parameter_values
from app.cpe.extract import extract_port_mappings


@action("port_mapping_get", notes="Extrai PortMapping.* das WANs")
async def port_mapping_get(ctx: ActionContext) -> dict[str, Any]:
    return {"ok": True, "mappings": extract_port_mappings(await ctx.load_device())}


@action("port_mapping_add", permission="acs.devices.write", notes="addObject + SPV opcional se index informado")
async def port_mapping_add(ctx: ActionContext) -> dict[str, Any]:
    wan_root = require_str(ctx.params, "wanRoot", detail="wanRoot obrigatório")
    add = await create_named_task(
        ctx,
        {"name": "addObject", "objectName": f"{wan_root}.PortMapping"},
        timeout_ms=25000,
    )
    index = ctx.params.get("index")
    if index is None:
        return {**add, "note": "refresh device to find new index"}
    root = f"{wan_root}.PortMapping.{int(index)}"
    pvs = [
        [f"{root}.PortMappingEnabled", bool(ctx.params.get("enabled", True)), "xsd:boolean"],
        [f"{root}.ExternalPort", int(ctx.params.get("externalPort") or 0), "xsd:unsignedInt"],
        [f"{root}.InternalPort", int(ctx.params.get("internalPort") or 0), "xsd:unsignedInt"],
        [f"{root}.InternalClient", str(ctx.params.get("internalClient") or ""), "xsd:string"],
        [f"{root}.PortMappingProtocol", str(ctx.params.get("protocol") or "TCP"), "xsd:string"],
        [f"{root}.PortMappingDescription", str(ctx.params.get("description") or ""), "xsd:string"],
    ]
    spv = await set_parameter_values(ctx.client, ctx.device_id, pvs)
    return {"ok": add["ok"] and spv["ok"], "add_http": add["http"], **spv}


@action("port_mapping_delete", permission="acs.devices.write", notes="deleteObject no root do mapping")
async def port_mapping_delete(ctx: ActionContext) -> dict[str, Any]:
    mapping_root = require_str(ctx.params, "root", detail="root do mapping obrigatório")
    return await create_named_task(
        ctx,
        {"name": "deleteObject", "objectName": mapping_root},
        timeout_ms=25000,
    )
