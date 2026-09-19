from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_backend_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "mordred-backend",
        "version": "0.3.0",
    }
