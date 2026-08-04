import pytest
from fastapi import HTTPException

from app.acs.actions.dhcp import validate_dhcp_params


def test_validate_complete_dhcp_configuration():
    values = validate_dhcp_params(
        {
            "enabled": True,
            "lanIp": "192.168.10.1",
            "subnetMask": "255.255.255.0",
            "minAddress": "192.168.10.20",
            "maxAddress": "192.168.10.200",
            "dnsServers": "1.1.1.1, 8.8.8.8",
            "leaseTime": 86400,
        }
    )

    assert values["dnsServers"] == "1.1.1.1,8.8.8.8"
    assert values["leaseTime"] == 86400


def test_validate_dhcp_rejects_pool_outside_subnet():
    with pytest.raises(HTTPException, match="fora da sub-rede"):
        validate_dhcp_params(
            {
                "lanIp": "192.168.10.1",
                "subnetMask": "255.255.255.0",
                "minAddress": "192.168.20.2",
            }
        )
