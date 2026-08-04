"""Compat: reexporta extração CPE (lógica vive em `app.cpe`)."""

from app.cpe.extract import (
    dhcp_paths,
    diag_roots,
    extract_dhcp_lan,
    extract_hosts,
    extract_neighbor_networks,
    extract_port_mappings,
    extract_wan_profiles,
    extract_wifi_radios,
    wifi_set_parameter_values,
)

__all__ = [
    "dhcp_paths",
    "diag_roots",
    "extract_dhcp_lan",
    "extract_hosts",
    "extract_neighbor_networks",
    "extract_port_mappings",
    "extract_wan_profiles",
    "extract_wifi_radios",
    "wifi_set_parameter_values",
]
