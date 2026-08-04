from types import SimpleNamespace

import pytest

from app.acs.actions.base import ActionContext
from app.acs.actions.traffic import traffic_sample
from app.cpe.traffic import traffic_projection
from app.integrations.acs.genieacs_client import GenieAcsResponse


def _device(*, rx: int, tx: int):
    return {
        "_deviceId": {"_Manufacturer": "ZTE", "_ProductClass": "ZXHN H199A"},
        "InternetGatewayDevice": {
            "WANDevice": {
                "2": {
                    "WANConnectionDevice": {
                        "1": {
                            "WANPPPConnection": {
                                "1": {
                                    "Stats": {
                                        "TotalBytesReceived": {"_value": rx},
                                        "TotalBytesSent": {"_value": tx},
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
    }


class FakeClient:
    def __init__(self):
        self.requests = []

    async def get_device(self, _device_id, *, projection=None):
        assert projection == traffic_projection()
        return _device(rx=1_500, tx=2_750)

    async def list_tasks(self, *, query, limit=None, skip=None):
        assert query["objectName"].endswith("WANPPPConnection.1.Stats")
        assert limit == 1
        return []

    async def create_task(self, device_id, payload, *, connection_request, timeout_ms):
        self.requests.append((device_id, payload, connection_request, timeout_ms))
        return GenieAcsResponse(status_code=200, json={})


@pytest.mark.asyncio
async def test_traffic_sample_refreshes_only_the_primary_wan_and_returns_counters():
    client = FakeClient()
    ctx = ActionContext(
        device_id="cpe-1",
        params={},
        client=client,
        db=SimpleNamespace(),
        auth=SimpleNamespace(),
        server=SimpleNamespace(),
    )

    result = await traffic_sample(ctx)

    assert result["available"] is True
    assert result["received_bytes"] == 1_500
    assert result["sent_bytes"] == 2_750
    assert "counter_updated_at" in result
    assert result["refresh_status"] == "completed"
    assert client.requests == [
        (
            "cpe-1",
            {
                "name": "refreshObject",
                "objectName": (
                    "InternetGatewayDevice.WANDevice.2.WANConnectionDevice.1."
                    "WANPPPConnection.1.Stats"
                ),
            },
            True,
            4500,
        )
    ]


@pytest.mark.asyncio
async def test_traffic_sample_does_not_duplicate_a_pending_refresh():
    client = FakeClient()

    async def pending_tasks(*, query, limit=None, skip=None):
        return [{"_id": "task-1", "objectName": query["objectName"]}]

    client.list_tasks = pending_tasks
    ctx = ActionContext(
        device_id="cpe-1",
        params={},
        client=client,
        db=SimpleNamespace(),
        auth=SimpleNamespace(),
        server=SimpleNamespace(),
    )

    result = await traffic_sample(ctx)

    assert result["refresh_status"] == "queued"
    assert client.requests == []
