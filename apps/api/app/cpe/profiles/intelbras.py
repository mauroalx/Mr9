"""Intelbras GF1200 / W4 — X_ITBS_* NeighboringWiFi."""

from __future__ import annotations

from app.cpe.params import Cap, PathFamily, VendorProfile

INTELBRAS = VendorProfile(
    id="intelbras",
    manufacturers=frozenset({"intelbras"}),
    product_classes=frozenset(),
    priority=100,
    notes="Família X_ITBS_* para start/estado/resultado de vizinhança Wi‑Fi.",
    families={
        Cap.WIFI_BANDWIDTH: PathFamily(
            capability=Cap.WIFI_BANDWIDTH,
            candidates=("{root}.Bandwidth",),
            leaf_map={"bandwidth": ("Bandwidth",)},
        ),
        Cap.NEIGHBOR_START: PathFamily(
            capability=Cap.NEIGHBOR_START,
            candidates=(
                "InternetGatewayDevice.WiFi.X_ITBS_StartNeighboringWiFiDiagnostic",
                "InternetGatewayDevice.LANDevice.1.WiFi.X_ITBS_StartNeighboringWiFiDiagnostic",
            ),
            notes="Trigger: setar 1 (ou true) via SPV — validar por firmware.",
        ),
        Cap.NEIGHBOR_STATE: PathFamily(
            capability=Cap.NEIGHBOR_STATE,
            candidates=(
                "InternetGatewayDevice.WiFi.X_ITBS_NeighboringWiFiDiagnosticState",
                "InternetGatewayDevice.WiFi.X_ITBS_NeighboringWiFiDiagnostic.State",
                "InternetGatewayDevice.LANDevice.1.WiFi.X_ITBS_NeighboringWiFiDiagnosticState",
            ),
        ),
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=(
                "InternetGatewayDevice.WiFi.X_ITBS_NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.LANDevice.1.WiFi.X_ITBS_NeighboringWiFiDiagnostic.Result",
            ),
            leaf_map={
                "ssid": ("SSID", "ssid"),
                "channel": ("Channel", "channel"),
                "rssi": ("SignalStrength", "RSSI", "rssi"),
            },
        ),
    },
)

INTELBRAS_GF1200 = VendorProfile(
    id="intelbras.gf1200",
    manufacturers=frozenset({"intelbras"}),
    product_classes=frozenset({"gf1200", "w4", "onu-w4"}),
    priority=10,
    notes="GF1200 / W4 validados com X_ITBS_Start* + Result list.",
    families={
        Cap.NEIGHBOR_START: PathFamily(
            capability=Cap.NEIGHBOR_START,
            candidates=("InternetGatewayDevice.WiFi.X_ITBS_StartNeighboringWiFiDiagnostic",),
        ),
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=("InternetGatewayDevice.WiFi.X_ITBS_NeighboringWiFiDiagnostic.Result",),
            leaf_map={
                "ssid": ("SSID",),
                "channel": ("Channel",),
                "rssi": ("SignalStrength",),
            },
        ),
    },
)

PROFILES: tuple[VendorProfile, ...] = (INTELBRAS_GF1200, INTELBRAS)
