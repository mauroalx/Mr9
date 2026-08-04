"""Huawei EG8145 / K562e — NeighboringWiFiDiagnostic sob WiFi."""

from __future__ import annotations

from app.cpe.params import Cap, PathFamily, VendorProfile

HUAWEI = VendorProfile(
    id="huawei",
    manufacturers=frozenset({"huawei", "huawei technologies co., ltd.", "huawei technologies"}),
    product_classes=frozenset(),
    priority=100,
    notes="Paths Huawei comuns. Leaf stub Genie sem _value: use param_exists(require_value=False).",
    families={
        Cap.WAN_VLAN: PathFamily(
            capability=Cap.WAN_VLAN,
            candidates=(
                "{root}.X_HW_VLAN",
                "{root}.X_HW_VLANID",
                "{root}.X_VT_VLANID",
                "{root}.VLANID",
            ),
        ),
        Cap.NEIGHBOR_START: PathFamily(
            capability=Cap.NEIGHBOR_START,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
                "Device.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
            ),
        ),
        Cap.NEIGHBOR_STATE: PathFamily(
            capability=Cap.NEIGHBOR_STATE,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
                "Device.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
            ),
        ),
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.Result",
                "Device.WiFi.NeighboringWiFiDiagnostic.Result",
            ),
            leaf_map={
                "ssid": ("SSID",),
                "channel": ("Channel",),
                "rssi": ("SignalStrength",),
            },
        ),
    },
)

HUAWEI_EG8145 = VendorProfile(
    id="huawei.eg8145",
    manufacturers=frozenset({"huawei", "huawei technologies co., ltd.", "huawei technologies"}),
    product_classes=frozenset({"eg8145v5", "eg8145", "k562e-10", "k562e"}),
    priority=10,
    notes="EG8145V5 / K562e-10: NeighboringWiFiDiagnostic sob LANDevice.1.WiFi.",
    families={
        Cap.NEIGHBOR_START: PathFamily(
            capability=Cap.NEIGHBOR_START,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
            ),
        ),
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.Result",
            ),
            leaf_map={
                "ssid": ("SSID",),
                "channel": ("Channel",),
                "rssi": ("SignalStrength",),
            },
        ),
    },
)

PROFILES: tuple[VendorProfile, ...] = (HUAWEI_EG8145, HUAWEI)
