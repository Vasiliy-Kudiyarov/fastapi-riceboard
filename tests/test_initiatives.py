from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str, role: str = "viewer") -> str:
    client.post("/auth/register", json={"email": email, "password": "pass123", "role": role})
    resp = client.post("/auth/login", data={"username": email, "password": "pass123"})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- GET /initiatives/ ---

def test_list_initiatives_empty(client: TestClient) -> None:
    resp = client.get("/initiatives/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_initiatives_filter_by_status(client: TestClient) -> None:
    token = _register_and_login(client, "a@x.com", "admin")
    client.post("/initiatives/", json={"title": "Init1", "status": "draft"}, headers=_auth(token))
    client.post("/initiatives/", json={"title": "Init2", "status": "proposed"}, headers=_auth(token))
    resp = client.get("/initiatives/?status=draft")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["status"] == "draft"


# --- GET /initiatives/{id} ---

def test_get_initiative_not_found(client: TestClient) -> None:
    resp = client.get("/initiatives/999")
    assert resp.status_code == 404


def test_get_initiative_success(client: TestClient) -> None:
    token = _register_and_login(client, "b@x.com")
    create_resp = client.post("/initiatives/", json={"title": "Тест"}, headers=_auth(token))
    iid = create_resp.json()["id"]
    resp = client.get(f"/initiatives/{iid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Тест"


# --- POST /initiatives/ ---

def test_create_initiative_success(client: TestClient) -> None:
    token = _register_and_login(client, "c@x.com")
    resp = client.post("/initiatives/", json={"title": "Новая", "status": "proposed"}, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["title"] == "Новая"


def test_create_initiative_unauthorized(client: TestClient) -> None:
    resp = client.post("/initiatives/", json={"title": "Без токена"})
    assert resp.status_code == 401


def test_create_initiative_invalid_status(client: TestClient) -> None:
    token = _register_and_login(client, "d@x.com")
    resp = client.post("/initiatives/", json={"title": "Плохой статус", "status": "unknown"}, headers=_auth(token))
    assert resp.status_code == 422


# --- PUT /initiatives/{id} ---

def test_update_initiative_success(client: TestClient) -> None:
    token = _register_and_login(client, "e@x.com")
    iid = client.post("/initiatives/", json={"title": "Старое"}, headers=_auth(token)).json()["id"]
    resp = client.put(f"/initiatives/{iid}", json={"title": "Новое"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Новое"


def test_update_initiative_forbidden(client: TestClient) -> None:
    owner_token = _register_and_login(client, "owner@x.com")
    other_token = _register_and_login(client, "other@x.com")
    iid = client.post("/initiatives/", json={"title": "Чужая"}, headers=_auth(owner_token)).json()["id"]
    resp = client.put(f"/initiatives/{iid}", json={"title": "Взлом"}, headers=_auth(other_token))
    assert resp.status_code == 403


def test_update_initiative_not_found(client: TestClient) -> None:
    token = _register_and_login(client, "f@x.com")
    resp = client.put("/initiatives/999", json={"title": "Нет"}, headers=_auth(token))
    assert resp.status_code == 404


# --- DELETE /initiatives/{id} ---

def test_delete_initiative_success(client: TestClient) -> None:
    token = _register_and_login(client, "g@x.com")
    iid = client.post("/initiatives/", json={"title": "Удаляемая"}, headers=_auth(token)).json()["id"]
    resp = client.delete(f"/initiatives/{iid}", headers=_auth(token))
    assert resp.status_code == 204
    assert client.get(f"/initiatives/{iid}").status_code == 404


def test_delete_initiative_forbidden(client: TestClient) -> None:
    owner_token = _register_and_login(client, "h@x.com")
    other_token = _register_and_login(client, "i@x.com")
    iid = client.post("/initiatives/", json={"title": "Чужая"}, headers=_auth(owner_token)).json()["id"]
    resp = client.delete(f"/initiatives/{iid}", headers=_auth(other_token))
    assert resp.status_code == 403
