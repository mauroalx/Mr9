from app.acs.actions.portmap import _mapping_values


def test_new_mapping_uses_relative_add_object_parameters():
    values = _mapping_values(
        None,
        {
            "externalPort": 8080,
            "internalPort": 80,
            "internalClient": "192.168.1.10",
            "protocol": "TCP",
        },
    )

    assert values[0][0] == "PortMappingEnabled"
    assert all(not row[0].startswith("InternetGatewayDevice") for row in values)
