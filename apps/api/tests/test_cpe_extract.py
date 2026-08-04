from app.cpe.extract import extract_neighbor_networks, extract_wan_profiles, extract_wifi_radios


def test_extract_wifi_and_wan():
    dev = {
        "_deviceId": {"_Manufacturer": "Generic", "_ProductClass": "IGD"},
        "InternetGatewayDevice": {
            "LANDevice": {
                "1": {
                    "WLANConfiguration": {
                        "1": {"SSID": {"_value": "Casa"}, "Channel": {"_value": 6}, "Enable": {"_value": True}}
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
    assert wan[0]["vlan_path"] and wan[0]["vlan_path"].endswith("X_VT_VLANID")


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
