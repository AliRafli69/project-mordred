from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.conversations import (
    ConversationMessage,
    InMemoryConversationStore,
)
from app.inference import (
    InferenceAuthenticationError,
    InferenceMalformedResponseError,
    InferenceTimeoutError,
    InferenceUnavailableError,
)
from app.main import (
    app,
    get_chat_client,
    get_conversation_store,
)
from app.prompts import PromptConfigurationError


client = TestClient(app)


class SuccessfulChatClient:
    def __init__(self) -> None:
        self.system_prompt: str | None = None
        self.user_input: str | None = None
        self.history: tuple[ConversationMessage, ...] = ()

    async def generate(
        self,
        *,
        system_prompt: str,
        user_input: str,
        history: tuple[ConversationMessage, ...] = (),
    ) -> str:
        self.system_prompt = system_prompt
        self.user_input = user_input
        self.history = history

        return "Hello from Mordred."


class FailingChatClient:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def generate(
        self,
        *,
        system_prompt: str,
        user_input: str,
        history: tuple[ConversationMessage, ...] = (),
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
    store = InMemoryConversationStore(
        max_messages=12,
        max_characters=24_000,
    )

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_conversation_store] = lambda: store

    yield

    app.dependency_overrides.clear()


def authenticated_headers() -> dict[str, str]:
    return {"Authorization": "Bearer backend-secret"}


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
        headers=authenticated_headers(),
        json={"message": "  Hello, Mordred.  "},
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Hello from Mordred.",
        "model": "test-model",
    }
    assert fake_client.system_prompt
    assert fake_client.user_input == "Hello, Mordred."
    assert fake_client.history == ()


def test_chat_rejects_blank_message() -> None:
    app.dependency_overrides[get_chat_client] = SuccessfulChatClient

    response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_chat_rejects_invalid_conversation_id() -> None:
    app.dependency_overrides[get_chat_client] = SuccessfulChatClient

    response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "Hello.",
            "conversation_id": "invalid conversation id",
        },
    )

    assert response.status_code == 422


def test_same_conversation_receives_previous_exchange() -> None:
    fake_client = SuccessfulChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake_client

    first_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "My codename is Cerberus.",
            "conversation_id": "conversation-a",
        },
    )

    assert first_response.status_code == 200
    assert fake_client.history == ()

    second_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "What codename did I give you?",
            "conversation_id": "conversation-a",
        },
    )

    assert second_response.status_code == 200
    assert [
        (message.role, message.content)
        for message in fake_client.history
    ] == [
        ("user", "My codename is Cerberus."),
        ("assistant", "Hello from Mordred."),
    ]


def test_different_conversations_are_isolated() -> None:
    fake_client = SuccessfulChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake_client

    first_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "My codename is Cerberus.",
            "conversation_id": "conversation-a",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "What is the codename?",
            "conversation_id": "conversation-b",
        },
    )

    assert second_response.status_code == 200
    assert fake_client.history == ()


def test_stateless_request_does_not_create_conversation_history() -> None:
    fake_client = SuccessfulChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake_client

    stateless_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={"message": "My codename is Cerberus."},
    )

    assert stateless_response.status_code == 200

    conversation_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "What is the codename?",
            "conversation_id": "conversation-a",
        },
    )

    assert conversation_response.status_code == 200
    assert fake_client.history == ()


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
        headers=authenticated_headers(),
        json={
            "message": "Hello.",
            "conversation_id": "conversation-a",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "reason": reason,
    }


def test_failed_generation_does_not_create_history() -> None:
    app.dependency_overrides[get_chat_client] = (
        lambda: FailingChatClient(InferenceTimeoutError())
    )

    failed_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "Remember Cerberus.",
            "conversation_id": "conversation-a",
        },
    )

    assert failed_response.status_code == 503

    successful_client = SuccessfulChatClient()
    app.dependency_overrides[get_chat_client] = (
        lambda: successful_client
    )

    retry_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "What should you remember?",
            "conversation_id": "conversation-a",
        },
    )

    assert retry_response.status_code == 200
    assert successful_client.history == ()


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
        headers=authenticated_headers(),
        json={
            "message": "Hello.",
            "conversation_id": "conversation-a",
        },
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "reason": "prompt_configuration_error",
    }


def test_reset_rejects_missing_backend_credential() -> None:
    response = client.delete("/conversations/conversation-a")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_reset_rejects_invalid_conversation_id() -> None:
    response = client.delete(
        "/conversations/invalid conversation id",
        headers=authenticated_headers(),
    )

    assert response.status_code == 422


def test_reset_clears_selected_conversation() -> None:
    fake_client = SuccessfulChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake_client

    first_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "Remember Cerberus.",
            "conversation_id": "conversation-a",
        },
    )
    assert first_response.status_code == 200

    reset_response = client.delete(
        "/conversations/conversation-a",
        headers=authenticated_headers(),
    )

    assert reset_response.status_code == 200
    assert reset_response.json() == {
        "status": "reset",
        "conversation_id": "conversation-a",
    }

    after_reset_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "What should you remember?",
            "conversation_id": "conversation-a",
        },
    )

    assert after_reset_response.status_code == 200
    assert fake_client.history == ()


def test_reset_does_not_clear_another_conversation() -> None:
    fake_client = SuccessfulChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake_client

    first_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "Remember Alpha.",
            "conversation_id": "conversation-a",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "Remember Beta.",
            "conversation_id": "conversation-b",
        },
    )
    assert second_response.status_code == 200

    reset_response = client.delete(
        "/conversations/conversation-a",
        headers=authenticated_headers(),
    )
    assert reset_response.status_code == 200

    conversation_b_response = client.post(
        "/chat",
        headers=authenticated_headers(),
        json={
            "message": "What should you remember?",
            "conversation_id": "conversation-b",
        },
    )

    assert conversation_b_response.status_code == 200
    assert [
        (message.role, message.content)
        for message in fake_client.history
    ] == [
        ("user", "Remember Beta."),
        ("assistant", "Hello from Mordred."),
    ]


def test_reset_unknown_conversation_is_idempotent() -> None:
    first_response = client.delete(
        "/conversations/unknown-conversation",
        headers=authenticated_headers(),
    )
    second_response = client.delete(
        "/conversations/unknown-conversation",
        headers=authenticated_headers(),
    )

    expected_body = {
        "status": "reset",
        "conversation_id": "unknown-conversation",
    }

    assert first_response.status_code == 200
    assert first_response.json() == expected_body
    assert second_response.status_code == 200
    assert second_response.json() == expected_body
