from app.acs.actions import ensure_handlers_loaded, get_action, list_actions


def test_actions_registry_loads_core_handlers():
    ensure_handlers_loaded()
    names = {a.name for a in list_actions()}
    expected = {
        "reboot",
        "sync",
        "tags_add",
        "tags_remove",
        "wifi_get",
        "wifi_set",
        "wan_get",
        "wan_set_pppoe",
        "dhcp_get",
        "dhcp_set",
        "port_mapping_get",
        "port_mapping_add",
        "port_mapping_delete",
        "hosts_get",
        "ping",
        "traceroute",
        "diagnostic_full",
        "diagnostic_clear",
    }
    assert expected <= names
    reboot = get_action("reboot")
    assert reboot is not None
    assert reboot.permission == "acs.devices.write"
    diag = get_action("diagnostic_full")
    assert diag is not None
    assert diag.permission == "acs.diagnostic"
