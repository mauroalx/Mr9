from app.cpe.search import wan_inventory_query_fields


def test_wan_search_has_virtual_and_multiple_index_fallbacks():
    fields = wan_inventory_query_fields()
    assert "VirtualParameters.pppoeUsername._value" in fields
    assert (
        "InternetGatewayDevice.WANDevice.1.WANConnectionDevice.1.WANPPPConnection.2.Username._value"
    ) in fields
    assert (
        "InternetGatewayDevice.WANDevice.1.WANConnectionDevice.2.WANPPPConnection.1.ExternalIPAddress._value"
    ) in fields
