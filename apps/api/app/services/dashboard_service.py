"""Coleta de métricas ACS usadas pelo dashboard."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from app.integrations.acs.genieacs_client import GenieAcsClient


async def collect_acs_metrics(
    client: GenieAcsClient,
    *,
    now: datetime,
    online_threshold_s: int,
    manufacturer_groups: list[dict[str, str]],
) -> dict[str, Any]:
    """Obtém contagens globais sem transferir documentos da coleção."""
    cutoff = (now - timedelta(seconds=online_threshold_s)).strftime("%Y-%m-%d %H:%M:%S %z")
    cutoff_24h = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S %z")
    total, online, informed_24h, firmware_known = await asyncio.gather(
        client.count_devices(query={}),
        client.count_devices(query={"_lastInform": {"$gte": cutoff}}),
        client.count_devices(query={"_lastInform": {"$gte": cutoff_24h}}),
        client.count_devices(
            query={"InternetGatewayDevice.DeviceInfo.SoftwareVersion._value": {"$exists": True}}
        ),
    )
    vendor_counts = await asyncio.gather(
        *[
            client.count_devices(
                query={
                    "_deviceId._Manufacturer": {
                        "$regex": group["pattern"],
                        "$options": "i",
                    }
                }
            )
            for group in manufacturer_groups
        ]
    )
    manufacturers = [
        {"name": group["label"], "count": count}
        for group, count in zip(manufacturer_groups, vendor_counts, strict=True)
        if count
    ]
    identified = sum(vendor_counts)
    if total > identified:
        manufacturers.append({"name": "Outros", "count": total - identified})
    return {
        "total": total,
        "online": online,
        "offline": max(total - online, 0),
        "stale_24h": max(total - informed_24h, 0),
        "firmware_known": firmware_known,
        "manufacturers": manufacturers,
    }
