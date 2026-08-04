"""Extração de inventário GenieACS usando catálogo vendor→genérico."""

from __future__ import annotations

from typing import Any

from app.cpe.params import Cap, identity_from_device
from app.cpe.profiles import ALL_PROFILES, candidates_for, leaf_keys_for
from app.cpe.tree import (
    first_existing_path,
    iter_numeric_children,
    leaf,
    param_at,
    str_value,
)


def _vendor_tag(dev: dict[str, Any]) -> str:
    from app.cpe.profiles import profiles_for

    matched = profiles_for(dev)
    for p in matched:
        # primeiro perfil vendor (não generic)
        if p.id != "generic.igd":
            return p.id.split(".", 1)[0]
    return "generic"


def _node_field(node: dict[str, Any], keys: list[str]) -> Any:
    for k in keys:
        if k in node:
            return node.get(k)
    return None


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "enabled", "on"}
    return bool(value)


def extract_wifi_radios(dev: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ssid_keys = leaf_keys_for(dev, Cap.WIFI_SSID, "ssid") or ["SSID"]
    channel_keys = leaf_keys_for(dev, Cap.WIFI_CHANNEL, "channel") or ["Channel"]
    auto_channel_keys = leaf_keys_for(dev, Cap.WIFI_AUTO_CHANNEL, "auto_channel") or [
        "AutoChannelEnable"
    ]
    bandwidth_keys = leaf_keys_for(dev, Cap.WIFI_BANDWIDTH, "bandwidth") or [
        "Bandwidth",
        "OperatingChannelBandwidth",
    ]
    enable_keys = leaf_keys_for(dev, Cap.WIFI_ENABLE, "enable") or ["Enable"]
    for container_path in candidates_for(dev, Cap.WIFI_RADIO_CONTAINER):
        if "{" in container_path:
            continue
        block = param_at(dev, container_path)
        if not isinstance(block, dict):
            continue
        children = iter_numeric_children(block)
        radio_block = block.get("Radio") if isinstance(block.get("Radio"), dict) else None
        if radio_block and not children:
            children = iter_numeric_children(radio_block)
            base = f"{container_path}.Radio"
        else:
            base = container_path
        for idx, node in children:
            if not any(
                k in node
                for k in (
                    *ssid_keys,
                    *channel_keys,
                    *auto_channel_keys,
                    *bandwidth_keys,
                    *enable_keys,
                )
            ):
                continue
            root = f"{base}.{idx}"
            enable_node = _node_field(node, enable_keys)
            enabled = leaf(enable_node) if enable_node is not None else None
            auto_channel_node = _node_field(node, auto_channel_keys)
            out.append(
                {
                    "root": root,
                    "index": int(idx),
                    "ssid": str_value(_node_field(node, ssid_keys)),
                    "channel": str_value(_node_field(node, channel_keys)),
                    "autoChannel": _optional_bool(leaf(auto_channel_node)),
                    "bandwidth": str_value(_node_field(node, bandwidth_keys)),
                    "enabled": _optional_bool(enabled),
                    "container": container_path,
                }
            )
        if out:
            break
    return out


def extract_wan_profiles(dev: dict[str, Any]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    wan_roots = [p for p in candidates_for(dev, Cap.WAN_DEVICE) if "{" not in p]
    vlan_templates = candidates_for(dev, Cap.WAN_VLAN)
    nat_templates = candidates_for(dev, Cap.WAN_NAT)
    for wan_root in wan_roots:
        wan_device = param_at(dev, wan_root)
        if not isinstance(wan_device, dict):
            continue
        for wd_idx, wd in iter_numeric_children(wan_device):
            wan_instance_root = f"{wan_root}.{wd_idx}"
            conns = wd.get("WANConnectionDevice") or {}
            if not isinstance(conns, dict):
                continue
            for cd_idx, cd in iter_numeric_children(conns):
                for kind in ("WANPPPConnection", "WANIPConnection"):
                    block = cd.get(kind) or {}
                    if not isinstance(block, dict):
                        continue
                    for c_idx, node in iter_numeric_children(block):
                        root = f"{wan_root}.{wd_idx}.WANConnectionDevice.{cd_idx}.{kind}.{c_idx}"
                        vlan_path = first_existing_path(
                            dev,
                            [t.replace("{root}", root) for t in vlan_templates],
                        )
                        nat_path = first_existing_path(
                            dev,
                            [t.replace("{root}", root) for t in nat_templates],
                        )
                        username_path = first_existing_path(
                            dev,
                            [
                                candidate.replace("{root}", root)
                                for candidate in candidates_for(dev, Cap.WAN_USERNAME)
                            ],
                            require_value=True,
                        )
                        bytes_received_path, bytes_sent_path = wan_counter_paths(
                            dev,
                            connection_root=root,
                            wan_root=wan_instance_root,
                        )
                        profiles.append(
                            {
                                "root": root,
                                "kind": "ppp" if kind == "WANPPPConnection" else "ip",
                                "name": str_value(node.get("Name")),
                                "username": str_value(param_at(dev, username_path)) if username_path else "",
                                "connection_status": str_value(node.get("ConnectionStatus")),
                                "external_ip": str_value(node.get("ExternalIPAddress")),
                                "bytes_received": leaf(
                                    param_at(dev, bytes_received_path)
                                )
                                if bytes_received_path
                                else None,
                                "bytes_sent": leaf(param_at(dev, bytes_sent_path))
                                if bytes_sent_path
                                else None,
                                "vlan_path": vlan_path,
                                "nat_path": nat_path,
                                "nat_enabled": leaf(node.get("NATEnabled")),
                            }
                        )
        if profiles:
            break
    return profiles


def _optical_number(node: Any) -> float | int | None:
    """Converte telemetria numérica sem adivinhar escalas proprietárias."""
    value = leaf(node)
    if value is None or isinstance(value, bool):
        return None
    token = str(value).strip().replace(",", ".")
    if not token:
        return None
    # Alguns CPEs incluem a unidade no valor (ex.: "-21.4 dBm").
    token = token.split()[0]
    try:
        parsed = float(token)
    except ValueError:
        return None
    return int(parsed) if parsed.is_integer() else parsed


def _optical_field(dev: dict[str, Any], root: str, aliases: list[str]) -> Any:
    for alias in aliases:
        node = param_at(dev, f"{root}.{alias}")
        if leaf(node) is not None:
            return node
    return None


def extract_optical_telemetry(dev: dict[str, Any]) -> dict[str, Any] | None:
    """Extrai telemetria ONU/ONT reportada pelo CPE, sem expor paths na API."""
    fields = {
        name: leaf_keys_for(dev, Cap.OPTICAL_CONTAINER, name)
        for name in (
            "status",
            "technology",
            "rx_power",
            "tx_power",
            "distance",
            "temperature",
            "voltage",
            "bias",
            "fec",
            "hec",
            "crc",
        )
    }
    roots: list[str] = []
    for candidate in candidates_for(dev, Cap.OPTICAL_CONTAINER):
        block = param_at(dev, candidate)
        if not isinstance(block, dict):
            continue
        children = iter_numeric_children(block)
        roots.extend(f"{candidate}.{index}" for index, _ in children)
        roots.append(candidate)

    for root in roots:
        raw = {name: _optical_field(dev, root, aliases) for name, aliases in fields.items()}
        if not any(leaf(node) is not None for node in raw.values()):
            continue
        technology = str_value(raw["technology"])
        if not technology:
            technology = "GPON" if "gpon" in root.lower() else "Óptica"
        return {
            "detected": True,
            "technology": technology,
            "status": str_value(raw["status"]),
            "rxPowerDbm": _optical_number(raw["rx_power"]),
            "txPowerDbm": _optical_number(raw["tx_power"]),
            "distanceMeters": _optical_number(raw["distance"]),
            "temperatureC": _optical_number(raw["temperature"]),
            "voltageV": _optical_number(raw["voltage"]),
            "biasCurrentMa": _optical_number(raw["bias"]),
            "fecErrors": _optical_number(raw["fec"]),
            "hecErrors": _optical_number(raw["hec"]),
            "crcErrors": _optical_number(raw["crc"]),
        }
    return None


def wan_counter_paths(
    dev: dict[str, Any],
    *,
    connection_root: str,
    wan_root: str,
) -> tuple[str | None, str | None]:
    """Resolve os dois contadores sem expor os paths no contrato do workbench."""

    def resolve(capability: str) -> str | None:
        return first_existing_path(
            dev,
            [
                candidate.replace("{root}", connection_root).replace("{wan}", wan_root)
                for candidate in candidates_for(dev, capability)
                if "{interface}" not in candidate
            ],
            require_value=True,
        )

    return resolve(Cap.WAN_BYTES_RECEIVED), resolve(Cap.WAN_BYTES_SENT)


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
        "subnetMask": str_value(param_at(dev, paths["lanSubnetMask"]))
        or str_value(param_at(dev, paths["subnetMask"])),
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


def extract_lan_ports(dev: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista interfaces Ethernet LAN e preserva estado desconhecido como `None`."""
    aliases = {
        field: leaf_keys_for(dev, Cap.LAN_PORT_CONTAINER, field)
        for field in ("status", "enable", "rate", "duplex", "name")
    }
    for container in candidates_for(dev, Cap.LAN_PORT_CONTAINER):
        block = param_at(dev, container)
        if not isinstance(block, dict):
            continue
        ports: list[dict[str, Any]] = []
        for index, node in iter_numeric_children(block):
            values = {
                field: leaf(_node_field(node, field_aliases))
                for field, field_aliases in aliases.items()
            }
            enabled_raw = values["enable"]
            enabled = (
                enabled_raw.strip().lower() in {"1", "true", "yes", "enabled"}
                if isinstance(enabled_raw, str)
                else bool(enabled_raw)
                if enabled_raw is not None
                else None
            )
            ports.append(
                {
                    "index": int(index),
                    "name": str(values["name"] or f"LAN {index}"),
                    "status": str(values["status"] or ""),
                    "enabled": enabled,
                    "maxBitRate": str(values["rate"] or ""),
                    "duplexMode": str(values["duplex"] or ""),
                }
            )
        if ports:
            return ports
    return []


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
    def prefer(cap: str) -> str | None:
        cands = candidates_for(dev, cap)
        return first_existing_path(dev, cands) or (cands[0] if cands else None)

    return {
        "ping": prefer(Cap.PING_ROOT),
        "traceroute": prefer(Cap.TRACEROUTE_ROOT),
        "neighbor_start": first_existing_path(
            dev,
            _expand_result_templates(candidates_for(dev, Cap.NEIGHBOR_START), _radio_indexes(dev)),
            require_value=False,
        ),
        "igd": prefer(Cap.IGD_ROOT),
    }


def wifi_set_parameter_values(
    root: str,
    *,
    ssid: str | None = None,
    password: str | None = None,
    channel: int | None = None,
    bandwidth: str | None = None,
    enabled: bool | None = None,
    dev: dict[str, Any] | None = None,
) -> list[list[Any]]:
    """Monta SPV usando Cap.WIFI_SSID / Cap.WIFI_KEY do catálogo."""
    sample = dev or {}
    pvs: list[list[Any]] = []
    if ssid is not None:
        ssid_tmpls = candidates_for(sample, Cap.WIFI_SSID) or ["{root}.SSID"]
        pvs.append([ssid_tmpls[0].replace("{root}", root), str(ssid), "xsd:string"])
    if password:
        key_tmpls = candidates_for(sample, Cap.WIFI_KEY) or [
            "{root}.KeyPassphrase",
            "{root}.PreSharedKey.1.KeyPassphrase",
        ]
        for tmpl in key_tmpls:
            pvs.append([tmpl.replace("{root}", root), str(password), "xsd:string"])
    if channel is not None:
        auto_paths = [
            tmpl.replace("{root}", root)
            for tmpl in (
                candidates_for(sample, Cap.WIFI_AUTO_CHANNEL)
                or ["{root}.AutoChannelEnable"]
            )
        ]
        auto_path = first_existing_path(sample, auto_paths, require_value=False)
        if auto_path:
            pvs.append([auto_path, channel == 0, "xsd:boolean"])
    if channel is not None and channel > 0:
        paths = [
            tmpl.replace("{root}", root)
            for tmpl in (candidates_for(sample, Cap.WIFI_CHANNEL) or ["{root}.Channel"])
        ]
        path = first_existing_path(sample, paths, require_value=False) or paths[0]
        pvs.append([path, int(channel), "xsd:unsignedInt"])
    if bandwidth:
        paths = [
            tmpl.replace("{root}", root)
            for tmpl in (candidates_for(sample, Cap.WIFI_BANDWIDTH) or ["{root}.Bandwidth"])
        ]
        path = first_existing_path(sample, paths, require_value=False) or paths[0]
        value: Any = str(bandwidth)
        xsd = "xsd:string"
        if path.endswith("X_HW_HT20"):
            value = {"Auto": 0, "20MHz": 1, "40MHz": 2, "80MHz": 3, "160MHz": 4}.get(str(bandwidth), 0)
            xsd = "xsd:unsignedInt"
        pvs.append([path, value, xsd])
    if enabled is not None:
        paths = [
            tmpl.replace("{root}", root)
            for tmpl in (candidates_for(sample, Cap.WIFI_ENABLE) or ["{root}.Enable"])
        ]
        path = first_existing_path(sample, paths, require_value=False) or paths[0]
        pvs.append([path, bool(enabled), "xsd:boolean"])
    return pvs
