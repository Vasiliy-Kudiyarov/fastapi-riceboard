from fastapi.testclient import TestClient


def _setup_initiative_with_estimate(client: TestClient, email: str) -> tuple[str, int]:
    """Регистрирует эксперта, создаёт инициативу и добавляет к ней оценку."""
    client.post("/auth/register", json={"email": email, "password": "pass123", "role": "expert"})
    token = client.post("/auth/login", data={"username": email, "password": "pass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    iid = client.post("/initiatives/", json={"title": f"Init {email}"}, headers=headers).json()["id"]
    client.post(
        f"/initiatives/{iid}/estimates/",
        json={"reach": 100, "impact": 2, "confidence": 80, "effort": 4},
        headers=headers,
    )
    return token, iid


# --- POST /prioritization/rank ---

def test_rank_success(client: TestClient) -> None:
    token, iid = _setup_initiative_with_estimate(client, "rank1@x.com")
    resp = client.post(
        "/prioritization/rank",
        json={"initiative_ids": [iid]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    ranked = resp.json()["ranked"]
    assert len(ranked) == 1
    assert ranked[0]["initiative_id"] == iid
    # RICE = 100 * 2 * 0.8 / 4 = 40.0
    assert ranked[0]["rice_score"] == 40.0


def test_rank_skips_no_estimates(client: TestClient) -> None:
    """Инициатива без оценок не попадает в ранжирование."""
    client.post("/auth/register", json={"email": "rank2@x.com", "password": "pass123", "role": "expert"})
    token = client.post("/auth/login", data={"username": "rank2@x.com", "password": "pass123"}).json()["access_token"]
    iid = client.post("/initiatives/", json={"title": "Без оценок"}, headers={"Authorization": f"Bearer {token}"}).json()["id"]
    resp = client.post(
        "/prioritization/rank",
        json={"initiative_ids": [iid]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["ranked"] == []


def test_rank_initiative_not_found(client: TestClient) -> None:
    token, _ = _setup_initiative_with_estimate(client, "rank3@x.com")
    resp = client.post(
        "/prioritization/rank",
        json={"initiative_ids": [9999]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_rank_unauthorized(client: TestClient) -> None:
    resp = client.post("/prioritization/rank", json={"initiative_ids": [1]})
    assert resp.status_code == 401


# --- POST /prioritization/optimize-portfolio ---

def test_optimize_portfolio_success(client: TestClient) -> None:
    token, iid = _setup_initiative_with_estimate(client, "knap1@x.com")
    resp = client.post(
        "/prioritization/optimize-portfolio",
        json={"initiative_ids": [iid], "budget": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["selected"]) == 1
    assert data["total_effort"] == 4.0
    assert data["total_rice_score"] == 40.0


def test_optimize_portfolio_budget_too_small(client: TestClient) -> None:
    """Если бюджет меньше effort любой инициативы — выбор пустой."""
    token, iid = _setup_initiative_with_estimate(client, "knap2@x.com")
    resp = client.post(
        "/prioritization/optimize-portfolio",
        json={"initiative_ids": [iid], "budget": 0.1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["selected"] == []


def test_optimize_portfolio_no_estimates(client: TestClient) -> None:
    """Если нет оценок — 400."""
    client.post("/auth/register", json={"email": "knap3@x.com", "password": "pass123", "role": "expert"})
    token = client.post("/auth/login", data={"username": "knap3@x.com", "password": "pass123"}).json()["access_token"]
    iid = client.post("/initiatives/", json={"title": "X"}, headers={"Authorization": f"Bearer {token}"}).json()["id"]
    resp = client.post(
        "/prioritization/optimize-portfolio",
        json={"initiative_ids": [iid], "budget": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
