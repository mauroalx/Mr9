"""Resumo + workbench a partir do inventário GenieACS."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.cpe.extract import (
    extract_dhcp_lan,
    extract_hosts,
    extract_neighbor_networks,
    extract_port_mappings,
    extract_wan_profiles,
    extract_wifi_radios,
)
from app.cpe.tree import dig, leaf


DEVICE_DETAIL_PROJECTION: list[str] = [
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
]


def device_summary(dev: dict[str, Any], *, online_threshold_s: int) -> dict[str, Any]:
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
        "software_version": leaf(dig(dev, "InternetGatewayDevice", "DeviceInfo", "SoftwareVersion")),
        "tags": list((dev.get("_tags") or [])) if isinstance(dev.get("_tags"), list) else [],
    }


def build_workbench(dev: dict[str, Any]) -> dict[str, Any]:
    return {
        "wifi": extract_wifi_radios(dev),
        "wan": extract_wan_profiles(dev),
        "dhcp": extract_dhcp_lan(dev),
        "hosts": extract_hosts(dev),
        "portmap": extract_port_mappings(dev),
        "neighbors": extract_neighbor_networks(dev),
    }
