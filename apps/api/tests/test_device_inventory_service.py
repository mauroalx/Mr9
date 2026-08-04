from datetime import UTC, datetime

from app.services.device_inventory import build_inventory_query


def test_inventory_filters_are_applied_to_server_query():
    query = build_inventory_query(
        q="cliente@isp",
        online=True,
        manufacturer="ZTE",
        model="H199A",
        firmware="V1",
        tag="noc",
        now=datetime(2026, 8, 4, tzinfo=UTC),
        online_threshold_s=300,
    )

    clauses = query["$and"]
    assert {"_deviceId._Manufacturer": "ZTE"} in clauses
    assert {"_deviceId._ProductClass": "H199A"} in clauses
    assert {"InternetGatewayDevice.DeviceInfo.SoftwareVersion._value": "V1"} in clauses
    assert {"_tags": "noc"} in clauses
    assert any("$or" in clause for clause in clauses)
