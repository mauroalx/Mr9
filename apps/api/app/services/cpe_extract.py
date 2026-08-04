from __future__ import annotations

from typing import Any


def leaf(node: Any) -> Any:
    if isinstance(node, dict) and "_value" in node:
        return node.get("_value")
    return node


def dig(obj: Any, *parts: str) -> Any:
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def param_at(dev: dict[str, Any], dotted: str) -> Any:
    parts = [p for p in dotted.split(".") if p]
    return dig(dev, *parts)


def str_value(node: Any) -> str:
    v = leaf(node)
    return "" if v is None else str(v)


def extract_wifi_radios(dev: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrai WLANConfiguration / WiFi rádios de forma tolerante a vendor."""
    out: list[dict[str, Any]] = []
    lan = dig(dev, "InternetGatewayDevice", "LANDevice", "1") or {}
    for key in ("WLANConfiguration", "WiFi", "WIFI"):
        block = lan.get(key) if isinstance(lan, dict) else None
        if not isinstance(block, dict):
            continue
        for idx, node in block.items():
            if not str(idx).isdigit() or not isinstance(node, dict):
                continue
            ssid = str_value(node.get("SSID") or dig(node, "SSID"))
            channel = str_value(node.get("Channel") or dig(node, "Channel"))
            enable = leaf(node.get("Enable") or dig(node, "Enable"))
            out.append(
                {
                    "root": f"InternetGatewayDevice.LANDevice.1.{key}.{idx}",
                    "index": int(idx),
                    "ssid": ssid,
                    "channel": channel,
                    "enabled": bool(enable) if enable is not None else None,
                    "vendor_key": key,
                }
            )
    return out


def extract_wan_profiles(dev: dict[str, Any]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    wan_device = dig(dev, "InternetGatewayDevice", "WANDevice") or {}
    if not isinstance(wan_device, dict):
        return profiles
    for wd_idx, wd in wan_device.items():
        if not str(wd_idx).isdigit() or not isinstance(wd, dict):
            continue
        conns = wd.get("WANConnectionDevice") or {}
        if not isinstance(conns, dict):
            continue
        for cd_idx, cd in conns.items():
            if not str(cd_idx).isdigit() or not isinstance(cd, dict):
                continue
            for kind in ("WANPPPConnection", "WANIPConnection"):
                block = cd.get(kind) or {}
                if not isinstance(block, dict):
                    continue
                for c_idx, node in block.items():
                    if not str(c_idx).isdigit() or not isinstance(node, dict):
                        continue
                    root = (
                        f"InternetGatewayDevice.WANDevice.{wd_idx}."
                        f"WANConnectionDevice.{cd_idx}.{kind}.{c_idx}"
                    )
                    vlan_path = None
                    for cand in (
                        f"{root}.X_VT_VLANID",
                        f"{root}.X_ZTE_VLAN",
                        f"{root}.VLANID",
                        f"{root}.X_HW_VLAN",
                    ):
                        if param_at(dev, cand) is not None:
                            vlan_path = cand
                            break
                    nat_path = f"{root}.NATEnabled"
                    if param_at(dev, nat_path) is None:
                        nat_path = None
                    profiles.append(
                        {
                            "root": root,
                            "kind": "ppp" if kind == "WANPPPConnection" else "ip",
                            "name": str_value(node.get("Name")),
                            "username": str_value(node.get("Username")),
                            "connection_status": str_value(node.get("ConnectionStatus")),
                            "external_ip": str_value(node.get("ExternalIPAddress")),
                            "vlan_path": vlan_path,
                            "nat_path": nat_path,
                            "nat_enabled": leaf(node.get("NATEnabled")),
                        }
                    )
    return profiles


DHCP_ROOT = "InternetGatewayDevice.LANDevice.1.LANHostConfigManagement"


def dhcp_paths() -> dict[str, str]:
    return {
        "enabled": f"{DHCP_ROOT}.DHCPServerEnable",
        "lanIp": "InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceIPAddress",
        "lanSubnetMask": "InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceSubnetMask",
        "subnetMask": f"{DHCP_ROOT}.SubnetMask",
        "minAddress": f"{DHCP_ROOT}.MinAddress",
        "maxAddress": f"{DHCP_ROOT}.MaxAddress",
        "dnsServers": f"{DHCP_ROOT}.DNSServers",
        "ipRouters": f"{DHCP_ROOT}.IPRouters",
        "leaseTime": f"{DHCP_ROOT}.DHCPLeaseTime",
    }


def extract_dhcp_lan(dev: dict[str, Any]) -> dict[str, Any] | None:
    node = dig(dev, "InternetGatewayDevice", "LANDevice", "1", "LANHostConfigManagement")
    if not isinstance(node, dict):
        return None
    paths = dhcp_paths()
    return {
        "root": DHCP_ROOT,
        "enabled": leaf(param_at(dev, paths["enabled"])),
        "lanIp": str_value(param_at(dev, paths["lanIp"])) or str_value(param_at(dev, paths["ipRouters"])),
        "subnetMask": str_value(param_at(dev, paths["lanSubnetMask"])) or str_value(param_at(dev, paths["subnetMask"])),
        "minAddress": str_value(param_at(dev, paths["minAddress"])),
        "maxAddress": str_value(param_at(dev, paths["maxAddress"])),
        "dnsServers": str_value(param_at(dev, paths["dnsServers"])),
        "leaseTime": leaf(param_at(dev, paths["leaseTime"])),
        "configurable": True,
        "writable": {k: True for k in ("enabled", "lanIp", "subnetMask", "minAddress", "maxAddress", "dnsServers", "leaseTime")},
    }


def extract_hosts(dev: dict[str, Any]) -> list[dict[str, Any]]:
    hosts_obj = dig(dev, "InternetGatewayDevice", "LANDevice", "1", "Hosts", "Host") or {}
    out: list[dict[str, Any]] = []
    if not isinstance(hosts_obj, dict):
        return out
    for idx, node in hosts_obj.items():
        if not str(idx).isdigit() or not isinstance(node, dict):
            continue
        out.append(
            {
                "index": int(idx),
                "hostname": str_value(node.get("HostName")),
                "ip": str_value(node.get("IPAddress")),
                "mac": str_value(node.get("MACAddress")),
                "active": leaf(node.get("Active")),
            }
        )
    return out


def extract_port_mappings(dev: dict[str, Any]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for profile in extract_wan_profiles(dev):
        root = str(profile["root"])
        pm = param_at(dev, f"{root}.PortMapping")
        if not isinstance(pm, dict):
            continue
        for idx, node in pm.items():
            if not str(idx).isdigit() or not isinstance(node, dict):
                continue
            mappings.append(
                {
                    "wanRoot": root,
                    "index": int(idx),
                    "root": f"{root}.PortMapping.{idx}",
                    "enabled": leaf(node.get("PortMappingEnabled")),
                    "externalPort": leaf(node.get("ExternalPort")),
                    "internalPort": leaf(node.get("InternalPort")),
                    "internalClient": str_value(node.get("InternalClient")),
                    "protocol": str_value(node.get("PortMappingProtocol")),
                    "description": str_value(node.get("PortMappingDescription")),
                }
            )
    return mappings


def extract_neighbor_networks(dev: dict[str, Any]) -> list[dict[str, Any]]:
    """Neighbors ZTE (WiFi/WIFI Radio) + Huawei NeighboringWiFiDiagnostic + Intelbras ITBS Result."""
    found: list[dict[str, Any]] = []

    def push(ssid: str, channel: Any, rssi: Any, *, vendor: str, path: str) -> None:
        if not ssid:
            return
        found.append(
            {
                "ssid": ssid,
                "channel": channel,
                "rssi": rssi,
                "vendor": vendor,
                "path": path,
            }
        )

    lan = dig(dev, "InternetGatewayDevice", "LANDevice", "1") or {}
    for wifi_key in ("WiFi", "WIFI"):
        radio = dig(lan, wifi_key, "Radio") if isinstance(lan, dict) else None
        if not isinstance(radio, dict):
            continue
        for ridx, rnode in radio.items():
            if not str(ridx).isdigit() or not isinstance(rnode, dict):
                continue
            for neigh_key in ("NeighboringWiFiDiagnostic", "X_ZTE_NeighboringWiFiDiagnostic", "SSID"):
                block = rnode.get(neigh_key)
                if not isinstance(block, dict):
                    continue
                result = block.get("Result") or block.get("NeighboringWiFiResult") or block
                if not isinstance(result, dict):
                    continue
                for nidx, nnode in result.items():
                    if not str(nidx).isdigit() or not isinstance(nnode, dict):
                        continue
                    push(
                        str_value(nnode.get("SSID") or nnode.get("ssid")),
                        leaf(nnode.get("Channel") or nnode.get("channel")),
                        leaf(nnode.get("SignalStrength") or nnode.get("RSSI") or nnode.get("rssi")),
                        vendor="zte",
                        path=f"InternetGatewayDevice.LANDevice.1.{wifi_key}.Radio.{ridx}.{neigh_key}.Result.{nidx}",
                    )

    # Huawei Device.WiFi.NeighboringWiFiDiagnostic.Result
    for base in (
        ("InternetGatewayDevice", "WiFi", "NeighboringWiFiDiagnostic", "Result"),
        ("Device", "WiFi", "NeighboringWiFiDiagnostic", "Result"),
    ):
        result = dig(dev, *base)
        if not isinstance(result, dict):
            continue
        for nidx, nnode in result.items():
            if not str(nidx).isdigit() or not isinstance(nnode, dict):
                continue
            push(
                str_value(nnode.get("SSID")),
                leaf(nnode.get("Channel")),
                leaf(nnode.get("SignalStrength")),
                vendor="huawei",
                path=".".join(base + (str(nidx),)),
            )

    # Intelbras X_ITBS result list
    itbs = dig(dev, "InternetGatewayDevice", "WiFi", "X_ITBS_NeighboringWiFiDiagnostic", "Result")
    if isinstance(itbs, dict):
        for nidx, nnode in itbs.items():
            if not str(nidx).isdigit() or not isinstance(nnode, dict):
                continue
            push(
                str_value(nnode.get("SSID")),
                leaf(nnode.get("Channel")),
                leaf(nnode.get("SignalStrength")),
                vendor="intelbras",
                path=f"InternetGatewayDevice.WiFi.X_ITBS_NeighboringWiFiDiagnostic.Result.{nidx}",
            )
    return found
