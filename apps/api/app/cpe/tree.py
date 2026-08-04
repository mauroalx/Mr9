"""Helpers de árvore GenieACS (valores `_value` / paths ponteados)."""

from __future__ import annotations

from typing import Any


def leaf(node: Any) -> Any:
    if isinstance(node, dict):
        # Nós de parâmetros do GenieACS carregam metadados (`_object`,
        # `_writable`, `_type` etc.). Sem `_value`, o CPE não informou um
        # valor escalar; nunca exponha o dicionário de metadados como dado.
        return node.get("_value") if "_value" in node else None
    return node


def dig(obj: Any, *parts: str) -> Any:
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def param_at(dev: dict[str, Any], dotted: str) -> Any:
    parts = [p for p in dotted.split(".") if p]
    return dig(dev, *parts)


def str_value(node: Any) -> str:
    v = leaf(node)
    return "" if v is None else str(v)


def param_exists(dev: dict[str, Any], dotted: str, *, require_value: bool = False) -> bool:
    """True se o nó existe na árvore.

    GenieACS às vezes deixa stub `{_writable: True}` sem `_value`.
    Por padrão `require_value=False` — necessário para plans Huawei/scan.
    """
    node = param_at(dev, dotted)
    if node is None:
        return False
    if not require_value:
        return True
    if isinstance(node, dict):
        return "_value" in node
    return True


def first_existing_path(
    dev: dict[str, Any],
    candidates: list[str],
    *,
    require_value: bool = False,
) -> str | None:
    for path in candidates:
        # Templates com placeholders não existem até expansão
        if "{" in path:
            continue
        if param_exists(dev, path, require_value=require_value):
            return path
    return None


def expand_indexed(template: str, **indexes: int) -> str:
    return template.format(**indexes)


def iter_numeric_children(node: Any) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(node, dict):
        return []
    out: list[tuple[str, dict[str, Any]]] = []
    for k, v in node.items():
        if str(k).isdigit() and isinstance(v, dict):
            out.append((str(k), v))
    return sorted(out, key=lambda item: int(item[0]))
