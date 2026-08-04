"""Amostragem de contadores WAN acumulados."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.acs.actions.base import ActionContext, action, task_result
from app.cpe.traffic import primary_traffic_counters, traffic_projection


@action(
    "traffic_sample",
    permission="acs.access",
    notes="Atualiza e lê os contadores da primeira WAN",
    audit=False,
)
async def traffic_sample(ctx: ActionContext) -> dict[str, Any]:
    projection = traffic_projection()
    current = primary_traffic_counters(await ctx.load_device(projection=projection))
    pending = await ctx.client.list_tasks(
        query={
            "device": ctx.device_id,
            "name": "refreshObject",
            "objectName": current.refresh_root,
        },
        limit=1,
    )
    if pending:
        refresh_status = "queued"
    else:
        refresh = await ctx.client.create_task(
            ctx.device_id,
            {"name": "refreshObject", "objectName": current.refresh_root},
            connection_request=True,
            timeout_ms=4500,
        )
        task = task_result(refresh)
        refresh_status = "completed" if task["ok"] and not task["queued"] else "queued" if task["ok"] else "failed"
    refreshed = await ctx.client.get_device(ctx.device_id, projection=projection)
    counters = primary_traffic_counters(refreshed or {})
    return {
        "available": counters.available,
        "received_bytes": counters.received_bytes,
        "sent_bytes": counters.sent_bytes,
        "sampled_at": datetime.now(UTC).isoformat(),
        "counter_updated_at": counters.updated_at,
        "refresh_status": refresh_status,
    }
