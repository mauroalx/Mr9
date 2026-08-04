from datetime import UTC, datetime

import pytest

from app.services.dashboard_service import collect_acs_metrics


class CountClient:
    def __init__(self):
        self.queries = []

    async def count_devices(self, *, query):
        self.queries.append(query)
        if not query:
            return 100
        text = str(query).lower()
        if "softwareversion" in text:
            return 80
        if "manufacturer" in text and "zte" in text:
            return 60
        if "manufacturer" in text and "huawei" in text:
            return 30
        if "_lastinform" in text and "24" not in text:
            return 90
        return 90


@pytest.mark.asyncio
async def test_collect_acs_metrics_uses_global_counts():
    client = CountClient()
    metrics = await collect_acs_metrics(
        client,
        now=datetime(2026, 8, 4, tzinfo=UTC),
        online_threshold_s=300,
        manufacturer_groups=[
            {"label": "ZTE", "pattern": "zte"},
            {"label": "Huawei", "pattern": "huawei"},
        ],
    )

    assert metrics["total"] == 100
    assert metrics["online"] == 90
    assert metrics["offline"] == 10
    assert metrics["firmware_known"] == 80
    assert metrics["manufacturers"][-1] == {"name": "Outros", "count": 10}
