from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.config import Settings


class InferenceError(Exception):
    """Base exception for controlled inference failures."""


class InferenceUnavailableError(InferenceError):
    """LM Studio cannot be reached or returned an unexpected HTTP status."""


class InferenceTimeoutError(InferenceError):
    """LM Studio did not respond within the configured timeout."""


class InferenceAuthenticationError(InferenceError):
    """LM Studio rejected the configured credential."""


class InferenceMalformedResponseError(InferenceError):
    """LM Studio returned a response that did not match the expected schema."""


class InferenceModelUnavailableError(InferenceError):
    """LM Studio responded, but the configured model was not available."""


class ModelRecord(BaseModel):
    id: str


class ModelsResponse(BaseModel):
    data: list[ModelRecord]


class LMStudioClient:
    """Bounded asynchronous client for the private LM Studio API."""

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def check_ready(self) -> str:
        """Return the configured model ID when LM Studio is ready."""

        endpoint = (
            f"{str(self._settings.lm_studio_base_url).rstrip('/')}/v1/models"
        )
        timeout = httpx.Timeout(
            timeout=self._settings.read_timeout_seconds,
            connect=self._settings.connect_timeout_seconds,
        )
        headers = {
            "Authorization": (
                "Bearer "
                f"{self._settings.lm_studio_api_key.get_secret_value()}"
            )
        }

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                transport=self._transport,
            ) as client:
                response = await client.get(endpoint, headers=headers)
        except httpx.TimeoutException as exc:
            raise InferenceTimeoutError from exc
        except httpx.RequestError as exc:
            raise InferenceUnavailableError from exc

        if response.status_code in {401, 403}:
            raise InferenceAuthenticationError

        if response.status_code != 200:
            raise InferenceUnavailableError

        try:
            payload: Any = response.json()
            models = ModelsResponse.model_validate(payload)
        except (ValueError, TypeError, ValidationError) as exc:
            raise InferenceMalformedResponseError from exc

        configured_model = self._settings.lm_studio_model

        if not any(model.id == configured_model for model in models.data):
            raise InferenceModelUnavailableError

        return configured_model
