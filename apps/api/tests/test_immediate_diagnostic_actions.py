from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.acs.actions.base import ActionContext
from app.acs.actions.tools import ping, traceroute
from app.integrations.acs.genieacs_client import GenieAcsResponse


def _device():
    return {
        "_deviceId": {"_Manufacturer": "Generic", "_ProductClass": "IGD"},
        "InternetGatewayDevice": {
            "IPPingDiagnostics": {"DiagnosticsState": {"_value": "None"}},
            "TraceRouteDiagnostics": {"DiagnosticsState": {"_value": "None"}},
        },
    }


class FakeClient:
    def __init__(self, response: GenieAcsResponse):
        self.response = response
        self.created = []
        self.deleted = []

    async def get_device(self, _device_id, *, projection=None):
        return _device()

    async def create_task(self, device_id, payload, *, connection_request, timeout_ms):
        self.created.append((device_id, payload, connection_request, timeout_ms))
        return self.response

    async def delete_task(self, task_id):
        self.deleted.append(task_id)
        return GenieAcsResponse(status_code=200, json={})


def _context(client: FakeClient, *, host: str = "8.8.8.8"):
    return ActionContext(
        device_id="cpe-1",
        params={"host": host},
        client=client,
        db=SimpleNamespace(),
        auth=SimpleNamespace(),
        server=SimpleNamespace(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("handler", [ping, traceroute])
async def test_network_diagnostics_force_connection_request(handler):
    client = FakeClient(GenieAcsResponse(status_code=200, json={}))

    result = await handler(_context(client))

    assert result == {"ok": True, "http": 200, "queued": False}
    assert client.created[0][2:] == (True, 12000)


@pytest.mark.asyncio
async def test_network_diagnostic_removes_task_when_cpe_does_not_answer():
    client = FakeClient(GenieAcsResponse(status_code=202, json={"_id": "task-1"}))

    with pytest.raises(HTTPException) as exc:
        await ping(_context(client))

    assert exc.value.status_code == 504
    assert client.deleted == ["task-1"]
