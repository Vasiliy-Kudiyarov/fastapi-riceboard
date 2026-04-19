from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    """Эндпоинт /health должен возвращать 200 и статус ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_endpoint_is_available(client: TestClient) -> None:
    """Swagger UI должен быть доступен на /docs."""
    response = client.get("/docs")
    assert response.status_code == 200
