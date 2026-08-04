from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AuthContext, get_current_auth, optional_acs_server_id
from app.models.diagnostic import DiagnosticRun
from app.models.settings import AppSettings
from app.services.acs_factory import build_client
from app.services.cpe_extract import (
    dhcp_paths,
    diag_roots,
    extract_dhcp_lan,
    extract_hosts,
    extract_neighbor_networks,
    extract_port_mappings,
    extract_wan_profiles,
    extract_wifi_radios,
    wifi_set_parameter_values,
)
from app.services.diagnostic_service import run_router_diagnostic

router = APIRouter(prefix="/acs", tags=["acs-devices"])

PPP_ROOT_RE = re.compile(
    r"^InternetGatewayDevice\.WANDevice\.\d+\.WANConnectionDevice\.\d+\.WANPPPConnection\.\d+$"
)


def _leaf(v: Any) -> Any:
    if isinstance(v, dict) and "_value" in v:
        return v.get("_value")
    return v


def _dig(obj: Any, *parts: str) -> Any:
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def _device_summary(dev: dict[str, Any], *, online_threshold_s: int) -> dict[str, Any]:
    last = dev.get("_lastInform")
    last_s = None
    if isinstance(last, dict):
        last_s = last.get("_value") or last.get("$date")
    elif isinstance(last, str):
        last_s = last
    online = False
    age = None
    if last_s:
        try:
            ts = datetime.fromisoformat(str(last_s).replace("Z", "+00:00"))
            age = int((datetime.now(timezone.utc) - ts).total_seconds())
            online = age <= online_threshold_s
        except Exception:
            pass
    did = dev.get("_deviceId") or {}
    return {
        "id": dev.get("_id"),
        "serial": did.get("_SerialNumber"),
        "product_class": did.get("_ProductClass"),
        "manufacturer": did.get("_Manufacturer"),
        "last_inform": last_s,
        "online": online,
        "offline_age_s": age,
        "software_version": _leaf(_dig(dev, "InternetGatewayDevice", "DeviceInfo", "SoftwareVersion")),
        "tags": list((dev.get("_tags") or [])) if isinstance(dev.get("_tags"), list) else [],
    }


async def _spv(client: Any, device_id: str, parameter_values: list[list[Any]]) -> dict[str, Any]:
    res = await client.create_task(
        device_id,
        {"name": "setParameterValues", "parameterValues": parameter_values},
        connection_request=True,
        timeout_ms=25000,
    )
    return {"ok": res.status_code in {200, 202}, "http": res.status_code, "queued": res.status_code == 202}


@router.get("/devices")
async def list_devices(
    q: str | None = None,
    online: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.access")
    settings = db.query(AppSettings).first()
    threshold = settings.online_threshold_s if settings else 300
    client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
    query: dict[str, Any] = {}
    if q:
        query = {
            "$or": [
                {"_deviceId._SerialNumber": {"$regex": q, "$options": "i"}},
                {"_id": {"$regex": q, "$options": "i"}},
            ]
        }
    try:
        rows = await client.search_devices(
            query=query or {},
            projection=[
                "_id",
                "_deviceId",
                "_lastInform",
                "_tags",
                "InternetGatewayDevice.DeviceInfo.SoftwareVersion",
            ],
            limit=limit,
            skip=skip,
        )
    finally:
        await client.aclose()
    items = [_device_summary(r, online_threshold_s=server.online_threshold_s or threshold) for r in rows]
    if online is not None:
        items = [i for i in items if bool(i["online"]) is online]
    return {"acs_server_id": str(server.id), "items": items, "count": len(items)}


@router.get("/devices/{device_id:path}")
async def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.access")
    client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
    try:
        dev = await client.get_device(
            device_id,
            projection=[
                "_id",
                "_deviceId",
                "_lastInform",
                "_tags",
                "InternetGatewayDevice.DeviceInfo",
                "InternetGatewayDevice.LANDevice.1.LANHostConfigManagement",
                "InternetGatewayDevice.LANDevice.1.Hosts",
                "InternetGatewayDevice.LANDevice.1.WLANConfiguration",
                "InternetGatewayDevice.LANDevice.1.WiFi",
                "InternetGatewayDevice.LANDevice.1.WIFI",
                "InternetGatewayDevice.WANDevice",
                "InternetGatewayDevice.WiFi",
            ],
        )
    finally:
        await client.aclose()
    if not dev:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    settings = db.query(AppSettings).first()
    threshold = settings.online_threshold_s if settings else 300
    summary = _device_summary(dev, online_threshold_s=server.online_threshold_s or threshold)
    return {
        "acs_server_id": str(server.id),
        "summary": summary,
        "device": dev,
        "workbench": {
            "wifi": extract_wifi_radios(dev),
            "wan": extract_wan_profiles(dev),
            "dhcp": extract_dhcp_lan(dev),
            "hosts": extract_hosts(dev),
            "portmap": extract_port_mappings(dev),
            "neighbors": extract_neighbor_networks(dev),
        },
    }


class ActionIn(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


@router.post("/devices/{device_id:path}/actions")
async def device_actions(
    device_id: str,
    body: ActionIn,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
    server_id: uuid.UUID | None = Depends(optional_acs_server_id),
):
    auth.require("acs.access")
    action = body.action.strip()
    write_actions = {
        "reboot",
        "wifi_set",
        "wan_set_pppoe",
        "dhcp_set",
        "tags_add",
        "tags_remove",
        "sync",
        "port_mapping_add",
        "port_mapping_delete",
        "static_host_set",
    }
    if action in write_actions:
        auth.require("acs.devices.write")
    if action == "diagnostic_full":
        auth.require("acs.diagnostic")
    if action == "diagnostic_clear":
        auth.require("acs.diagnostic-clear")

    client, server = build_client(db, server_id or auth.user.preferred_acs_server_id)
    try:
        if action == "reboot":
            res = await client.create_task(device_id, {"name": "reboot"}, connection_request=True, timeout_ms=20000)
            return {"ok": res.status_code in {200, 202}, "http": res.status_code}
        if action == "sync":
            res = await client.create_task(
                device_id,
                {"name": "refreshObject", "objectName": "InternetGatewayDevice"},
                connection_request=True,
                timeout_ms=25000,
            )
            return {"ok": res.status_code in {200, 202}, "http": res.status_code}
        if action == "tags_add":
            tag = str(body.params.get("tag") or "").strip()
            if not tag:
                raise HTTPException(status_code=400, detail="tag obrigatória")
            res = await client.set_tag(device_id, tag)
            return {"ok": res.status_code in {200, 204}, "http": res.status_code}
        if action == "tags_remove":
            tag = str(body.params.get("tag") or "").strip()
            if not tag:
                raise HTTPException(status_code=400, detail="tag obrigatória")
            res = await client.delete_tag(device_id, tag)
            return {"ok": res.status_code in {200, 204}, "http": res.status_code}
        if action == "wifi_set":
            pvs = body.params.get("parameterValues")
            if not isinstance(pvs, list):
                root = str(body.params.get("root") or "").strip()
                if not root:
                    raise HTTPException(status_code=400, detail="root ou parameterValues obrigatório")
                pvs = wifi_set_parameter_values(
                    root,
                    ssid=None if body.params.get("ssid") is None else str(body.params.get("ssid")),
                    password=str(body.params["password"]) if body.params.get("password") else None,
                )
            if not pvs:
                raise HTTPException(status_code=400, detail="Nenhuma alteração Wi‑Fi")
            return await _spv(client, device_id, pvs)
        if action == "wan_set_pppoe":
            root = str(body.params.get("root") or "").strip()
            if not PPP_ROOT_RE.match(root):
                raise HTTPException(status_code=400, detail="WAN PPP root inválido")
            dev = await client.get_device(device_id) or {}
            profiles = extract_wan_profiles(dev)
            profile = next((p for p in profiles if str(p.get("root")) == root), None)
            pvs: list[list[Any]] = []
            if body.params.get("username") is not None:
                pvs.append([f"{root}.Username", str(body.params["username"]).strip(), "xsd:string"])
            if body.params.get("password"):
                pvs.append([f"{root}.Password", str(body.params["password"]), "xsd:string"])
            if body.params.get("vlan") is not None:
                vlan = str(body.params["vlan"]).strip()
                vlan_path = str(
                    body.params.get("vlan_path")
                    or (profile or {}).get("vlan_path")
                    or f"{root}.X_VT_VLANID"
                )
                pvs.append([vlan_path, int(vlan), "xsd:unsignedInt"])
            if "natEnabled" in body.params:
                nat_path = str((profile or {}).get("nat_path") or f"{root}.NATEnabled")
                pvs.append([nat_path, bool(body.params["natEnabled"]), "xsd:boolean"])
            if not pvs:
                raise HTTPException(status_code=400, detail="Nenhuma alteração WAN")
            return await _spv(client, device_id, pvs)
        if action == "dhcp_set":
            paths = dhcp_paths(await client.get_device(device_id) or {})
            pvs = []
            p = body.params
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
            return await _spv(client, device_id, pvs)
        if action == "port_mapping_get":
            dev = await client.get_device(device_id) or {}
            return {"ok": True, "mappings": extract_port_mappings(dev)}
        if action == "port_mapping_add":
            wan_root = str(body.params.get("wanRoot") or "").strip()
            if not wan_root:
                raise HTTPException(status_code=400, detail="wanRoot obrigatório")
            add = await client.create_task(
                device_id,
                {"name": "addObject", "objectName": f"{wan_root}.PortMapping"},
                connection_request=True,
                timeout_ms=25000,
            )
            # Best-effort SPV after add (index may need refresh by operator)
            index = body.params.get("index")
            if index is not None:
                root = f"{wan_root}.PortMapping.{int(index)}"
                pvs = [
                    [f"{root}.PortMappingEnabled", bool(body.params.get("enabled", True)), "xsd:boolean"],
                    [f"{root}.ExternalPort", int(body.params.get("externalPort") or 0), "xsd:unsignedInt"],
                    [f"{root}.InternalPort", int(body.params.get("internalPort") or 0), "xsd:unsignedInt"],
                    [f"{root}.InternalClient", str(body.params.get("internalClient") or ""), "xsd:string"],
                    [f"{root}.PortMappingProtocol", str(body.params.get("protocol") or "TCP"), "xsd:string"],
                    [f"{root}.PortMappingDescription", str(body.params.get("description") or ""), "xsd:string"],
                ]
                spv = await _spv(client, device_id, pvs)
                return {"ok": add.status_code in {200, 202} and spv["ok"], "add_http": add.status_code, **spv}
            return {"ok": add.status_code in {200, 202}, "http": add.status_code, "note": "refresh device to find new index"}
        if action == "port_mapping_delete":
            mapping_root = str(body.params.get("root") or "").strip()
            if not mapping_root:
                raise HTTPException(status_code=400, detail="root do mapping obrigatório")
            res = await client.create_task(
                device_id,
                {"name": "deleteObject", "objectName": mapping_root},
                connection_request=True,
                timeout_ms=25000,
            )
            return {"ok": res.status_code in {200, 202}, "http": res.status_code}
        if action == "hosts_get":
            dev = await client.get_device(device_id) or {}
            return {"ok": True, "hosts": extract_hosts(dev)}
        if action == "wan_get":
            dev = await client.get_device(device_id) or {}
            return {"ok": True, "profiles": extract_wan_profiles(dev)}
        if action == "dhcp_get":
            dev = await client.get_device(device_id) or {}
            return {"ok": True, "config": extract_dhcp_lan(dev)}
        if action == "wifi_get":
            dev = await client.get_device(device_id) or {}
            return {"ok": True, "radios": extract_wifi_radios(dev)}
        if action == "ping":
            host = str(body.params.get("host") or "").strip()
            if not host:
                raise HTTPException(status_code=400, detail="host obrigatório")
            roots = diag_roots(await client.get_device(device_id) or {})
            diagnostics_root = roots.get("ping") or "InternetGatewayDevice.IPPingDiagnostics"
            pvs = [
                [f"{diagnostics_root}.Host", host, "xsd:string"],
                [f"{diagnostics_root}.NumberOfRepetitions", int(body.params.get("count") or 3), "xsd:unsignedInt"],
                [f"{diagnostics_root}.DiagnosticsState", "Requested", "xsd:string"],
            ]
            return await _spv(client, device_id, pvs)
        if action == "traceroute":
            host = str(body.params.get("host") or "").strip()
            if not host:
                raise HTTPException(status_code=400, detail="host obrigatório")
            roots = diag_roots(await client.get_device(device_id) or {})
            root = roots.get("traceroute") or "InternetGatewayDevice.TraceRouteDiagnostics"
            pvs = [
                [f"{root}.Host", host, "xsd:string"],
                [f"{root}.DiagnosticsState", "Requested", "xsd:string"],
            ]
            return await _spv(client, device_id, pvs)
        if action == "diagnostic_clear":
            db.query(DiagnosticRun).filter(DiagnosticRun.device_id == device_id).delete()
            db.commit()
            return {"ok": True}
        if action == "diagnostic_full":
            settings = db.query(AppSettings).first()
            approved = list(settings.approved_dns or []) if settings else []
            dev = await client.get_device(device_id) or {}
            report = run_router_diagnostic(
                dev,
                approved_dns=approved,
                ping_results=body.params.get("ping_results"),
            )
            report["neighbors"] = extract_neighbor_networks(dev)
            run = DiagnosticRun(
                device_id=device_id,
                acs_server_id=server.id,
                score=int(report["score"]),
                grade=str(report["grade"]),
                report=report,
                created_by=auth.user.email,
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return {"ok": True, "run_id": str(run.id), "report": report}
        raise HTTPException(status_code=422, detail=f"Action não suportada: {action}")
    finally:
        await client.aclose()


@router.get("/devices/{device_id:path}/diagnostics")
def list_diagnostics(
    device_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    auth.require("acs.access")
    rows = (
        db.query(DiagnosticRun)
        .filter(DiagnosticRun.device_id == device_id)
        .order_by(DiagnosticRun.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "items": [
            {
                "id": str(r.id),
                "score": r.score,
                "grade": r.grade,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "created_by": r.created_by,
                "report": r.report,
            }
            for r in rows
        ]
    }
