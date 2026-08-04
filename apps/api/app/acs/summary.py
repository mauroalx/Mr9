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
from app.cpe.params import Cap, identity_from_device
from app.cpe.profiles import candidates_for
from app.cpe.tree import leaf, param_at


def _detail_projection() -> list[str]:
    """Projection GenieACS alinhada às Caps do workbench (genérico + variantes WiFi)."""
    base = [
        "_id",
        "_deviceId",
        "_lastInform",
        "_tags",
        "InternetGatewayDevice.DeviceInfo",
    ]
    # Caps sem template {i}/{root}
    for cap in (
        Cap.DHCP_ROOT,
        Cap.HOSTS_CONTAINER,
        Cap.WAN_DEVICE,
        Cap.WIFI_RADIO_CONTAINER,
        Cap.NEIGHBOR_RESULT,
        Cap.DEVICE_UPTIME,
    ):
        for path in candidates_for({}, cap):
            if "{" in path:
                continue
            # Hosts.Host → Hosts para projection mais ampla
            if path.endswith(".Host"):
                path = path.rsplit(".", 1)[0]
            if path.endswith(".Result"):
                path = path.rsplit(".", 1)[0]
            base.append(path)
    # dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for p in base:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


DEVICE_DETAIL_PROJECTION: list[str] = _detail_projection()


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
    ident = identity_from_device(dev)
    sw = leaf(param_at(dev, "InternetGatewayDevice.DeviceInfo.SoftwareVersion"))
    return {
        "id": dev.get("_id"),
        "serial": ident.serial or None,
        "product_class": ident.product_class or None,
        "manufacturer": ident.manufacturer or None,
        "last_inform": last_s,
        "online": online,
        "offline_age_s": age,
        "software_version": sw,
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
