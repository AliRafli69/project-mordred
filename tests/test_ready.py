import pytest
from fastapi.testclient import TestClient

from app.inference import (
    InferenceAuthenticationError,
    InferenceMalformedResponseError,
    InferenceModelUnavailableError,
    InferenceTimeoutError,
    InferenceUnavailableError,
)
from app.main import app, get_inference_client


client = TestClient(app)


class SuccessfulInferenceClient:
    async def check_ready(self) -> str:
        return "test-model"


class FailingInferenceClient:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def check_ready(self) -> str:
        raise self._error


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_ready_returns_200_when_model_is_available() -> None:
    app.dependency_overrides[get_inference_client] = (
        lambda: SuccessfulInferenceClient()
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "inference": "available",
        "model": "test-model",
    }


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (InferenceUnavailableError(), "inference_unavailable"),
        (InferenceTimeoutError(), "timeout"),
        (InferenceAuthenticationError(), "authentication_failed"),
        (InferenceMalformedResponseError(), "malformed_response"),
        (InferenceModelUnavailableError(), "model_unavailable"),
    ],
)
def test_ready_returns_503_for_controlled_inference_failures(
    error: Exception,
    reason: str,
) -> None:
    app.dependency_overrides[get_inference_client] = (
        lambda: FailingInferenceClient(error)
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "inference": "unavailable",
        "reason": reason,
    }


def test_health_remains_ok_when_inference_is_unavailable() -> None:
    app.dependency_overrides[get_inference_client] = (
        lambda: FailingInferenceClient(InferenceUnavailableError())
    )

    readiness_response = client.get("/ready")
    health_response = client.get("/health")

    assert readiness_response.status_code == 503
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
