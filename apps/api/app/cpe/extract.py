"""Extração de inventário GenieACS usando catálogo vendor→genérico."""

from __future__ import annotations

from typing import Any

from app.cpe.params import Cap, identity_from_device
from app.cpe.profiles import ALL_PROFILES, candidates_for, leaf_keys_for
from app.cpe.tree import (
    dig,
    first_existing_path,
    iter_numeric_children,
    leaf,
    param_at,
    str_value,
)


def _vendor_tag(dev: dict[str, Any]) -> str:
    ident = identity_from_device(dev)
    m = ident.manufacturer_l
    if "zte" in m:
        return "zte"
    if "huawei" in m:
        return "huawei"
    if "intelbras" in m:
        return "intelbras"
    return m or "generic"


def extract_wifi_radios(dev: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for container_path in candidates_for(dev, Cap.WIFI_RADIO_CONTAINER):
        if "{" in container_path:
            continue
        block = param_at(dev, container_path)
        if not isinstance(block, dict):
            continue
        # WLANConfiguration: índices = SSIDs. WiFi/WIFI: pode ter Radio + SSIDs.
        children = iter_numeric_children(block)
        radio_block = block.get("Radio") if isinstance(block.get("Radio"), dict) else None
        if radio_block and not children:
            children = iter_numeric_children(radio_block)
            base = f"{container_path}.Radio"
        else:
            base = container_path
        for idx, node in children:
            # Skip non-SSID objects under WiFi (e.g. NeighboringWiFiDiagnostic as sibling)
            if "SSID" not in node and "Channel" not in node and "Enable" not in node:
                continue
            root = f"{base}.{idx}"
            out.append(
                {
                    "root": root,
                    "index": int(idx),
                    "ssid": str_value(node.get("SSID")),
                    "channel": str_value(node.get("Channel")),
                    "enabled": bool(leaf(node.get("Enable"))) if node.get("Enable") is not None else None,
                    "container": container_path,
                }
            )
        if out:
            break  # primeiro container que renderizou vence (específico→genérico)
    return out


def extract_wan_profiles(dev: dict[str, Any]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    wan_device = dig(dev, "InternetGatewayDevice", "WANDevice") or {}
    if not isinstance(wan_device, dict):
        return profiles
    vlan_templates = candidates_for(dev, Cap.WAN_VLAN)
    nat_templates = candidates_for(dev, Cap.WAN_NAT)
    for wd_idx, wd in iter_numeric_children(wan_device):
        conns = wd.get("WANConnectionDevice") or {}
        if not isinstance(conns, dict):
            continue
        for cd_idx, cd in iter_numeric_children(conns):
            for kind in ("WANPPPConnection", "WANIPConnection"):
                block = cd.get(kind) or {}
                if not isinstance(block, dict):
                    continue
                for c_idx, node in iter_numeric_children(block):
                    root = (
                        f"InternetGatewayDevice.WANDevice.{wd_idx}."
                        f"WANConnectionDevice.{cd_idx}.{kind}.{c_idx}"
                    )
                    vlan_path = first_existing_path(
                        dev,
                        [t.replace("{root}", root) for t in vlan_templates],
                    )
                    nat_path = first_existing_path(
                        dev,
                        [t.replace("{root}", root) for t in nat_templates],
                    )
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


def dhcp_paths(dev: dict[str, Any] | None = None) -> dict[str, str]:
    """Resolve paths DHCP (específico→genérico). Sem device usa só o perfil generic."""
    from app.cpe.params import DeviceIdentity, resolve_candidates

    sample = dev if isinstance(dev, dict) else {}
    ident = identity_from_device(sample) if sample else DeviceIdentity("", "")

    def first(cap: str) -> str:
        cands = resolve_candidates(ident, cap, ALL_PROFILES)
        if not cands:
            raise KeyError(f"Sem candidatos para {cap}")
        return cands[0]

    subnet = resolve_candidates(ident, Cap.DHCP_SUBNET, ALL_PROFILES)
    return {
        "enabled": first(Cap.DHCP_ENABLE),
        "lanIp": first(Cap.DHCP_LAN_IP),
        "lanSubnetMask": subnet[0],
        "subnetMask": subnet[1] if len(subnet) > 1 else subnet[0],
        "minAddress": first(Cap.DHCP_MIN),
        "maxAddress": first(Cap.DHCP_MAX),
        "dnsServers": first(Cap.DHCP_DNS),
        "ipRouters": first(Cap.DHCP_ROUTERS),
        "leaseTime": first(Cap.DHCP_LEASE),
        "root": first(Cap.DHCP_ROOT),
    }


def extract_dhcp_lan(dev: dict[str, Any]) -> dict[str, Any] | None:
    paths = dhcp_paths(dev)
    node = param_at(dev, paths["root"])
    if not isinstance(node, dict):
        return None
    return {
        "root": paths["root"],
        "enabled": leaf(param_at(dev, paths["enabled"])),
        "lanIp": str_value(param_at(dev, paths["lanIp"])) or str_value(param_at(dev, paths["ipRouters"])),
        "subnetMask": str_value(param_at(dev, paths["lanSubnetMask"])) or str_value(param_at(dev, paths["subnetMask"])),
        "minAddress": str_value(param_at(dev, paths["minAddress"])),
        "maxAddress": str_value(param_at(dev, paths["maxAddress"])),
        "dnsServers": str_value(param_at(dev, paths["dnsServers"])),
        "leaseTime": leaf(param_at(dev, paths["leaseTime"])),
        "configurable": True,
        "writable": {
            k: True
            for k in ("enabled", "lanIp", "subnetMask", "minAddress", "maxAddress", "dnsServers", "leaseTime")
        },
        "paths": paths,
    }


def extract_hosts(dev: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for container in candidates_for(dev, Cap.HOSTS_CONTAINER):
        hosts_obj = param_at(dev, container)
        if not isinstance(hosts_obj, dict):
            continue
        for idx, node in iter_numeric_children(hosts_obj):
            out.append(
                {
                    "index": int(idx),
                    "hostname": str_value(node.get("HostName")),
                    "ip": str_value(node.get("IPAddress")),
                    "mac": str_value(node.get("MACAddress")),
                    "active": leaf(node.get("Active")),
                }
            )
        if out:
            break
    return out


def extract_port_mappings(dev: dict[str, Any]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for profile in extract_wan_profiles(dev):
        root = str(profile["root"])
        pm = param_at(dev, f"{root}.PortMapping")
        if not isinstance(pm, dict):
            continue
        for idx, node in iter_numeric_children(pm):
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


def _pick_leaf(node: dict[str, Any], keys: list[str]) -> Any:
    for k in keys:
        if k in node:
            return leaf(node.get(k))
    return None


def _expand_result_templates(templates: list[str], radio_indexes: list[str]) -> list[str]:
    expanded: list[str] = []
    for t in templates:
        if "{i}" in t:
            for i in radio_indexes or ["1"]:
                expanded.append(t.replace("{i}", i))
        else:
            expanded.append(t)
    return expanded


def _radio_indexes(dev: dict[str, Any]) -> list[str]:
    idxs: list[str] = []
    for container in candidates_for(dev, Cap.WIFI_RADIO_CONTAINER):
        block = param_at(dev, container)
        if not isinstance(block, dict):
            continue
        radio = block.get("Radio")
        if isinstance(radio, dict):
            idxs.extend(i for i, _ in iter_numeric_children(radio))
        if idxs:
            break
    return idxs or ["1"]


def extract_neighbor_networks(dev: dict[str, Any]) -> list[dict[str, Any]]:
    """Lê Result.* usando candidatos specific→generic do catálogo."""
    from app.cpe.profiles import discovery_candidates

    found: list[dict[str, Any]] = []
    seen: set[tuple[str, Any, Any]] = set()
    vendor = _vendor_tag(dev)
    templates = candidates_for(dev, Cap.NEIGHBOR_RESULT)
    ssid_keys = leaf_keys_for(dev, Cap.NEIGHBOR_RESULT, "ssid") or ["SSID"]
    ch_keys = leaf_keys_for(dev, Cap.NEIGHBOR_RESULT, "channel") or ["Channel"]
    rssi_keys = leaf_keys_for(dev, Cap.NEIGHBOR_RESULT, "rssi") or ["SignalStrength"]

    def harvest(path_list: list[str]) -> None:
        for result_path in _expand_result_templates(path_list, _radio_indexes(dev)):
            result = param_at(dev, result_path)
            if not isinstance(result, dict):
                continue
            for nidx, nnode in iter_numeric_children(result):
                ssid = str(_pick_leaf(nnode, ssid_keys) or "")
                if not ssid:
                    continue
                channel = _pick_leaf(nnode, ch_keys)
                rssi = _pick_leaf(nnode, rssi_keys)
                key = (ssid, channel, rssi)
                if key in seen:
                    continue
                seen.add(key)
                found.append(
                    {
                        "ssid": ssid,
                        "channel": channel,
                        "rssi": rssi,
                        "vendor": vendor,
                        "path": f"{result_path}.{nidx}",
                        "profile_hint": path_list[0] if path_list else "",
                    }
                )

    harvest(templates)
    # Sem Manufacturer no inventário (ou CPE misto): tenta discovery de todos os vendors.
    if not found:
        harvest(discovery_candidates(Cap.NEIGHBOR_RESULT))
    return found


def diag_roots(dev: dict[str, Any]) -> dict[str, str | None]:
    return {
        "ping": first_existing_path(dev, candidates_for(dev, Cap.PING_ROOT))
        or (candidates_for(dev, Cap.PING_ROOT) or [None])[0],
        "traceroute": first_existing_path(dev, candidates_for(dev, Cap.TRACEROUTE_ROOT))
        or (candidates_for(dev, Cap.TRACEROUTE_ROOT) or [None])[0],
        "neighbor_start": first_existing_path(
            dev,
            _expand_result_templates(candidates_for(dev, Cap.NEIGHBOR_START), _radio_indexes(dev)),
            require_value=False,
        ),
    }


def wifi_set_parameter_values(root: str, *, ssid: str | None = None, password: str | None = None) -> list[list[Any]]:
    pvs: list[list[Any]] = []
    if ssid is not None:
        pvs.append([f"{root}.SSID", str(ssid), "xsd:string"])
    if password:
        # genérico: tenta KeyPassphrase + PreSharedKey
        for leaf_path in (
            f"{root}.KeyPassphrase",
            f"{root}.PreSharedKey.1.KeyPassphrase",
        ):
            pvs.append([leaf_path, str(password), "xsd:string"])
    return pvs
