"""ZTE — family H3601 / WIFI vs WiFi (case) + radio diagnostics."""

from __future__ import annotations

from app.cpe.params import Cap, PathFamily, VendorProfile

# Vendor-wide (qualquer ProductClass ZTE)
ZTE = VendorProfile(
    id="zte",
    manufacturers=frozenset({"zte", "zte corporation"}),
    product_classes=frozenset(),
    priority=100,
    notes="Paths ZTE comuns (VLAN / vizinhos sob LANDevice.*.WiFi|WIFI.Radio).",
    families={
        Cap.WAN_VLAN: PathFamily(
            capability=Cap.WAN_VLAN,
            candidates=(
                "{root}.X_ZTE_VLAN",
                "{root}.X_ZTE-COM_VLANID",
                "{root}.X_VT_VLANID",
                "{root}.VLANID",
            ),
        ),
        Cap.WIFI_RADIO_CONTAINER: PathFamily(
            capability=Cap.WIFI_RADIO_CONTAINER,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WIFI",
                "InternetGatewayDevice.LANDevice.1.WiFi",
                "InternetGatewayDevice.LANDevice.1.WLANConfiguration",
            ),
            notes="H3601 P1/P3 usam WIFI; P9/P10 usam WiFi.",
        ),
        Cap.NEIGHBOR_START: PathFamily(
            capability=Cap.NEIGHBOR_START,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.Radio.{i}.DiagnosticsState",
                "InternetGatewayDevice.LANDevice.1.WIFI.Radio.{i}.DiagnosticsState",
                "InternetGatewayDevice.LANDevice.1.WiFi.Radio.{i}.NeighboringWiFiDiagnostic.DiagnosticsState",
                "InternetGatewayDevice.LANDevice.1.WIFI.Radio.{i}.NeighboringWiFiDiagnostic.DiagnosticsState",
            ),
            notes="Trigger de scan por rádio. Expandir {i} com índices presentes.",
        ),
        Cap.NEIGHBOR_STATE: PathFamily(
            capability=Cap.NEIGHBOR_STATE,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.Radio.{i}.DiagnosticsState",
                "InternetGatewayDevice.LANDevice.1.WIFI.Radio.{i}.DiagnosticsState",
                "InternetGatewayDevice.LANDevice.1.WiFi.Radio.{i}.NeighboringWiFiDiagnostic.DiagnosticsState",
                "InternetGatewayDevice.LANDevice.1.WIFI.Radio.{i}.NeighboringWiFiDiagnostic.DiagnosticsState",
            ),
        ),
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.Radio.{i}.NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.LANDevice.1.WIFI.Radio.{i}.NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.LANDevice.1.WiFi.Radio.{i}.X_ZTE_NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.LANDevice.1.WIFI.Radio.{i}.X_ZTE_NeighboringWiFiDiagnostic.Result",
            ),
            leaf_map={
                "ssid": ("SSID", "ssid"),
                "channel": ("Channel", "channel"),
                "rssi": ("SignalStrength", "RSSI", "rssi"),
            },
        ),
    },
)

# Modelo mais específico — prioridade menor
ZTE_H3601P = VendorProfile(
    id="zte.h3601p",
    manufacturers=frozenset({"zte", "zte corporation"}),
    product_classes=frozenset({"h3601p", "h3601"}),
    priority=10,
    notes="H3601P: preferir WiFi (P9/P10) antes de WIFI (P1/P3).",
    families={
        Cap.WIFI_RADIO_CONTAINER: PathFamily(
            capability=Cap.WIFI_RADIO_CONTAINER,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi",
                "InternetGatewayDevice.LANDevice.1.WIFI",
                "InternetGatewayDevice.LANDevice.1.WLANConfiguration",
            ),
        ),
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.Radio.{i}.NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.LANDevice.1.WIFI.Radio.{i}.NeighboringWiFiDiagnostic.Result",
            ),
            leaf_map={
                "ssid": ("SSID",),
                "channel": ("Channel",),
                "rssi": ("SignalStrength",),
            },
            notes="P9/P10: WiFi (case). P1/P3: WIFI.",
        ),
    },
)

PROFILES: tuple[VendorProfile, ...] = (ZTE_H3601P, ZTE)
