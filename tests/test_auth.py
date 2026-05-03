import pytest
from fastapi.testclient import TestClient


def _register(client: TestClient, email: str, password: str = "pass123", role: str = "viewer") -> dict:
    resp = client.post("/auth/register", json={"email": email, "password": password, "role": role})
    return resp


def _login(client: TestClient, email: str, password: str = "pass123") -> str:
    resp = client.post("/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# --- Регистрация ---

def test_register_success(client: TestClient) -> None:
    resp = _register(client, "user@example.com")
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "user@example.com"
    assert data["role"] == "viewer"
    assert "id" in data


def test_register_duplicate_email(client: TestClient) -> None:
    _register(client, "dup@example.com")
    resp = _register(client, "dup@example.com")
    assert resp.status_code == 409


def test_register_invalid_role(client: TestClient) -> None:
    resp = _register(client, "x@example.com", role="superuser")
    assert resp.status_code == 422


def test_register_short_password(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "x@x.com", "password": "12"})
    assert resp.status_code == 422


# --- Логин ---

def test_login_success(client: TestClient) -> None:
    _register(client, "login@example.com")
    resp = client.post("/auth/login", data={"username": "login@example.com", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client: TestClient) -> None:
    _register(client, "login2@example.com")
    resp = client.post("/auth/login", data={"username": "login2@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient) -> None:
    resp = client.post("/auth/login", data={"username": "nobody@example.com", "password": "pass123"})
    assert resp.status_code == 401


# --- /auth/me ---

def test_me_success(client: TestClient) -> None:
    _register(client, "me@example.com")
    token = _login(client, "me@example.com")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_me_unauthorized(client: TestClient) -> None:
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
