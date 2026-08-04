"""Device actions: catálogo de handlers (`@action`).

Veja `docs/device-actions.md`.
"""

from __future__ import annotations

from app.acs.actions import (  # noqa: F401 — side-effect: @action register
    dhcp,
    diagnostic,
    inventory,
    portmap,
    power,
    tags,
    tools,
    traffic,
    wan,
    wifi,
)
from app.acs.actions.base import (
    ActionContext,
    ActionSpec,
    dispatch,
    get_action,
    list_actions,
)

_LOADED = True


def ensure_handlers_loaded() -> None:
    """No-op após import deste pacote (handlers já registrados)."""
    return


__all__ = [
    "ActionContext",
    "ActionSpec",
    "dispatch",
    "ensure_handlers_loaded",
    "get_action",
    "list_actions",
]
