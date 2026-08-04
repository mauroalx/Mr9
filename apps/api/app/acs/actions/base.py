"""ACS device actions — um handler por ação, registrados no catálogo.

Como contribuir:
1. Crie/edite um módulo em `app/acs/actions/` (ex.: `wifi.py`)
2. Decore com `@action("nome", permission="acs.devices.write", notes="...")`
3. Importe o módulo em `app/acs/actions/__init__.py`
4. Teste unitário do handler (params → tasks) quando houver lógica não trivial

A rota FastAPI só autentica, resolve o ACS e chama `dispatch()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.deps import AuthContext
from app.integrations.acs.genieacs_client import GenieAcsClient
from app.models.acs_server import AcsServer


@dataclass
class ActionContext:
    device_id: str
    params: dict[str, Any]
    client: GenieAcsClient
    db: Session
    auth: AuthContext
    server: AcsServer


HandlerFn = Callable[[ActionContext], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ActionSpec:
    name: str
    handler: HandlerFn
    # Permissão além de `acs.access` (já exigida na rota). None = só leitura ACS.
    permission: str | None = None
    notes: str = ""


_REGISTRY: dict[str, ActionSpec] = {}


def action(name: str, *, permission: str | None = None, notes: str = "") -> Callable[[HandlerFn], HandlerFn]:
    """Registra um handler. Nome = valor de `body.action` na API."""

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
    return {
        "ok": res.status_code in {200, 202},
        "http": res.status_code,
        "queued": res.status_code == 202,
    }


def require_str(params: dict[str, Any], key: str, *, detail: str | None = None) -> str:
    value = str(params.get(key) or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail=detail or f"{key} obrigatório")
    return value
