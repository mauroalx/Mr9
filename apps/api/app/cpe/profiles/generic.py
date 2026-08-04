"""Perfil TR-098 / InternetGatewayDevice genérico (fallback final)."""

from __future__ import annotations

from app.cpe.params import Cap, PathFamily, VendorProfile

GENERIC = VendorProfile(
    id="generic.igd",
    manufacturers=frozenset(),  # wildcard
    product_classes=frozenset(),
    priority=1000,
    notes="Paths padrão TR-098/IGD. Sempre presente como fallback.",
    families={
        Cap.WIFI_RADIO_CONTAINER: PathFamily(
            capability=Cap.WIFI_RADIO_CONTAINER,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WLANConfiguration",
                "InternetGatewayDevice.LANDevice.1.WiFi",
                "InternetGatewayDevice.LANDevice.1.WIFI",
            ),
            notes="Containers de rádio/SSID. Extração itera índices numéricos.",
        ),
        Cap.WIFI_SSID: PathFamily(
            capability=Cap.WIFI_SSID,
            candidates=("{root}.SSID",),
            leaf_map={"ssid": ("SSID",)},
        ),
        Cap.WIFI_KEY: PathFamily(
            capability=Cap.WIFI_KEY,
            candidates=(
                "{root}.KeyPassphrase",
                "{root}.PreSharedKey.1.KeyPassphrase",
                "{root}.PreSharedKey.1.PreSharedKey",
            ),
        ),
        Cap.WIFI_CHANNEL: PathFamily(
            capability=Cap.WIFI_CHANNEL,
            candidates=("{root}.Channel",),
            leaf_map={"channel": ("Channel",)},
        ),
        Cap.WIFI_AUTO_CHANNEL: PathFamily(
            capability=Cap.WIFI_AUTO_CHANNEL,
            candidates=("{root}.AutoChannelEnable",),
            leaf_map={"auto_channel": ("AutoChannelEnable",)},
        ),
        Cap.WIFI_BANDWIDTH: PathFamily(
            capability=Cap.WIFI_BANDWIDTH,
            candidates=("{root}.Bandwidth", "{root}.OperatingChannelBandwidth"),
            leaf_map={"bandwidth": ("Bandwidth", "OperatingChannelBandwidth")},
        ),
        Cap.WIFI_ENABLE: PathFamily(
            capability=Cap.WIFI_ENABLE,
            candidates=("{root}.Enable",),
            leaf_map={"enable": ("Enable",)},
        ),
        Cap.WAN_VLAN: PathFamily(
            capability=Cap.WAN_VLAN,
            candidates=(
                "{root}.X_VT_VLANID",
                "{root}.VLANID",
                "{root}.X_CU_VLAN",
            ),
            notes="VLAN vendor-neuter; vendors adicionam aliases mais à frente na cadeia.",
        ),
        Cap.WAN_DEVICE: PathFamily(
            capability=Cap.WAN_DEVICE,
            candidates=("InternetGatewayDevice.WANDevice",),
            notes="Container WANDevice; índices 1..N.",
        ),
        Cap.DEVICE_UPTIME: PathFamily(
            capability=Cap.DEVICE_UPTIME,
            candidates=("InternetGatewayDevice.DeviceInfo.UpTime",),
        ),
        Cap.OPTICAL_CONTAINER: PathFamily(
            capability=Cap.OPTICAL_CONTAINER,
            candidates=(
                "Device.Optical.Interface",
                "InternetGatewayDevice.WANDevice.1.OpticalInterface",
            ),
            leaf_map={
                "status": ("Status", "ConnectionStatus", "LinkStatus"),
                "technology": ("Technology", "Standard", "LinkType"),
                "rx_power": ("RXPower", "RxPower", "ReceivePower", "OpticalRxPower"),
                "tx_power": ("TXPower", "TxPower", "TransmitPower", "OpticalTxPower"),
                "distance": ("Distance", "ONTDistance", "OnuDistance", "OpticalDistance"),
                "temperature": ("TransceiverTemperature", "Temperature", "OpticalTemperature"),
                "voltage": ("SupplyVoltage", "Voltage", "OpticalVoltage"),
                "bias": ("BiasCurrent", "TxBias", "OpticalBiasCurrent"),
                "fec": (
                    "Stats.FECError",
                    "Stats.FECErrors",
                    "FECError",
                    "FECErrors",
                    "FecErrors",
                ),
                "hec": (
                    "Stats.HECError",
                    "Stats.HECErrors",
                    "HECError",
                    "HECErrors",
                    "HecErrors",
                ),
                "crc": (
                    "Stats.CRCError",
                    "Stats.CRCErrors",
                    "CRCError",
                    "CRCErrors",
                    "CrcErrors",
                ),
            },
            notes="Interface óptica TR-181; aliases servem como fallback entre firmwares.",
        ),
        Cap.IGD_ROOT: PathFamily(
            capability=Cap.IGD_ROOT,
            candidates=("InternetGatewayDevice",),
        ),
        Cap.WAN_NAT: PathFamily(
            capability=Cap.WAN_NAT,
            candidates=("{root}.NATEnabled",),
        ),
        Cap.WAN_USERNAME: PathFamily(
            capability=Cap.WAN_USERNAME,
            candidates=(
                "{root}.Username",
                "VirtualParameters.pppoeUsername",
                "VirtualParameters.PPPoEUsername",
                "VirtualParameters.pppoe_username",
            ),
            notes="Username real por WAN; Virtual Parameters são atalhos opcionais.",
        ),
        Cap.WAN_PASSWORD: PathFamily(
            capability=Cap.WAN_PASSWORD,
            candidates=("{root}.Password",),
        ),
        Cap.WAN_BYTES_RECEIVED: PathFamily(
            capability=Cap.WAN_BYTES_RECEIVED,
            candidates=(
                "{root}.Stats.TotalBytesReceived",
                "{root}.Stats.BytesReceived",
                "{root}.Stats.EthernetBytesReceived",
                "{wan}.WANCommonInterfaceConfig.TotalBytesReceived",
                "{wan}.WANEthernetInterfaceConfig.Stats.BytesReceived",
                "{interface}.Stats.BytesReceived",
            ),
            notes="Conexão primeiro; contadores agregados da WANDevice como fallback.",
        ),
        Cap.WAN_BYTES_SENT: PathFamily(
            capability=Cap.WAN_BYTES_SENT,
            candidates=(
                "{root}.Stats.TotalBytesSent",
                "{root}.Stats.BytesSent",
                "{root}.Stats.EthernetBytesSent",
                "{wan}.WANCommonInterfaceConfig.TotalBytesSent",
                "{wan}.WANEthernetInterfaceConfig.Stats.BytesSent",
                "{interface}.Stats.BytesSent",
            ),
            notes="Conexão primeiro; contadores agregados da WANDevice como fallback.",
        ),
        Cap.WAN_TRAFFIC_INTERFACE: PathFamily(
            capability=Cap.WAN_TRAFFIC_INTERFACE,
            candidates=(
                "Device.PPP.Interface",
                "Device.IP.Interface",
                "Device.Ethernet.Interface",
                "Device.PTM.Link",
                "Device.ATM.Link",
                "Device.Optical.Interface",
            ),
            notes="Interfaces TR-181 ordenadas da camada lógica para a física.",
        ),
        Cap.DHCP_ROOT: PathFamily(
            capability=Cap.DHCP_ROOT,
            candidates=("InternetGatewayDevice.LANDevice.1.LANHostConfigManagement",),
        ),
        Cap.DHCP_ENABLE: PathFamily(
            capability=Cap.DHCP_ENABLE,
            candidates=("InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.DHCPServerEnable",),
        ),
        Cap.DHCP_DNS: PathFamily(
            capability=Cap.DHCP_DNS,
            candidates=("InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.DNSServers",),
        ),
        Cap.DHCP_MIN: PathFamily(
            capability=Cap.DHCP_MIN,
            candidates=("InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.MinAddress",),
        ),
        Cap.DHCP_MAX: PathFamily(
            capability=Cap.DHCP_MAX,
            candidates=("InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.MaxAddress",),
        ),
        Cap.DHCP_LEASE: PathFamily(
            capability=Cap.DHCP_LEASE,
            candidates=("InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.DHCPLeaseTime",),
        ),
        Cap.DHCP_LAN_IP: PathFamily(
            capability=Cap.DHCP_LAN_IP,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceIPAddress",
            ),
        ),
        Cap.DHCP_SUBNET: PathFamily(
            capability=Cap.DHCP_SUBNET,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPInterface.1.IPInterfaceSubnetMask",
                "InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.SubnetMask",
            ),
        ),
        Cap.DHCP_ROUTERS: PathFamily(
            capability=Cap.DHCP_ROUTERS,
            candidates=("InternetGatewayDevice.LANDevice.1.LANHostConfigManagement.IPRouters",),
        ),
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.Result",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.Result",
                "Device.WiFi.NeighboringWiFiDiagnostic.Result",
            ),
            leaf_map={
                "ssid": ("SSID", "ssid"),
                "channel": ("Channel", "channel"),
                "rssi": ("SignalStrength", "RSSI", "rssi"),
            },
            notes="Resultado genérico de scan vizinho (quando o CPE implementa o objeto padrão).",
        ),
        Cap.NEIGHBOR_START: PathFamily(
            capability=Cap.NEIGHBOR_START,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
            ),
        ),
        Cap.NEIGHBOR_STATE: PathFamily(
            capability=Cap.NEIGHBOR_STATE,
            candidates=(
                "InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
                "InternetGatewayDevice.WiFi.NeighboringWiFiDiagnostic.DiagnosticsState",
            ),
        ),
        Cap.PING_ROOT: PathFamily(
            capability=Cap.PING_ROOT,
            candidates=("InternetGatewayDevice.IPPingDiagnostics",),
        ),
        Cap.TRACEROUTE_ROOT: PathFamily(
            capability=Cap.TRACEROUTE_ROOT,
            candidates=("InternetGatewayDevice.TraceRouteDiagnostics",),
        ),
        Cap.HOSTS_CONTAINER: PathFamily(
            capability=Cap.HOSTS_CONTAINER,
            candidates=("InternetGatewayDevice.LANDevice.1.Hosts.Host",),
        ),
        Cap.LAN_PORT_CONTAINER: PathFamily(
            capability=Cap.LAN_PORT_CONTAINER,
            candidates=("InternetGatewayDevice.LANDevice.1.LANEthernetInterfaceConfig",),
            leaf_map={
                "status": ("Status",),
                "enable": ("Enable",),
                "rate": ("MaxBitRate", "CurrentBitRate"),
                "duplex": ("DuplexMode",),
                "name": ("Name", "X_HW_PortName", "X_ZTE-COM_Name"),
            },
            notes="Portas Ethernet da LAN no TR-098; índices presentes definem a quantidade.",
        ),
    },
)
