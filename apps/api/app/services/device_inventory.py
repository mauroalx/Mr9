"""Construção de consultas do inventário ACS."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from app.cpe.search import wan_inventory_query_fields


def build_inventory_query(
    *,
    q: str | None = None,
    online: bool | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
    firmware: str | None = None,
    tag: str | None = None,
    now: datetime,
    online_threshold_s: int,
) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = []
    if q and q.strip():
        search = re.escape(q.strip())
        fields = [
            "_deviceId._SerialNumber",
            "_deviceId._ProductClass",
            "_deviceId._Manufacturer",
            "_id",
            *wan_inventory_query_fields(),
        ]
        clauses.append({"$or": [{field: {"$regex": search, "$options": "i"}} for field in fields]})
    for field, value in (
        ("_deviceId._Manufacturer", manufacturer),
        ("_deviceId._ProductClass", model),
        ("InternetGatewayDevice.DeviceInfo.SoftwareVersion._value", firmware),
        ("_tags", tag),
    ):
        if value and value.strip():
            clauses.append({field: value.strip()})
    if online is not None:
        cutoff = (now - timedelta(seconds=online_threshold_s)).strftime("%Y-%m-%d %H:%M:%S %z")
        clauses.append(
            {"_lastInform": {"$gte": cutoff}}
            if online
            else {
                "$or": [
                    {"_lastInform": {"$lt": cutoff}},
                    {"_lastInform": {"$exists": False}},
                ]
            }
        )
    if not clauses:
        return {}
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}
