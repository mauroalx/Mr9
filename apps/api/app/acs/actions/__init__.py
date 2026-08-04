"""Device actions: catálogo de handlers (`@action`).

Veja `docs/device-actions.md`.
"""

from __future__ import annotations

from app.acs.actions.base import (
    ActionContext,
    ActionSpec,
    dispatch,
    get_action,
    list_actions,
)
from app.acs.actions import (  # noqa: F401 — side-effect: @action register
    dhcp,
    diagnostic,
    inventory,
    portmap,
    power,
    tags,
    tools,
    wan,
    wifi,
)

_LOADED = True


def ensure_handlers_loaded() -> None:
    """No-op após import deste pacote (handlers já registrados)."""
    return None


__all__ = [
    "ActionContext",
    "ActionSpec",
    "dispatch",
    "ensure_handlers_loaded",
    "get_action",
    "list_actions",
]
