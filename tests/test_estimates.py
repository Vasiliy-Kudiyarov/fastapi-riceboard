from fastapi.testclient import TestClient


def _setup(client: TestClient, email: str, role: str = "expert") -> tuple[str, int]:
    """Регистрирует пользователя, создаёт инициативу. Возвращает (token, initiative_id)."""
    client.post("/auth/register", json={"email": email, "password": "pass123", "role": role})
    token = client.post("/auth/login", data={"username": email, "password": "pass123"}).json()["access_token"]
    iid = client.post(
        "/initiatives/", json={"title": "Init"}, headers={"Authorization": f"Bearer {token}"}
    ).json()["id"]
    return token, iid


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


ESTIMATE_DATA = {"reach": 60, "impact": 1.5, "confidence": 80, "effort": 2}


# --- GET /initiatives/{id}/estimates/ ---

def test_list_estimates_empty(client: TestClient) -> None:
    token, iid = _setup(client, "est1@x.com")
    resp = client.get(f"/initiatives/{iid}/estimates/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_estimates_initiative_not_found(client: TestClient) -> None:
    resp = client.get("/initiatives/999/estimates/")
    assert resp.status_code == 404


# --- POST /initiatives/{id}/estimates/ ---

def test_create_estimate_success(client: TestClient) -> None:
    token, iid = _setup(client, "est2@x.com")
    resp = client.post(f"/initiatives/{iid}/estimates/", json=ESTIMATE_DATA, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["reach"] == 60
    assert data["initiative_id"] == iid


def test_create_estimate_duplicate(client: TestClient) -> None:
    token, iid = _setup(client, "est3@x.com")
    client.post(f"/initiatives/{iid}/estimates/", json=ESTIMATE_DATA, headers=_auth(token))
    resp = client.post(f"/initiatives/{iid}/estimates/", json=ESTIMATE_DATA, headers=_auth(token))
    assert resp.status_code == 409


def test_create_estimate_initiative_not_found(client: TestClient) -> None:
    token, _ = _setup(client, "est4@x.com")
    resp = client.post("/initiatives/999/estimates/", json=ESTIMATE_DATA, headers=_auth(token))
    assert resp.status_code == 404


def test_create_estimate_invalid_reach(client: TestClient) -> None:
    token, iid = _setup(client, "est5@x.com")
    bad = {**ESTIMATE_DATA, "reach": 150}
    resp = client.post(f"/initiatives/{iid}/estimates/", json=bad, headers=_auth(token))
    assert resp.status_code == 422


# --- PUT /estimates/{id} ---

def test_update_estimate_success(client: TestClient) -> None:
    token, iid = _setup(client, "est6@x.com")
    eid = client.post(f"/initiatives/{iid}/estimates/", json=ESTIMATE_DATA, headers=_auth(token)).json()["id"]
    resp = client.put(f"/estimates/{eid}", json={"reach": 90}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["reach"] == 90


def test_update_estimate_forbidden(client: TestClient) -> None:
    token, iid = _setup(client, "est7@x.com")
    eid = client.post(f"/initiatives/{iid}/estimates/", json=ESTIMATE_DATA, headers=_auth(token)).json()["id"]
    # Другой пользователь
    client.post("/auth/register", json={"email": "other@x.com", "password": "pass123", "role": "expert"})
    other_token = client.post("/auth/login", data={"username": "other@x.com", "password": "pass123"}).json()["access_token"]
    resp = client.put(f"/estimates/{eid}", json={"reach": 50}, headers=_auth(other_token))
    assert resp.status_code == 403


def test_update_estimate_not_found(client: TestClient) -> None:
    token, _ = _setup(client, "est8@x.com")
    resp = client.put("/estimates/999", json={"reach": 50}, headers=_auth(token))
    assert resp.status_code == 404


# --- DELETE /estimates/{id} ---

def test_delete_estimate_success(client: TestClient) -> None:
    token, iid = _setup(client, "est9@x.com")
    eid = client.post(f"/initiatives/{iid}/estimates/", json=ESTIMATE_DATA, headers=_auth(token)).json()["id"]
    resp = client.delete(f"/estimates/{eid}", headers=_auth(token))
    assert resp.status_code == 204


def test_delete_estimate_forbidden(client: TestClient) -> None:
    token, iid = _setup(client, "est10@x.com")
    eid = client.post(f"/initiatives/{iid}/estimates/", json=ESTIMATE_DATA, headers=_auth(token)).json()["id"]
    client.post("/auth/register", json={"email": "other2@x.com", "password": "pass123", "role": "expert"})
    other_token = client.post("/auth/login", data={"username": "other2@x.com", "password": "pass123"}).json()["access_token"]
    resp = client.delete(f"/estimates/{eid}", headers=_auth(other_token))
    assert resp.status_code == 403
