import asyncio
import json

import httpx
import pytest

from app.telegram_adapter.backend import (
    BackendAuthenticationError,
    BackendProtocolError,
    BackendTimeoutError,
    InferenceUnavailableError,
    MordredBackendClient,
)
from app.telegram_adapter.config import TelegramSettings


def settings() -> TelegramSettings:
    return TelegramSettings(
        bot_token="telegram-secret",
        allowed_user_ids="123",
        backend_base_url="http://backend:8000",
        backend_api_key="backend-secret",
    )


def test_chat_sends_authenticated_backend_request_once() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"reply": "Hello.", "model": "test-model"},
        )

    client = MordredBackendClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        client.chat(
            message="Study this.",
            conversation_id="telegram:user:123",
        )
    )

    assert result.reply == "Hello."
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert request.url == "http://backend:8000/chat"
    assert request.headers["authorization"] == "Bearer backend-secret"
    assert json.loads(request.content) == {
        "message": "Study this.",
        "conversation_id": "telegram:user:123",
    }


def test_reset_calls_authenticated_reset_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url == (
            "http://backend:8000/conversations/telegram:user:123"
        )
        assert request.headers["authorization"] == "Bearer backend-secret"
        return httpx.Response(
            200,
            json={
                "status": "reset",
                "conversation_id": "telegram:user:123",
            },
        )

    client = MordredBackendClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        client.reset(conversation_id="telegram:user:123")
    )

    assert result.status == "reset"


@pytest.mark.parametrize("status_code", [401, 403])
def test_backend_authentication_failure_is_controlled(
    status_code: int,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status_code)
    )
    client = MordredBackendClient(settings(), transport=transport)

    with pytest.raises(BackendAuthenticationError):
        asyncio.run(
            client.chat(
                message="Hello.",
                conversation_id="telegram:user:123",
            )
        )


def test_inference_unavailable_reason_is_preserved() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            503,
            json={"status": "unavailable", "reason": "timeout"},
        )
    )
    client = MordredBackendClient(settings(), transport=transport)

    with pytest.raises(InferenceUnavailableError) as raised:
        asyncio.run(
            client.chat(
                message="Hello.",
                conversation_id="telegram:user:123",
            )
        )

    assert raised.value.reason == "timeout"


def test_prompt_configuration_error_reason_is_preserved() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            503,
            json={
                "status": "unavailable",
                "reason": "prompt_configuration_error",
            },
        )
    )
    client = MordredBackendClient(settings(), transport=transport)

    with pytest.raises(InferenceUnavailableError) as raised:
        asyncio.run(
            client.chat(
                message="Hello.",
                conversation_id="telegram:user:123",
            )
        )

    assert raised.value.reason == "prompt_configuration_error"


def test_timeout_is_not_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("test timeout", request=request)

    client = MordredBackendClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(BackendTimeoutError):
        asyncio.run(
            client.chat(
                message="Hello.",
                conversation_id="telegram:user:123",
            )
        )

    assert calls == 1


def test_malformed_success_response_is_rejected() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"unexpected": True})
    )
    client = MordredBackendClient(settings(), transport=transport)

    with pytest.raises(BackendProtocolError):
        asyncio.run(
            client.chat(
                message="Hello.",
                conversation_id="telegram:user:123",
            )
        )


def test_status_reports_available_backend_and_inference() -> None:
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)

        if request.url.path == "/health":
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "service": "mordred-backend",
                    "version": "0.3.0",
                },
            )

        return httpx.Response(
            200,
            json={
                "status": "ready",
                "inference": "available",
                "model": "test-model",
            },
        )

    client = MordredBackendClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.status())

    assert requested_paths == ["/health", "/ready"]
    assert result.backend_available is True
    assert result.inference_available is True
    assert result.model == "test-model"
    assert result.reason is None


def test_status_distinguishes_offline_inference_from_backend_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "service": "mordred-backend",
                    "version": "0.3.0",
                },
            )

        return httpx.Response(
            503,
            json={
                "status": "not_ready",
                "inference": "unavailable",
                "reason": "inference_unavailable",
            },
        )

    client = MordredBackendClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.status())

    assert result.backend_available is True
    assert result.inference_available is False
    assert result.model is None
    assert result.reason == "inference_unavailable"
