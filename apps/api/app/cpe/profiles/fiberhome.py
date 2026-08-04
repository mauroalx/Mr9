"""FiberHome — registro de identidade; paths WAN usam fallback TR-098."""

from __future__ import annotations

from app.cpe.params import VendorProfile

FIBERHOME = VendorProfile(
    id="fiberhome",
    manufacturers=frozenset(
        {
            "fiberhome",
            "fiberhome telecommunication technologies co., ltd.",
            "fiberhome telecommunication technologies co.,ltd",
        }
    ),
    product_classes=frozenset(),
    priority=100,
    notes="FiberHome TR-098; particularidades entram aqui antes do perfil genérico.",
)

PROFILES: tuple[VendorProfile, ...] = (FIBERHOME,)
