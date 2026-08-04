"""Resolução de contadores WAN para amostragem de tráfego."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.cpe.extract import extract_wan_profiles, wan_counter_paths
from app.cpe.params import Cap
from app.cpe.profiles import candidates_for
from app.cpe.tree import first_existing_path, iter_numeric_children, leaf, param_at


@dataclass(frozen=True)
class TrafficCounters:
    received_bytes: int | None
    sent_bytes: int | None
    refresh_root: str
    updated_at: str | None = None

    @property
    def available(self) -> bool:
        return self.received_bytes is not None and self.sent_bytes is not None


def _counter(value: Any) -> int | None:
    raw = leaf(value)
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _latest_timestamp(*values: Any) -> str | None:
    timestamps = [
        str(value.get("_timestamp"))
        for value in values
        if isinstance(value, dict) and value.get("_timestamp")
    ]
    return max(timestamps) if timestamps else None


def _wan_root(path: str) -> str:
    match = re.match(r"^(InternetGatewayDevice\.WANDevice\.\d+)", path)
    return match.group(1) if match else "InternetGatewayDevice.WANDevice.1"


def _refresh_root(paths: list[str | None], default: str) -> str:
    parents = [path.rsplit(".", 1)[0] for path in paths if path and "." in path]
    if not parents:
        return default
    common = parents[0].split(".")
    for parent in parents[1:]:
        parts = parent.split(".")
        shared = 0
        while shared < min(len(common), len(parts)) and common[shared] == parts[shared]:
            shared += 1
        common = common[:shared]
    return ".".join(common) or default


def traffic_projection() -> list[str]:
    return [
        "_deviceId",
        "InternetGatewayDevice.WANDevice",
        *[path for path in candidates_for({}, Cap.WAN_TRAFFIC_INTERFACE) if "{" not in path],
    ]


def primary_traffic_counters(dev: dict[str, Any]) -> TrafficCounters:
    """Usa a primeira WAN existente; o índice não precisa começar em 1."""
    profiles = extract_wan_profiles(dev)
    if profiles:
        primary = profiles[0]
        connection_root = str(primary.get("root") or "")
        wan_root = _wan_root(connection_root)
        received_path, sent_path = wan_counter_paths(
            dev,
            connection_root=connection_root,
            wan_root=wan_root,
        )
        return TrafficCounters(
            received_bytes=_counter(primary.get("bytes_received")),
            sent_bytes=_counter(primary.get("bytes_sent")),
            refresh_root=_refresh_root([received_path, sent_path], wan_root),
            updated_at=_latest_timestamp(
                param_at(dev, received_path),
                param_at(dev, sent_path),
            ),
        )

    wan_containers = candidates_for(dev, Cap.WAN_DEVICE)
    for container in wan_containers:
        node = param_at(dev, container)
        if not isinstance(node, dict):
            continue
        for index, _ in iter_numeric_children(node):
            root = f"{container}.{index}"
            received_path = first_existing_path(
                dev,
                [
                    candidate.replace("{wan}", root)
                    for candidate in candidates_for(dev, Cap.WAN_BYTES_RECEIVED)
                    if "{root}" not in candidate
                ],
                require_value=True,
            )
            sent_path = first_existing_path(
                dev,
                [
                    candidate.replace("{wan}", root)
                    for candidate in candidates_for(dev, Cap.WAN_BYTES_SENT)
                    if "{root}" not in candidate
                ],
                require_value=True,
            )
            if received_path or sent_path:
                return TrafficCounters(
                    received_bytes=_counter(param_at(dev, received_path)) if received_path else None,
                    sent_bytes=_counter(param_at(dev, sent_path)) if sent_path else None,
                    refresh_root=_refresh_root([received_path, sent_path], root),
                    updated_at=_latest_timestamp(
                        param_at(dev, received_path),
                        param_at(dev, sent_path),
                    ),
                )

    for container in candidates_for(dev, Cap.WAN_TRAFFIC_INTERFACE):
        node = param_at(dev, container)
        if not isinstance(node, dict):
            continue
        for index, _ in iter_numeric_children(node):
            interface_root = f"{container}.{index}"
            received_path = first_existing_path(
                dev,
                [
                    candidate.replace("{interface}", interface_root)
                    for candidate in candidates_for(dev, Cap.WAN_BYTES_RECEIVED)
                    if "{interface}" in candidate
                ],
                require_value=True,
            )
            sent_path = first_existing_path(
                dev,
                [
                    candidate.replace("{interface}", interface_root)
                    for candidate in candidates_for(dev, Cap.WAN_BYTES_SENT)
                    if "{interface}" in candidate
                ],
                require_value=True,
            )
            if received_path or sent_path:
                return TrafficCounters(
                    received_bytes=_counter(param_at(dev, received_path)) if received_path else None,
                    sent_bytes=_counter(param_at(dev, sent_path)) if sent_path else None,
                    refresh_root=_refresh_root([received_path, sent_path], interface_root),
                    updated_at=_latest_timestamp(
                        param_at(dev, received_path),
                        param_at(dev, sent_path),
                    ),
                )
    return TrafficCounters(None, None, "InternetGatewayDevice.WANDevice.1")
