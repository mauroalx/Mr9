"""ACS device actions — um handler por ação, registrados no catálogo.

Como contribuir: veja `docs/device-actions.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.deps import AuthContext
from app.integrations.acs.genieacs_client import GenieAcsClient, GenieAcsResponse
from app.models.acs_server import AcsServer


@dataclass
class ActionContext:
    device_id: str
    params: dict[str, Any]
    client: GenieAcsClient
    db: Session
    auth: AuthContext
    server: AcsServer
    _device_cache: dict[str, Any] | None = None

    async def load_device(self, *, projection: list[str] | None = None) -> dict[str, Any]:
        """Carrega inventário uma vez por request (cache em memória do contexto)."""
        if self._device_cache is not None and projection is None:
            return self._device_cache
        dev = await self.client.get_device(self.device_id, projection=projection) or {}
        if projection is None:
            self._device_cache = dev
        return dev


HandlerFn = Callable[[ActionContext], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ActionSpec:
    name: str
    handler: HandlerFn
    permission: str | None = None
    notes: str = ""


_REGISTRY: dict[str, ActionSpec] = {}


def action(name: str, *, permission: str | None = None, notes: str = "") -> Callable[[HandlerFn], HandlerFn]:
    def decorator(fn: HandlerFn) -> HandlerFn:
        key = name.strip()
        if key in _REGISTRY:
            raise RuntimeError(f"Action duplicada: {key}")
        _REGISTRY[key] = ActionSpec(name=key, handler=fn, permission=permission, notes=notes)
        return fn

    return decorator


def get_action(name: str) -> ActionSpec | None:
    return _REGISTRY.get(name.strip())


def list_actions() -> list[ActionSpec]:
    return sorted(_REGISTRY.values(), key=lambda s: s.name)


async def dispatch(ctx: ActionContext, action_name: str) -> dict[str, Any]:
    from app.acs.actions import ensure_handlers_loaded

    ensure_handlers_loaded()
    spec = get_action(action_name)
    if not spec:
        known = ", ".join(a.name for a in list_actions()) or "(nenhuma)"
        raise HTTPException(status_code=422, detail=f"Action não suportada: {action_name}. Conhecidas: {known}")
    if spec.permission:
        ctx.auth.require(spec.permission)
    return await spec.handler(ctx)


def task_result(res: GenieAcsResponse, *, ok_codes: set[int] | None = None) -> dict[str, Any]:
    """Normaliza resposta de create_task / tags."""
    codes = ok_codes or {200, 202}
    return {
        "ok": res.status_code in codes,
        "http": res.status_code,
        "queued": res.status_code == 202,
    }


async def set_parameter_values(
    client: GenieAcsClient,
    device_id: str,
    parameter_values: list[list[Any]],
    *,
    timeout_ms: int = 25000,
) -> dict[str, Any]:
    res = await client.create_task(
        device_id,
        {"name": "setParameterValues", "parameterValues": parameter_values},
        connection_request=True,
        timeout_ms=timeout_ms,
    )
    return task_result(res)


async def create_named_task(
    ctx: ActionContext,
    payload: dict[str, Any],
    *,
    timeout_ms: int = 25000,
    connection_request: bool = True,
    ok_codes: set[int] | None = None,
) -> dict[str, Any]:
    res = await ctx.client.create_task(
        ctx.device_id,
        payload,
        connection_request=connection_request,
        timeout_ms=timeout_ms,
    )
    return task_result(res, ok_codes=ok_codes)


def require_str(params: dict[str, Any], key: str, *, detail: str | None = None) -> str:
    value = str(params.get(key) or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail=detail or f"{key} obrigatório")
    return value
