from app.cpe.params import Cap, DeviceIdentity, matching_profiles, resolve_candidates
from app.cpe.profiles import ALL_PROFILES, candidates_for, identity_from_device


def test_h3601p_prefers_wifi_before_wifi_upper():
    ident = DeviceIdentity(manufacturer="ZTE", product_class="H3601P")
    matched = matching_profiles(ident, ALL_PROFILES)
    assert matched[0].id == "zte.h3601p"
    cands = resolve_candidates(ident, Cap.WIFI_RADIO_CONTAINER, ALL_PROFILES)
    assert cands[0].endswith(".WiFi")
    assert any(c.endswith(".WIFI") for c in cands)
    assert cands[-1].endswith("WLANConfiguration") or "WLANConfiguration" in cands[-1]


def test_unknown_vendor_falls_back_to_generic():
    ident = DeviceIdentity(manufacturer="ACME-ISP-ROUTER", product_class="X100")
    matched = matching_profiles(ident, ALL_PROFILES)
    assert matched[-1].id == "generic.igd"
    assert any(p.id == "generic.igd" for p in matched)
    dns = resolve_candidates(ident, Cap.DHCP_DNS, ALL_PROFILES)
    assert dns[0].endswith("DNSServers")


def test_intelbras_neighbor_start_specific():
    ident = DeviceIdentity(manufacturer="Intelbras", product_class="GF1200")
    cands = resolve_candidates(ident, Cap.NEIGHBOR_START, ALL_PROFILES)
    assert "X_ITBS_StartNeighboringWiFiDiagnostic" in cands[0]


def test_huawei_eg8145_chain():
    ident = DeviceIdentity(manufacturer="Huawei Technologies Co., Ltd.", product_class="EG8145V5")
    matched_ids = [p.id for p in matching_profiles(ident, ALL_PROFILES)]
    assert matched_ids[0] == "huawei.eg8145"
    assert "huawei" in matched_ids
    assert matched_ids[-1] == "generic.igd"


def test_candidates_for_device_tree():
    dev = {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "H3601P", "_SerialNumber": "X"},
    }
    assert identity_from_device(dev).product_class == "H3601P"
    assert "WiFi" in candidates_for(dev, Cap.WIFI_RADIO_CONTAINER)[0]
