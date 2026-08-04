import pytest
from app.integrations.acs.genieacs_client import GenieAcsClient, encode_device_id_for_path


def test_encode_device_id():
    assert "%25" in encode_device_id_for_path("C04943-ZXHN%20H3601P-ABC")


@pytest.mark.asyncio
async def test_probe_uses_bearer(httpx_mock=None):
    # lightweight: ensure client stores bearer header construction path
    c = GenieAcsClient(base_url="http://example.invalid", bearer_token="abc")
    assert c.bearer_token == "abc"
    await c.aclose()
