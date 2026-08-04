"""Tags GenieACS (_tags)."""

from __future__ import annotations

from typing import Any

from app.acs.actions.base import ActionContext, action, require_str, task_result


@action("tags_add", permission="acs.devices.write", notes="POST /devices/{id}/tags/{tag}")
async def tags_add(ctx: ActionContext) -> dict[str, Any]:
    tag = require_str(ctx.params, "tag", detail="tag obrigatória")
    res = await ctx.client.set_tag(ctx.device_id, tag)
    return task_result(res, ok_codes={200, 204})


@action("tags_remove", permission="acs.devices.write", notes="DELETE /devices/{id}/tags/{tag}")
async def tags_remove(ctx: ActionContext) -> dict[str, Any]:
    tag = require_str(ctx.params, "tag", detail="tag obrigatória")
    res = await ctx.client.delete_tag(ctx.device_id, tag)
    return task_result(res, ok_codes={200, 204})
