from fastapi.testclient import TestClient


def _login_as(client: TestClient, email: str, role: str) -> str:
    client.post("/auth/register", json={"email": email, "password": "pass123", "role": role})
    return client.post("/auth/login", data={"username": email, "password": "pass123"}).json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- GET /categories/ ---

def test_list_categories_empty(client: TestClient) -> None:
    resp = client.get("/categories/")
    assert resp.status_code == 200
    assert resp.json() == []


# --- POST /categories/ ---

def test_create_category_admin(client: TestClient) -> None:
    token = _login_as(client, "admin@x.com", "admin")
    resp = client.post("/categories/", json={"name": "Инфра", "description": "Desc"}, headers=_auth(token))
    assert resp.status_code == 201
    assert resp.json()["name"] == "Инфра"


def test_create_category_forbidden_non_admin(client: TestClient) -> None:
    token = _login_as(client, "viewer@x.com", "viewer")
    resp = client.post("/categories/", json={"name": "Запрещённая"}, headers=_auth(token))
    assert resp.status_code == 403


def test_create_category_duplicate(client: TestClient) -> None:
    token = _login_as(client, "admin2@x.com", "admin")
    client.post("/categories/", json={"name": "Уникальная"}, headers=_auth(token))
    resp = client.post("/categories/", json={"name": "Уникальная"}, headers=_auth(token))
    assert resp.status_code == 409


def test_list_categories_after_create(client: TestClient) -> None:
    token = _login_as(client, "admin3@x.com", "admin")
    client.post("/categories/", json={"name": "А"}, headers=_auth(token))
    client.post("/categories/", json={"name": "Б"}, headers=_auth(token))
    resp = client.get("/categories/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- POST /initiatives/{id}/categories/{cat_id} ---

def test_link_category_success(client: TestClient) -> None:
    admin_token = _login_as(client, "adm@x.com", "admin")
    iid = client.post("/initiatives/", json={"title": "Init"}, headers=_auth(admin_token)).json()["id"]
    cid = client.post("/categories/", json={"name": "Cat"}, headers=_auth(admin_token)).json()["id"]
    resp = client.post(f"/initiatives/{iid}/categories/{cid}", headers=_auth(admin_token))
    assert resp.status_code == 200


def test_link_category_initiative_not_found(client: TestClient) -> None:
    admin_token = _login_as(client, "adm2@x.com", "admin")
    cid = client.post("/categories/", json={"name": "Cat2"}, headers=_auth(admin_token)).json()["id"]
    resp = client.post(f"/initiatives/999/categories/{cid}", headers=_auth(admin_token))
    assert resp.status_code == 404


def test_link_category_forbidden(client: TestClient) -> None:
    admin_token = _login_as(client, "adm3@x.com", "admin")
    viewer_token = _login_as(client, "viewer3@x.com", "viewer")
    iid = client.post("/initiatives/", json={"title": "Init"}, headers=_auth(admin_token)).json()["id"]
    cid = client.post("/categories/", json={"name": "Cat3"}, headers=_auth(admin_token)).json()["id"]
    resp = client.post(f"/initiatives/{iid}/categories/{cid}", headers=_auth(viewer_token))
    assert resp.status_code == 403
