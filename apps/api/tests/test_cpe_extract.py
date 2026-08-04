from app.services.cpe_extract import extract_neighbor_networks, extract_wan_profiles, extract_wifi_radios


def test_extract_wifi_and_wan():
    dev = {
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
                                }
                            }
                        }
                    }
                }
            },
        }
    }
    wifi = extract_wifi_radios(dev)
    assert wifi and wifi[0]["ssid"] == "Casa"
    wan = extract_wan_profiles(dev)
    assert wan and wan[0]["kind"] == "ppp" and wan[0]["username"] == "user@isp"


def test_neighbors_zte_huawei_intelbras():
    dev = {
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
            },
            "WiFi": {
                "NeighboringWiFiDiagnostic": {
                    "Result": {
                        "1": {
                            "SSID": {"_value": "Vizinho-HW"},
                            "Channel": {"_value": 36},
                            "SignalStrength": {"_value": -65},
                        }
                    }
                },
                "X_ITBS_NeighboringWiFiDiagnostic": {
                    "Result": {
                        "1": {
                            "SSID": {"_value": "Vizinho-ITBS"},
                            "Channel": {"_value": 1},
                            "SignalStrength": {"_value": -55},
                        }
                    }
                },
            },
        }
    }
    rows = extract_neighbor_networks(dev)
    ssids = {r["ssid"] for r in rows}
    assert {"Vizinho-ZTE", "Vizinho-HW", "Vizinho-ITBS"} <= ssids
    vendors = {r["vendor"] for r in rows}
    assert {"zte", "huawei", "intelbras"} <= vendors
