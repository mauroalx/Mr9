"""Campos de busca do inventário derivados do catálogo de perfis CPE."""

from __future__ import annotations

from app.cpe.params import Cap
from app.cpe.profiles import discovery_candidates

# A extração de um CPE carregado percorre todos os índices existentes. Esta
# matriz compacta vale somente para a query do NBI: expansões cartesianas
# extensas excedem o limite HTTP do GenieACS. Casos especiais entram como
# candidatos absolutos nos perfis modelo → vendor → generic.
GENERIC_WAN_ROOT_INDEXES = (
    (1, 1, 1),
    (1, 1, 2),
    (1, 1, 3),
    (1, 2, 1),
)


def _expanded_wan_fields(candidates: list[str]) -> list[str]:
    wan_containers = discovery_candidates(Cap.WAN_DEVICE)
    fields: list[str] = []
    for candidate in candidates:
        if "{root}" not in candidate:
            fields.append(candidate)
            continue
        for container in wan_containers:
            if "{" in container:
                continue
            for wan_index, connection_index, ppp_index in GENERIC_WAN_ROOT_INDEXES:
                root = (
                    f"{container}.{wan_index}.WANConnectionDevice."
                    f"{connection_index}.WANPPPConnection.{ppp_index}"
                )
                fields.append(candidate.replace("{root}", root))
    return fields


def wan_username_query_fields() -> list[str]:
    """Campos PPPoE pesquisáveis: aliases especiais primeiro, TR-098 depois."""
    candidates = discovery_candidates(Cap.WAN_USERNAME)
    fields = _expanded_wan_fields(candidates)
    return list(dict.fromkeys(field if field.endswith("._value") else f"{field}._value" for field in fields))


def wan_inventory_query_fields() -> list[str]:
    """Username e IP de qualquer perfil PPP dentro da janela de descoberta."""
    return list(
        dict.fromkeys(
            [
                *wan_username_query_fields(),
                *_expanded_wan_fields(["{root}.ExternalIPAddress._value"]),
            ]
        )
    )
