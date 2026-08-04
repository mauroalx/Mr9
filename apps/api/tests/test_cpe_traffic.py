import pytest

from app.cpe.traffic import primary_traffic_counters


def _device(*, wan_index: str = "2", rx=1_000, tx=2_000):
    return {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "ZXHN H199A"},
        "InternetGatewayDevice": {
            "WANDevice": {
                wan_index: {
                    "WANConnectionDevice": {
                        "1": {
                            "WANPPPConnection": {
                                "1": {
                                    "ConnectionStatus": {"_value": "Connected"},
                                    "Stats": {
                                        "TotalBytesReceived": {"_value": rx},
                                        "TotalBytesSent": {"_value": tx},
                                    },
                                }
                            }
                        }
                    }
                }
            }
        },
    }


def test_traffic_uses_first_existing_wan_even_when_index_does_not_start_at_one():
    counters = primary_traffic_counters(_device())

    assert counters.received_bytes == 1_000
    assert counters.sent_bytes == 2_000
    assert counters.refresh_root.endswith("WANPPPConnection.1.Stats")
    assert counters.available is True


def test_traffic_rejects_metadata_nodes_as_counter_values():
    counters = primary_traffic_counters(_device(rx={"_object": False}, tx=None))

    assert counters.received_bytes is None
    assert counters.sent_bytes is None
    assert counters.available is False


@pytest.mark.parametrize(
    ("manufacturer", "product_class"),
    [
        ("ZTE", "ZXHN H199A"),
        ("Huawei Technologies Co., Ltd", "EG8145V5"),
        ("Intelbras", "GF1200"),
        ("FiberHome", "AN5506-04"),
    ],
)
def test_generic_traffic_fallback_covers_registered_vendors(manufacturer, product_class):
    dev = _device(wan_index="3", rx=10_000, tx=20_000)
    dev["_deviceId"] = {
        "_Manufacturer": manufacturer,
        "_ProductClass": product_class,
    }

    counters = primary_traffic_counters(dev)

    assert counters.available is True
    assert counters.refresh_root.endswith("WANPPPConnection.1.Stats")


def test_traffic_accepts_stats_without_total_prefix():
    dev = _device(rx=0, tx=0)
    stats = dev["InternetGatewayDevice"]["WANDevice"]["2"]["WANConnectionDevice"]["1"][
        "WANPPPConnection"
    ]["1"]["Stats"]
    stats.clear()
    stats.update(
        {
            "BytesReceived": {"_value": 3_000},
            "BytesSent": {"_value": 4_000},
        }
    )

    counters = primary_traffic_counters(dev)

    assert counters.received_bytes == 3_000
    assert counters.sent_bytes == 4_000


def test_traffic_refreshes_the_exact_aggregate_object_used_by_zte():
    dev = _device(rx=0, tx=0)
    wan = dev["InternetGatewayDevice"]["WANDevice"]["2"]
    wan["WANConnectionDevice"]["1"]["WANPPPConnection"]["1"]["Stats"].clear()
    wan["WANCommonInterfaceConfig"] = {
        "TotalBytesReceived": {"_value": 12_000},
        "TotalBytesSent": {"_value": 24_000},
    }

    counters = primary_traffic_counters(dev)

    assert counters.received_bytes == 12_000
    assert counters.sent_bytes == 24_000
    assert counters.refresh_root == "InternetGatewayDevice.WANDevice.2.WANCommonInterfaceConfig"


def test_traffic_supports_tr181_ppp_interface():
    dev = {
        "_deviceId": {"_Manufacturer": "Vendor TR-181", "_ProductClass": "Router"},
        "Device": {
            "PPP": {
                "Interface": {
                    "4": {
                        "Stats": {
                            "BytesReceived": {"_value": 50_000},
                            "BytesSent": {"_value": 25_000},
                        }
                    }
                }
            }
        },
    }

    counters = primary_traffic_counters(dev)

    assert counters.received_bytes == 50_000
    assert counters.sent_bytes == 25_000
    assert counters.refresh_root == "Device.PPP.Interface.4.Stats"
