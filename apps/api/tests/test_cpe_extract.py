from app.cpe.extract import (
    extract_dhcp_lan,
    extract_lan_ports,
    extract_neighbor_networks,
    extract_optical_telemetry,
    extract_wan_profiles,
    extract_wifi_radios,
    wifi_set_parameter_values,
)


def test_extract_lan_ports_preserves_link_and_disabled_states():
    dev = {
        "_deviceId": {"_Manufacturer": "Generic", "_ProductClass": "ONT"},
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "LANEthernetInterfaceConfig": {
                        "1": {
                            "Status": {"_value": "Up"},
                            "Enable": {"_value": True},
                            "MaxBitRate": {"_value": 1000},
                            "DuplexMode": {"_value": "Full"},
                        },
                        "2": {
                            "Status": {"_value": "Down"},
                            "Enable": {"_value": "false"},
                        },
                    }
                }
            }
        },
    }

    ports = extract_lan_ports(dev)

    assert ports[0] == {
        "index": 1,
        "name": "LAN 1",
        "status": "Up",
        "enabled": True,
        "maxBitRate": "1000",
        "duplexMode": "Full",
    }
    assert ports[1]["status"] == "Down"
    assert ports[1]["enabled"] is False


def test_extract_huawei_gpon_optical_telemetry():
    dev = {
        "_deviceId": {
            "_Manufacturer": "Huawei Technologies Co., Ltd.",
            "_ProductClass": "EG8145V5",
        },
        "InternetGatewayDevice": {
            "WANDevice": {
                "1": {
                    "X_GponInterafceConfig": {
                        "Status": {"_value": "Up"},
                        "RXPower": {"_value": "-23 dBm"},
                        "TXPower": {"_value": 2.4},
                        "ONTDistance": {"_value": 1840},
                        "TransceiverTemperature": {"_value": 47},
                        "SupplyVoltage": {"_value": 3.3},
                        "BiasCurrent": {"_value": 12.8},
                        "Stats": {
                            "FECError": {"_value": 10827},
                            "HECError": {"_value": 2},
                            "CRCError": {"_value": 1},
                        },
                    }
                }
            }
        },
    }

    optical = extract_optical_telemetry(dev)

    assert optical == {
        "detected": True,
        "technology": "GPON",
        "status": "Up",
        "rxPowerDbm": -23,
        "txPowerDbm": 2.4,
        "distanceMeters": 1840,
        "temperatureC": 47,
        "voltageV": 3.3,
        "biasCurrentMa": 12.8,
        "fecErrors": 10827,
        "hecErrors": 2,
        "crcErrors": 1,
    }


def test_extract_optical_ignores_metadata_only_stubs():
    dev = {
        "_deviceId": {"_Manufacturer": "Generic", "_ProductClass": "ONT"},
        "Device": {
            "Optical": {
                "Interface": {
                    "1": {
                        "RXPower": {"_object": False, "_writable": False},
                        "Stats": {"FECErrors": {"_object": False}},
                    }
                }
            }
        },
    }

    assert extract_optical_telemetry(dev) is None


def test_dhcp_metadata_stubs_are_not_exposed_as_values():
    metadata_stub = {"_object": False, "_writable": True}
    dev = {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "ZXHN H199A"},
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "LANHostConfigManagement": {
                        "DHCPServerEnable": {"_value": True},
                        "DNSServers": metadata_stub,
                        "MinAddress": metadata_stub,
                        "MaxAddress": metadata_stub,
                        "DHCPLeaseTime": metadata_stub,
                        "IPInterface": {
                            "1": {
                                "IPInterfaceIPAddress": metadata_stub,
                                "IPInterfaceSubnetMask": metadata_stub,
                            }
                        },
                    }
                }
            }
        },
    }

    dhcp = extract_dhcp_lan(dev)

    assert dhcp is not None
    assert dhcp["enabled"] is True
    assert dhcp["lanIp"] == ""
    assert dhcp["subnetMask"] == ""
    assert dhcp["minAddress"] == ""
    assert dhcp["maxAddress"] == ""
    assert dhcp["dnsServers"] == ""
    assert dhcp["leaseTime"] is None


def test_extract_wifi_and_wan():
    dev = {
        "_deviceId": {"_Manufacturer": "Generic", "_ProductClass": "IGD"},
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "WLANConfiguration": {
                        "1": {
                            "SSID": {"_value": "Casa"},
                            "Channel": {"_value": 6},
                            "Enable": {"_value": True},
                        }
                    }
                }
            },
            "WANDevice": {
                "1": {
                    "WANConnectionDevice": {
                        "1": {
                            "WANPPPConnection": {
                                "1": {
                                    "Name": {"_value": "internet"},
                                    "Username": {"_value": "user@isp"},
                                    "ConnectionStatus": {"_value": "Connected"},
                                    "ExternalIPAddress": {"_value": "1.2.3.4"},
                                    "Stats": {
                                        "TotalBytesReceived": {"_value": 2_750_000_000},
                                        "TotalBytesSent": {"_value": 4_220_000_000},
                                    },
                                    "NATEnabled": {"_value": True},
                                    "X_VT_VLANID": {"_value": 100},
                                }
                            }
                        }
                    }
                }
            },
        },
    }
    wifi = extract_wifi_radios(dev)
    assert wifi and wifi[0]["ssid"] == "Casa"
    wan = extract_wan_profiles(dev)
    assert wan and wan[0]["kind"] == "ppp" and wan[0]["username"] == "user@isp"
    assert wan[0]["bytes_received"] == 2_750_000_000
    assert wan[0]["bytes_sent"] == 4_220_000_000
    assert wan[0]["vlan_path"] and wan[0]["vlan_path"].endswith("X_VT_VLANID")


def test_wan_counters_fall_back_to_wan_common_interface():
    dev = {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "ZXHN H198A V3.0"},
        "InternetGatewayDevice": {
            "WANDevice": {
                "1": {
                    "WANCommonInterfaceConfig": {
                        "TotalBytesReceived": {"_value": 3_560_000_000},
                        "TotalBytesSent": {"_value": 2_680_000_000},
                    },
                    "WANConnectionDevice": {
                        "1": {
                            "WANPPPConnection": {
                                "1": {"ConnectionStatus": {"_value": "Connected"}}
                            }
                        }
                    },
                }
            }
        },
    }

    wan = extract_wan_profiles(dev)

    assert wan[0]["bytes_received"] == 3_560_000_000
    assert wan[0]["bytes_sent"] == 2_680_000_000


def test_wan_profiles_are_sorted_by_existing_numeric_index():
    dev = {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "H198A"},
        "InternetGatewayDevice": {
            "WANDevice": {
                "1": {
                    "WANConnectionDevice": {
                        "1": {
                            "WANPPPConnection": {
                                "5": {"Username": {"_value": "quinta@isp"}},
                                "2": {"Username": {"_value": "segunda@isp"}},
                            }
                        }
                    }
                }
            }
        },
    }
    wan = extract_wan_profiles(dev)
    assert [profile["username"] for profile in wan] == ["segunda@isp", "quinta@isp"]


def test_wan_username_falls_back_to_virtual_parameter():
    dev = {
        "_deviceId": {"_Manufacturer": "Generic", "_ProductClass": "IGD"},
        "VirtualParameters": {
            "pppoeUsername": {"_value": "virtual@isp"},
        },
        "InternetGatewayDevice": {
            "WANDevice": {
                "1": {
                    "WANConnectionDevice": {
                        "1": {"WANPPPConnection": {"2": {}}},
                    }
                }
            }
        },
    }
    assert extract_wan_profiles(dev)[0]["username"] == "virtual@isp"


def test_wifi_extracts_bandwidth_and_builds_full_configuration():
    dev = {
        "_deviceId": {"_Manufacturer": "Generic", "_ProductClass": "IGD"},
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "WLANConfiguration": {
                        "3": {
                            "SSID": {"_value": "Visitantes"},
                            "Channel": {"_value": 11},
                            "AutoChannelEnable": {"_value": False},
                            "Bandwidth": {"_value": "40MHz"},
                            "Enable": {"_value": False},
                        }
                    }
                }
            }
        },
    }
    radio = extract_wifi_radios(dev)[0]
    assert radio["bandwidth"] == "40MHz"
    assert radio["autoChannel"] is False
    assert radio["enabled"] is False
    values = wifi_set_parameter_values(
        radio["root"], ssid="Novo SSID", channel=6, bandwidth="20MHz", enabled=True, dev=dev
    )
    paths = {row[0]: row[1] for row in values}
    assert paths[f"{radio['root']}.SSID"] == "Novo SSID"
    assert paths[f"{radio['root']}.Channel"] == 6
    assert paths[f"{radio['root']}.AutoChannelEnable"] is False
    assert paths[f"{radio['root']}.Bandwidth"] == "20MHz"
    assert paths[f"{radio['root']}.Enable"] is True

    automatic = wifi_set_parameter_values(radio["root"], channel=0, dev=dev)
    automatic_paths = {row[0]: row[1] for row in automatic}
    assert automatic_paths[f"{radio['root']}.AutoChannelEnable"] is True
    assert f"{radio['root']}.Channel" not in automatic_paths


def test_wifi_zte_uses_vendor_bandwidth_and_auto_channel_paths():
    root = "InternetGatewayDevice.LANDevice.1.WLANConfiguration.4"
    dev = {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "H3601P"},
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "WLANConfiguration": {
                        "4": {
                            "SSID": {"_value": "Rede"},
                            "Channel": {"_value": 2},
                            "AutoChannelEnable": {"_value": True},
                            "X_ZTE-COM_BandWidth": {"_value": "20MHz"},
                            "Enable": {"_value": True},
                        }
                    }
                }
            }
        },
    }

    radio = extract_wifi_radios(dev)[0]
    assert radio["autoChannel"] is True
    assert radio["bandwidth"] == "20MHz"

    values = wifi_set_parameter_values(root, channel=6, bandwidth="40MHz", dev=dev)
    paths = {row[0]: row[1] for row in values}
    assert paths[f"{root}.AutoChannelEnable"] is False
    assert paths[f"{root}.Channel"] == 6
    assert paths[f"{root}.X_ZTE-COM_BandWidth"] == "40MHz"


def test_neighbors_zte_huawei_intelbras_via_registry():
    zte = {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "H3601P"},
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "WiFi": {
                        "Radio": {
                            "1": {
                                "NeighboringWiFiDiagnostic": {
                                    "Result": {
                                        "1": {
                                            "SSID": {"_value": "Vizinho-ZTE"},
                                            "Channel": {"_value": 11},
                                            "SignalStrength": {"_value": -70},
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
    }
    hw = {
        "_deviceId": {"_Manufacturer": "Huawei Technologies Co., Ltd.", "_ProductClass": "EG8145V5"},
        "InternetGatewayDevice": {
            "WiFi": {
                "NeighboringWiFiDiagnostic": {
                    "Result": {
                        "1": {
                            "SSID": {"_value": "Vizinho-HW"},
                            "Channel": {"_value": 36},
                            "SignalStrength": {"_value": -65},
                        }
                    }
                }
            }
        },
    }
    itbs = {
        "_deviceId": {"_Manufacturer": "Intelbras", "_ProductClass": "GF1200"},
        "InternetGatewayDevice": {
            "WiFi": {
                "X_ITBS_NeighboringWiFiDiagnostic": {
                    "Result": {
                        "1": {
                            "SSID": {"_value": "Vizinho-ITBS"},
                            "Channel": {"_value": 1},
                            "SignalStrength": {"_value": -55},
                        }
                    }
                }
            }
        },
    }
    assert extract_neighbor_networks(zte)[0]["ssid"] == "Vizinho-ZTE"
    assert extract_neighbor_networks(hw)[0]["ssid"] == "Vizinho-HW"
    assert extract_neighbor_networks(itbs)[0]["ssid"] == "Vizinho-ITBS"
