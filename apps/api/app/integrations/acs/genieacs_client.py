from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx


def encode_device_id_for_path(device_id: str) -> str:
    return quote(str(device_id or "").strip(), safe="")


@dataclass(frozen=True)
class GenieAcsResponse:
    status_code: int
    json: Any


class GenieAcsClient:
    """Cliente NBI GenieACS. Instancie no backend com Bearer — nunca no browser."""

    def __init__(
        self,
        *,
        base_url: str,
        bearer_token: str | None = None,
        timeout_seconds: float = 15.0,
        max_concurrency: int = 12,
        verify_tls: bool = False,
    ):
        self.base_url = (base_url or "").strip().rstrip("/")
        self.bearer_token = (bearer_token or "").strip() or None
        self.timeout_seconds = float(timeout_seconds)
        self.max_concurrency = int(max_concurrency)
        self.verify_tls = bool(verify_tls)
        self._sem = asyncio.Semaphore(max(1, self.max_concurrency))
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.bearer_token:
                headers["Authorization"] = f"Bearer {self.bearer_token}"
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds),
                verify=self.verify_tls,
                follow_redirects=True,
                headers=headers,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: Any | None = None,
    ) -> GenieAcsResponse:
        url = f"{self.base_url}{path}"
        async with self._sem:
            client = await self._get_client()
            res = await client.request(method, url, params=params, json=json_body)
        try:
            payload = res.json()
        except Exception:
            payload = res.text
        return GenieAcsResponse(status_code=int(res.status_code), json=payload)

    async def probe(self) -> dict[str, Any]:
        res = await self._request("GET", "/devices/", params={"query": "{}", "limit": "1"})
        ok = res.status_code == 200
        return {"ok": ok, "status_code": res.status_code, "sample_count": len(res.json) if isinstance(res.json, list) else 0}

    async def search_devices(
        self,
        *,
        query: dict[str, Any],
        projection: list[str] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"query": json.dumps(query)}
        if projection:
            params["projection"] = ",".join([p for p in projection if str(p).strip()])
        if limit is not None:
            params["limit"] = str(int(limit))
        if skip is not None:
            params["skip"] = str(int(skip))
        res = await self._request("GET", "/devices/", params=params)
        if res.status_code != 200:
            raise RuntimeError(f"GenieACS devices search failed HTTP {res.status_code}: {res.json!r}")
        return res.json if isinstance(res.json, list) else []

    async def get_device(self, device_id: str, *, projection: list[str] | None = None) -> dict[str, Any] | None:
        devices = await self.search_devices(query={"_id": str(device_id)}, projection=projection, limit=1, skip=0)
        return devices[0] if devices else None

    async def create_task(
        self,
        device_id: str,
        payload: dict[str, Any],
        *,
        connection_request: bool,
        timeout_ms: int | None = None,
    ) -> GenieAcsResponse:
        enc = encode_device_id_for_path(device_id)
        qs: dict[str, str] = {}
        if connection_request:
            qs["connection_request"] = ""
        if timeout_ms is not None:
            qs["timeout"] = str(int(timeout_ms))
        return await self._request("POST", f"/devices/{enc}/tasks", params=qs or None, json_body=payload)

    async def set_tag(self, device_id: str, tag: str) -> GenieAcsResponse:
        enc = encode_device_id_for_path(device_id)
        return await self._request("POST", f"/devices/{enc}/tags/{quote(str(tag), safe='')}")

    async def delete_tag(self, device_id: str, tag: str) -> GenieAcsResponse:
        enc = encode_device_id_for_path(device_id)
        return await self._request("DELETE", f"/devices/{enc}/tags/{quote(str(tag), safe='')}")

    async def list_tasks(self, *, query: dict[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, str] = {"query": json.dumps(query)}
        if limit is not None:
            params["limit"] = str(int(limit))
        res = await self._request("GET", "/tasks/", params=params)
        if res.status_code != 200:
            raise RuntimeError(f"GenieACS tasks list failed HTTP {res.status_code}")
        return res.json if isinstance(res.json, list) else []

    async def list_faults(self, *, query: dict[str, Any], limit: int | None = None) -> list[dict[str, Any]]:
        params: dict[str, str] = {"query": json.dumps(query)}
        if limit is not None:
            params["limit"] = str(int(limit))
        res = await self._request("GET", "/faults/", params=params)
        if res.status_code != 200:
            raise RuntimeError(f"GenieACS faults list failed HTTP {res.status_code}")
        return res.json if isinstance(res.json, list) else []
