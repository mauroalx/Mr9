import httpx
import pytest

from app.integrations.acs.genieacs_client import (
    GenieAcsClient,
    GenieAcsResponse,
    encode_device_id_for_path,
)


def test_encode_device_id():
    assert "%25" in encode_device_id_for_path("C04943-ZXHN%20H3601P-ABC")


@pytest.mark.asyncio
async def test_probe_uses_bearer(httpx_mock=None):
    # Garante que a construção do cliente preserve o bearer configurado.
    c = GenieAcsClient(base_url="http://example.invalid", bearer_token="abc")
    assert c.bearer_token == "abc"
    await c.aclose()


@pytest.mark.asyncio
async def test_request_translates_timeout_to_gateway_timeout(monkeypatch):
    from app.core.exceptions import AcsUpstreamError

    class TimeoutClient:
        async def request(self, *args, **kwargs):
            raise httpx.ReadTimeout("timeout")

    client = GenieAcsClient(base_url="http://example.invalid")

    async def get_client():
        return TimeoutClient()

    monkeypatch.setattr(client, "_get_client", get_client)
    with pytest.raises(AcsUpstreamError) as exc:
        await client._request("GET", "/devices/")
    assert exc.value.status_code == 504


@pytest.mark.asyncio
async def test_task_transport_timeout_exceeds_genie_timeout(monkeypatch):
    client = GenieAcsClient(base_url="http://example.invalid", timeout_seconds=15)
    captured = {}

    async def request(*args, **kwargs):
        captured.update(kwargs)
        return GenieAcsResponse(status_code=200, json={})

    monkeypatch.setattr(client, "_request", request)
    await client.create_task(
        "cpe-1",
        {"name": "refreshObject", "objectName": "InternetGatewayDevice"},
        connection_request=True,
        timeout_ms=25000,
    )
    assert captured["timeout_seconds"] == 30


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [{"total": "92363"}, {"x-total-count": "92363"}])
async def test_count_devices_uses_total_count_header(monkeypatch, headers):
    client = GenieAcsClient(base_url="http://example.invalid")

    async def request(*args, **kwargs):
        return GenieAcsResponse(status_code=200, json="", headers=headers)

    monkeypatch.setattr(client, "_request", request)
    assert await client.count_devices(query={}) == 92363
