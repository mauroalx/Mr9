"""Registro de perfis vendor/modelo + genérico.

Para adicionar um vendor:
1. Crie `app/cpe/profiles/<vendor>.py` exportando `PROFILES`
2. Importe e concatene em `ALL_PROFILES` abaixo
3. Teste em `tests/test_cpe_params_registry.py`
4. Veja `docs/vendor-paths.md`
"""

from __future__ import annotations

from typing import Any

from app.cpe.params import (
    Cap,
    DeviceIdentity,
    PathFamily,
    VendorProfile,
    identity_from_device,
    matching_profiles,
    resolve_candidates,
    resolve_candidates_discovery,
    resolve_family,
    resolve_leaf_keys,
)
from app.cpe.profiles import fiberhome as fiberhome_mod
from app.cpe.profiles import generic as generic_mod
from app.cpe.profiles import huawei as huawei_mod
from app.cpe.profiles import intelbras as intelbras_mod
from app.cpe.profiles import zte as zte_mod

# Ordem na tupla não importa — a resolução ordena por `priority`.
ALL_PROFILES: tuple[VendorProfile, ...] = (
    *zte_mod.PROFILES,
    *huawei_mod.PROFILES,
    *intelbras_mod.PROFILES,
    *fiberhome_mod.PROFILES,
    generic_mod.GENERIC,
)

_MANUFACTURER_LABELS = {
    "zte": "ZTE",
    "huawei": "Huawei",
    "intelbras": "Intelbras",
    "fiberhome": "FiberHome",
}


def manufacturer_distribution_groups() -> list[dict[str, str]]:
    """Grupos conhecidos para contagem exata no dashboard."""
    vendor_ids = {profile.id.split(".", 1)[0] for profile in ALL_PROFILES if profile.id != "generic.igd"}
    return [
        {
            "id": vendor_id,
            "label": _MANUFACTURER_LABELS.get(vendor_id, vendor_id.title()),
            "pattern": vendor_id,
        }
        for vendor_id in sorted(vendor_ids)
    ]


def profiles_for(dev: dict[str, Any]) -> list[VendorProfile]:
    return matching_profiles(identity_from_device(dev), ALL_PROFILES)


def candidates_for(dev: dict[str, Any], capability: str) -> list[str]:
    return resolve_candidates(identity_from_device(dev), capability, ALL_PROFILES)


def discovery_candidates(capability: str) -> list[str]:
    return resolve_candidates_discovery(capability, ALL_PROFILES)


def family_for(dev: dict[str, Any], capability: str) -> PathFamily | None:
    return resolve_family(identity_from_device(dev), capability, ALL_PROFILES)


def leaf_keys_for(dev: dict[str, Any], capability: str, field: str) -> list[str]:
    return resolve_leaf_keys(identity_from_device(dev), capability, field, ALL_PROFILES)


def describe_resolution(dev: dict[str, Any], capability: str) -> dict[str, Any]:
    """Debug/contrib: mostra identidade + cadeia de perfis + candidatos."""
    ident = identity_from_device(dev)
    matched = matching_profiles(ident, ALL_PROFILES)
    fam = resolve_family(ident, capability, ALL_PROFILES)
    return {
        "identity": {
            "manufacturer": ident.manufacturer,
            "product_class": ident.product_class,
            "serial": ident.serial,
        },
        "profiles": [{"id": p.id, "priority": p.priority, "notes": p.notes} for p in matched],
        "candidates": resolve_candidates(ident, capability, ALL_PROFILES),
        "first_family": (
            None
            if not fam
            else {
                "capability": capability,
                "candidates": list(fam.candidates),
                "notes": fam.notes,
            }
        ),
    }


__all__ = [
    "ALL_PROFILES",
    "Cap",
    "DeviceIdentity",
    "PathFamily",
    "VendorProfile",
    "candidates_for",
    "describe_resolution",
    "discovery_candidates",
    "family_for",
    "identity_from_device",
    "leaf_keys_for",
    "manufacturer_distribution_groups",
    "profiles_for",
]
