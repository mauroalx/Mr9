def _auth(client):
    created = client.post(
        "/api/v1/setup/superadmin",
        json={"email": "admin@example.com", "name": "Admin", "password": "senha-segura"},
    )
    assert created.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "senha-segura"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_create_and_manage_user(client):
    headers = _auth(client)
    group = client.post(
        "/api/v1/security/groups",
        headers=headers,
        json={"name": "NOC", "permissions": ["acs.access"]},
    )
    assert group.status_code == 200
    group_id = group.json()["id"]
    created = client.post(
        "/api/v1/security/users",
        headers=headers,
        json={
            "email": "operador@example.com",
            "name": "Operador",
            "password": "senha-inicial",
            "group_id": group_id,
        },
    )
    assert created.status_code == 200

    updated = client.patch(
        f"/api/v1/security/users/{created.json()['id']}",
        headers=headers,
        json={
            "email": "noc@example.com",
            "name": "Operador NOC",
            "group_id": group_id,
            "is_active": False,
            "password": "senha-alterada",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["email"] == "noc@example.com"
    assert updated.json()["is_active"] is False

    users = client.get("/api/v1/security/users", headers=headers)
    assert users.status_code == 200
    assert [user["email"] for user in users.json()] == ["noc@example.com"]


def test_security_crud_rejects_invalid_ids_and_duplicate_group_names(client):
    headers = _auth(client)
    first = client.post(
        "/api/v1/security/groups",
        headers=headers,
        json={"name": "NOC", "permissions": []},
    )
    second = client.post(
        "/api/v1/security/groups",
        headers=headers,
        json={"name": "Suporte", "permissions": []},
    )
    assert first.status_code == second.status_code == 200

    invalid = client.patch(
        "/api/v1/security/groups/id-invalido",
        headers=headers,
        json={"name": "Campo", "permissions": []},
    )
    assert invalid.status_code == 400

    duplicate = client.patch(
        f"/api/v1/security/groups/{second.json()['id']}",
        headers=headers,
        json={"name": "NOC", "permissions": []},
    )
    assert duplicate.status_code == 400

    user = client.post(
        "/api/v1/security/users",
        headers=headers,
        json={
            "email": "operador@example.com",
            "name": "Operador",
            "password": "senha-inicial",
            "group_id": "id-invalido",
        },
    )
    assert user.status_code == 400
