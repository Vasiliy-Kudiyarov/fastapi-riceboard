import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    """Тестовый клиент для отправки HTTP-запросов к приложению."""
    return TestClient(app)
