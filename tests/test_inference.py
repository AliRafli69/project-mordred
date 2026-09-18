import asyncio
from collections.abc import Callable

import httpx
import pytest

from app.config import Settings
from app.inference import (
    InferenceAuthenticationError,
    InferenceMalformedResponseError,
    InferenceModelUnavailableError,
    InferenceTimeoutError,
    InferenceUnavailableError,
    LMStudioClient,
)


def make_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> LMStudioClient:
    settings = Settings(
        lm_studio_base_url="http://example.invalid:1234",
        lm_studio_api_key="inference-secret",
        lm_studio_model="test-model",
        backend_api_key="backend-secret",
    )
    transport = httpx.MockTransport(handler)

    return LMStudioClient(settings=settings, transport=transport)


def test_readiness_succeeds_when_configured_model_is_available() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://example.invalid:1234/v1/models"
        assert request.headers["Authorization"] == "Bearer inference-secret"

        return httpx.Response(
            status_code=200,
            json={"data": [{"id": "test-model"}]},
        )

    client = make_client(handler)

    assert asyncio.run(client.check_ready()) == "test-model"


def test_readiness_handles_offline_inference() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = make_client(handler)

    with pytest.raises(InferenceUnavailableError):
        asyncio.run(client.check_ready())


def test_readiness_handles_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    client = make_client(handler)

    with pytest.raises(InferenceTimeoutError):
        asyncio.run(client.check_ready())


def test_readiness_handles_authentication_rejection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=401)

    client = make_client(handler)

    with pytest.raises(InferenceAuthenticationError):
        asyncio.run(client.check_ready())


def test_readiness_rejects_malformed_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"unexpected": []},
        )

    client = make_client(handler)

    with pytest.raises(InferenceMalformedResponseError):
        asyncio.run(client.check_ready())


def test_readiness_detects_missing_configured_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"data": [{"id": "different-model"}]},
        )

    client = make_client(handler)

    with pytest.raises(InferenceModelUnavailableError):
        asyncio.run(client.check_ready())
