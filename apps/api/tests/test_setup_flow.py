from unittest.mock import AsyncMock, patch


def test_setup_status_uninstalled(client):
    r = client.get("/api/v1/setup/status")
    assert r.status_code == 200
    assert r.json()["installed"] is False


def test_refresh_rotates_session_tokens(client):
    created = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "refresh@example.com", "name": "Refresh", "password": "senha-segura"},
    )
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": created.json()["refresh_token"]},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]
    assert client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": created.json()["access_token"]},
    ).status_code == 401


def test_superadmin_and_complete_requires_acs(client):
    r = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "admin@example.com", "name": "Admin", "password": "senha-segura"},
    )
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r2 = client.post(
        "/api/v1/setup/settings",
        json={"approved_dns": ["1.1.1.1"], "timezone": "America/Sao_Paulo"},
        headers=headers,
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
                "verify_tls": False,
            },
            headers=headers,
        )
        assert r3.status_code == 200, r3.text
        # O bearer é opcional; este cenário valida um NBI sem autenticação.
        kwargs = MockClient.call_args.kwargs
        assert kwargs.get("bearer_token") in (None, "")
    r4 = client.post("/api/v1/setup/complete", headers=headers)
    assert r4.status_code == 200
    assert r4.json()["installed"] is True
    # O bootstrap não pode criar um segundo Super Admin.
    r5 = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "other@example.com", "name": "X", "password": "senha-segura"},
    )
    assert r5.status_code == 400
    assert client.post("/api/v1/setup/settings", json={}, headers=headers).status_code == 409


def test_setup_acs_with_optional_bearer_present(client):
    created = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "admin2@example.com", "name": "Admin", "password": "senha-segura"},
    )
    headers = {"Authorization": f"Bearer {created.json()['access_token']}"}
    client.post("/api/v1/setup/settings", json={"approved_dns": ["1.1.1.1"]}, headers=headers)
    with patch("app.api.routes.setup.GenieAcsClient") as MockClient:
        inst = MockClient.return_value
        inst.probe = AsyncMock(return_value={"ok": True, "status_code": 200})
        inst.aclose = AsyncMock()
        r = client.post(
            "/api/v1/setup/acs-server",
            json={
                "name": "secured",
                "base_url": "http://genie:7557",
                "bearer_token": "tok",
            },
            headers=headers,
        )
        assert r.status_code == 200, r.text
        assert MockClient.call_args.kwargs.get("bearer_token") == "tok"


def test_setup_steps_require_authenticated_superadmin(client):
    created = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "owner@example.com", "name": "Owner", "password": "senha-segura"},
    )
    assert created.status_code == 200
    assert client.post("/api/v1/setup/settings", json={}).status_code == 401
