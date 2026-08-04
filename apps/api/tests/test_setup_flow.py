from unittest.mock import AsyncMock, patch


def test_setup_status_uninstalled(client):
    r = client.get("/api/v1/setup/status")
    assert r.status_code == 200
    assert r.json()["installed"] is False


def test_superadmin_and_complete_requires_acs(client):
    r = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "admin@example.com", "name": "Admin", "password": "senha-segura"},
    )
    assert r.status_code == 200, r.text
    r2 = client.post(
        "/api/v1/setup/settings",
        json={"approved_dns": ["1.1.1.1"], "timezone": "America/Sao_Paulo"},
    )
    assert r2.status_code == 200
    with patch("app.api.routes.setup.GenieAcsClient") as MockClient:
        inst = MockClient.return_value
        inst.probe = AsyncMock(return_value={"ok": True, "status_code": 200, "sample_count": 1})
        inst.aclose = AsyncMock()
        r3 = client.post(
            "/api/v1/setup/acs-server",
            json={
                "name": "local",
                "base_url": "http://genie:7557",
                "bearer_token": "tok",
                "verify_tls": False,
            },
        )
        assert r3.status_code == 200, r3.text
    r4 = client.post("/api/v1/setup/complete")
    assert r4.status_code == 200
    assert r4.json()["installed"] is True
    # second superadmin blocked
    r5 = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "other@example.com", "name": "X", "password": "senha-segura"},
    )
    assert r5.status_code == 400
