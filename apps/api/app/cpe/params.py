"""Catálogo de paths TR-069 / GenieACS por vendor e modelo.

Ordem de resolução:
1. Perfil **modelo específico** (manufacturer + product_class)
2. Perfil **vendor** (todos os modelos da família)
3. Perfil **generic** (TR-098 / IGD comum)

Quem contribui: edite `app/cpe/profiles/<vendor>.py` (ou crie um novo), registre em
`PROFILES`, e adicione um teste com inventário JSON mínimo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Capabilidades (chaves estáveis — use estas no código de aplicação)
# ---------------------------------------------------------------------------

class Cap:
    WIFI_RADIO_CONTAINER = "wifi.radio_container"
    WIFI_SSID = "wifi.ssid"
    WIFI_KEY = "wifi.key"
    WIFI_CHANNEL = "wifi.channel"
    WIFI_ENABLE = "wifi.enable"

    WAN_DEVICE = "wan.device"  # container WANDevice
    WAN_VLAN = "wan.vlan"
    WAN_NAT = "wan.nat"
    WAN_USERNAME = "wan.username"
    WAN_PASSWORD = "wan.password"

    DEVICE_UPTIME = "device.uptime"

    DHCP_ROOT = "dhcp.root"
    DHCP_ENABLE = "dhcp.enable"
    DHCP_DNS = "dhcp.dns"
    DHCP_MIN = "dhcp.min"
    DHCP_MAX = "dhcp.max"
    DHCP_LEASE = "dhcp.lease"
    DHCP_LAN_IP = "dhcp.lan_ip"
    DHCP_SUBNET = "dhcp.subnet"
    DHCP_ROUTERS = "dhcp.ip_routers"

    NEIGHBOR_START = "neighbor.start"  # SPV / trigger
    NEIGHBOR_STATE = "neighbor.state"
    NEIGHBOR_RESULT = "neighbor.result"  # container Result.*

    PING_ROOT = "diag.ping"
    TRACEROUTE_ROOT = "diag.traceroute"

    HOSTS_CONTAINER = "hosts.container"

    IGD_ROOT = "igd.root"  # para refreshObject / projection


@dataclass(frozen=True)
class PathFamily:
    """Lista ordenada de candidatos para uma capacidade.

    Templates podem usar `{i}`, `{j}`, `{k}` para índices TR-069.
    O primeiro path que **existir** no inventário do CPE vence.
    """

    capability: str
    candidates: tuple[str, ...]
    # Campos leaf relativos ao item Result.* (neighbors) ou ao rádio
    leaf_map: dict[str, tuple[str, ...]] = field(default_factory=dict)
    notes: str = ""


@dataclass(frozen=True)
class VendorProfile:
    """Perfil de vendor/modelo.

    - `manufacturers` / `product_classes`: matching case-insensitive; conjunto vazio = wildcard.
    - `priority`: menor = mais específico (modelo < vendor < generic).
    """

    id: str
    manufacturers: frozenset[str] = frozenset()
    product_classes: frozenset[str] = frozenset()
    priority: int = 100
    families: dict[str, PathFamily] = field(default_factory=dict)
    notes: str = ""


@dataclass(frozen=True)
class DeviceIdentity:
    manufacturer: str
    product_class: str
    serial: str = ""
    oui: str = ""

    @property
    def manufacturer_l(self) -> str:
        return self.manufacturer.strip().lower()

    @property
    def product_class_l(self) -> str:
        return self.product_class.strip().lower()


def identity_from_device(dev: dict[str, Any]) -> DeviceIdentity:
    from app.cpe.tree import leaf

    did = dev.get("_deviceId") if isinstance(dev.get("_deviceId"), dict) else {}
    info = (
        ((dev.get("InternetGatewayDevice") or {}).get("DeviceInfo") or {})
        if isinstance(dev.get("InternetGatewayDevice"), dict)
        else {}
    )

    manufacturer = str(did.get("_Manufacturer") or leaf(info.get("Manufacturer")) or "")
    product_class = str(did.get("_ProductClass") or leaf(info.get("ProductClass")) or "")
    serial = str(did.get("_SerialNumber") or leaf(info.get("SerialNumber")) or "")
    oui = str(did.get("_OUI") or "")
    return DeviceIdentity(manufacturer=manufacturer, product_class=product_class, serial=serial, oui=oui)


def _norm_set(values: Iterable[str]) -> frozenset[str]:
    return frozenset(v.strip().lower() for v in values if str(v).strip())


def profile_matches(profile: VendorProfile, ident: DeviceIdentity) -> bool:
    mfrs = _norm_set(profile.manufacturers)
    pcs = _norm_set(profile.product_classes)
    if mfrs and ident.manufacturer_l not in mfrs and not any(x in ident.manufacturer_l for x in mfrs):
        # substring alias (ex.: "huawei technologies" contains "huawei")
        if not any(alias in ident.manufacturer_l or ident.manufacturer_l in alias for alias in mfrs):
            return False
    if pcs and ident.product_class_l not in pcs and not any(
        alias in ident.product_class_l or ident.product_class_l in alias for alias in pcs
    ):
        return False
    return True


def matching_profiles(ident: DeviceIdentity, profiles: tuple[VendorProfile, ...]) -> list[VendorProfile]:
    matched = [p for p in profiles if profile_matches(p, ident)]
    # Específico primeiro: priority asc, depois id
    return sorted(matched, key=lambda p: (p.priority, p.id))


def resolve_family(
    ident: DeviceIdentity,
    capability: str,
    profiles: tuple[VendorProfile, ...],
) -> PathFamily | None:
    """Primeira PathFamily definida na cadeia específico → genérico."""
    for profile in matching_profiles(ident, profiles):
        fam = profile.families.get(capability)
        if fam and fam.candidates:
            return fam
    return None


def resolve_candidates(
    ident: DeviceIdentity,
    capability: str,
    profiles: tuple[VendorProfile, ...],
) -> list[str]:
    """Une candidatos de todos os perfis matchando, **sem duplicar**, específico→genérico.

    Útil quando o inventário não tem tipagem confiável e queremos varrer com ordem.
    """
    out: list[str] = []
    seen: set[str] = set()
    for profile in matching_profiles(ident, profiles):
        fam = profile.families.get(capability)
        if not fam:
            continue
        for cand in fam.candidates:
            if cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out


def resolve_candidates_discovery(
    capability: str,
    profiles: tuple[VendorProfile, ...],
) -> list[str]:
    """Varredura best-effort: todos os perfis (modelo→vendor→generic), ignorando identidade.

    Use só quando a leitura specific→generic não achou nada (CPE sem Manufacturer, etc.).
    """
    ordered = sorted(profiles, key=lambda p: (p.priority, p.id))
    out: list[str] = []
    seen: set[str] = set()
    for profile in ordered:
        fam = profile.families.get(capability)
        if not fam:
            continue
        for cand in fam.candidates:
            if cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out


def resolve_leaf_keys(
    ident: DeviceIdentity,
    capability: str,
    field: str,
    profiles: tuple[VendorProfile, ...],
) -> list[str]:
    """Aliases de leaf (SSID / Channel / SignalStrength…) — específico→genérico."""
    out: list[str] = []
    seen: set[str] = set()
    for profile in matching_profiles(ident, profiles):
        fam = profile.families.get(capability)
        if not fam:
            continue
        for key in fam.leaf_map.get(field, ()):
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out
