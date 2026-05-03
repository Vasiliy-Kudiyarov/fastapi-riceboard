"""Тесты для расширенного ответа GET /initiatives/{id} и пагинации списка."""
from fastapi.testclient import TestClient


def _login_as(client: TestClient, email: str, role: str = "admin") -> str:
    client.post("/auth/register", json={"email": email, "password": "pass123", "role": role})
    return client.post("/auth/login", data={"username": email, "password": "pass123"}).json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Категории в деталях инициативы ---

def test_initiative_detail_has_categories_field(client: TestClient) -> None:
    token = _login_as(client, "det1@x.com")
    iid = client.post("/initiatives/", json={"title": "X"}, headers=_auth(token)).json()["id"]
    resp = client.get(f"/initiatives/{iid}")
    assert resp.status_code == 200
    assert "categories" in resp.json()
    assert resp.json()["categories"] == []


def test_initiative_detail_shows_linked_category(client: TestClient) -> None:
    token = _login_as(client, "det2@x.com")
    iid = client.post("/initiatives/", json={"title": "Y"}, headers=_auth(token)).json()["id"]
    cid = client.post("/categories/", json={"name": "ТестКат"}, headers=_auth(token)).json()["id"]
    client.post(f"/initiatives/{iid}/categories/{cid}", headers=_auth(token))

    resp = client.get(f"/initiatives/{iid}")
    assert resp.status_code == 200
    cats = resp.json()["categories"]
    assert len(cats) == 1
    assert cats[0]["name"] == "ТестКат"


# --- Пагинация и сортировка ---

def test_pagination_limit(client: TestClient) -> None:
    token = _login_as(client, "pag1@x.com")
    for i in range(5):
        client.post("/initiatives/", json={"title": f"Init {i}"}, headers=_auth(token))

    resp = client.get("/initiatives/?limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_pagination_offset(client: TestClient) -> None:
    token = _login_as(client, "pag2@x.com")
    for i in range(4):
        client.post("/initiatives/", json={"title": f"P{i}"}, headers=_auth(token))

    all_ids = [i["id"] for i in client.get("/initiatives/").json()]
    offset_ids = [i["id"] for i in client.get("/initiatives/?offset=2").json()]
    # Смещение на 2 — получаем последние 2 элемента
    assert offset_ids == all_ids[2:]


def test_list_ordered_newest_first(client: TestClient) -> None:
    token = _login_as(client, "pag3@x.com")
    id1 = client.post("/initiatives/", json={"title": "Первая"}, headers=_auth(token)).json()["id"]
    id2 = client.post("/initiatives/", json={"title": "Вторая"}, headers=_auth(token)).json()["id"]

    ids = [i["id"] for i in client.get("/initiatives/").json()]
    # Новые сверху — id2 должен быть раньше id1
    assert ids.index(id2) < ids.index(id1)


def test_pagination_invalid_limit(client: TestClient) -> None:
    resp = client.get("/initiatives/?limit=0")
    assert resp.status_code == 422


def test_filter_by_category_id(client: TestClient) -> None:
    token = _login_as(client, "pag4@x.com")
    iid = client.post("/initiatives/", json={"title": "С категорией"}, headers=_auth(token)).json()["id"]
    client.post("/initiatives/", json={"title": "Без категории"}, headers=_auth(token))
    cid = client.post("/categories/", json={"name": "Фильтр"}, headers=_auth(token)).json()["id"]
    client.post(f"/initiatives/{iid}/categories/{cid}", headers=_auth(token))

    resp = client.get(f"/initiatives/?category_id={cid}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == iid
