import asyncio
import json
from collections.abc import Callable

import httpx
import pytest

from app.chat import LMStudioChatClient
from app.config import Settings
from app.inference import (
    InferenceAuthenticationError,
    InferenceMalformedResponseError,
    InferenceTimeoutError,
    InferenceUnavailableError,
)


def make_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> LMStudioChatClient:
    settings = Settings(
        lm_studio_base_url="http://example.invalid:1234",
        lm_studio_api_key="inference-secret",
        lm_studio_model="test-model",
        backend_api_key="backend-secret",
    )
    transport = httpx.MockTransport(handler)

    return LMStudioChatClient(settings=settings, transport=transport)


def test_generate_sends_server_controlled_chat_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "http://example.invalid:1234/api/v1/chat"
        assert request.headers["Authorization"] == "Bearer inference-secret"

        payload = json.loads(request.content)

        assert payload == {
            "model": "test-model",
            "system_prompt": "Combined personality.",
            "input": "Hello, Mordred.",
            "reasoning": "off",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "stream": False,
            "store": False,
        }

        return httpx.Response(
            status_code=200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": "Hello! How can I help?",
                    }
                ]
            },
        )

    client = make_client(handler)

    response = asyncio.run(
        client.generate(
            system_prompt="Combined personality.",
            user_input="Hello, Mordred.",
        )
    )

    assert response == "Hello! How can I help?"


def test_generate_handles_offline_inference() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = make_client(handler)

    with pytest.raises(InferenceUnavailableError):
        asyncio.run(
            client.generate(
                system_prompt="Personality.",
                user_input="Hello.",
            )
        )


def test_generate_handles_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    client = make_client(handler)

    with pytest.raises(InferenceTimeoutError):
        asyncio.run(
            client.generate(
                system_prompt="Personality.",
                user_input="Hello.",
            )
        )


def test_generate_handles_authentication_rejection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=401)

    client = make_client(handler)

    with pytest.raises(InferenceAuthenticationError):
        asyncio.run(
            client.generate(
                system_prompt="Personality.",
                user_input="Hello.",
            )
        )


def test_generate_rejects_response_without_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"output": []},
        )

    client = make_client(handler)

    with pytest.raises(InferenceMalformedResponseError):
        asyncio.run(
            client.generate(
                system_prompt="Personality.",
                user_input="Hello.",
            )
        )
