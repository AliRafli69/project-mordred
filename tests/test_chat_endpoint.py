from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.inference import (
    InferenceAuthenticationError,
    InferenceMalformedResponseError,
    InferenceTimeoutError,
    InferenceUnavailableError,
)
from app.main import app, get_chat_client
from app.prompts import PromptConfigurationError


client = TestClient(app)


class SuccessfulChatClient:
    def __init__(self) -> None:
        self.system_prompt: str | None = None
        self.user_input: str | None = None

    async def generate(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> str:
        self.system_prompt = system_prompt
        self.user_input = user_input

        return "Hello from Mordred."


class FailingChatClient:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def generate(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> str:
        raise self._error


@pytest.fixture(autouse=True)
def configure_test_application() -> Generator[None, None, None]:
    settings = Settings(
        lm_studio_base_url="http://example.invalid:1234",
        lm_studio_api_key="inference-secret",
        lm_studio_model="test-model",
        backend_api_key="backend-secret",
    )

    app.dependency_overrides[get_settings] = lambda: settings

    yield

    app.dependency_overrides.clear()


def test_chat_rejects_missing_backend_credential() -> None:
    app.dependency_overrides[get_chat_client] = SuccessfulChatClient

    response = client.post(
        "/chat",
        json={"message": "Hello."},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_chat_rejects_incorrect_backend_credential() -> None:
    app.dependency_overrides[get_chat_client] = SuccessfulChatClient

    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer incorrect-secret"},
        json={"message": "Hello."},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_chat_injects_server_prompt_and_returns_reply() -> None:
    fake_client = SuccessfulChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake_client

    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer backend-secret"},
        json={"message": "  Hello, Mordred.  "},
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Hello from Mordred.",
        "model": "test-model",
    }
    assert fake_client.system_prompt
    assert fake_client.user_input == "Hello, Mordred."


def test_chat_rejects_blank_message() -> None:
    app.dependency_overrides[get_chat_client] = SuccessfulChatClient

    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer backend-secret"},
        json={"message": "   "},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (InferenceUnavailableError(), "inference_unavailable"),
        (InferenceTimeoutError(), "timeout"),
        (InferenceAuthenticationError(), "authentication_failed"),
        (InferenceMalformedResponseError(), "malformed_response"),
    ],
)
def test_chat_maps_controlled_inference_failures(
    error: Exception,
    reason: str,
) -> None:
    app.dependency_overrides[get_chat_client] = (
        lambda: FailingChatClient(error)
    )

    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer backend-secret"},
        json={"message": "Hello."},
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "reason": reason,
    }


def test_chat_handles_prompt_configuration_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_to_load_prompt() -> str:
        raise PromptConfigurationError("test failure")

    monkeypatch.setattr(
        "app.main.load_system_prompt",
        fail_to_load_prompt,
    )
    app.dependency_overrides[get_chat_client] = SuccessfulChatClient

    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer backend-secret"},
        json={"message": "Hello."},
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "reason": "prompt_configuration_error",
    }
