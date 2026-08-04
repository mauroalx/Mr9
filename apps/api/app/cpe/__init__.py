"""Pacote CPE: identidade, catálogo TR-069 e extração do inventário GenieACS."""

from app.cpe import extract as extract
from app.cpe.profiles import Cap, candidates_for, describe_resolution, identity_from_device

__all__ = [
    "Cap",
    "candidates_for",
    "describe_resolution",
    "extract",
    "identity_from_device",
]
