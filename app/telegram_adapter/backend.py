from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.telegram_adapter.config import TelegramSettings


class BackendError(Exception):
    """Base class for controlled backend-client failures."""


class BackendTimeoutError(BackendError):
    """The backend request exceeded its configured timeout."""


class BackendUnavailableError(BackendError):
    """The backend could not be reached or returned an unexpected failure."""


class BackendAuthenticationError(BackendError):
    """The adapter's backend credential was rejected."""


class BackendProtocolError(BackendError):
    """The backend returned an invalid response."""


class InferenceUnavailableError(BackendError):
    """The backend reported that inference is unavailable."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ChatResponse(BaseModel):
    reply: str
    model: str


class ResetResponse(BaseModel):
    status: str
    conversation_id: str


class UnavailableResponse(BaseModel):
    status: str
    reason: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    inference: str
    model: str


class BackendStatus(BaseModel):
    backend_available: bool
    inference_available: bool
    model: str | None = None
    reason: str | None = None


class MordredBackendClient:
    """Authenticated asynchronous client for the Mordred backend."""

    def __init__(
        self,
        settings: TelegramSettings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": (
                "Bearer "
                f"{self._settings.backend_api_key.get_secret_value()}"
            )
        }

    def _timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            timeout=self._settings.read_timeout_seconds,
            connect=self._settings.connect_timeout_seconds,
        )

    async def chat(
        self,
        *,
        message: str,
        conversation_id: str,
    ) -> ChatResponse:
        response = await self._request(
            "POST",
            "/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
            },
        )

        if response.status_code == 503:
            try:
                unavailable = UnavailableResponse.model_validate(
                    response.json()
                )
            except (ValueError, TypeError, ValidationError) as exc:
                raise BackendProtocolError from exc

            raise InferenceUnavailableError(unavailable.reason)

        self._raise_for_status(response)

        try:
            return ChatResponse.model_validate(response.json())
        except (ValueError, TypeError, ValidationError) as exc:
            raise BackendProtocolError from exc

    async def reset(self, *, conversation_id: str) -> ResetResponse:
        response = await self._request(
            "DELETE",
            f"/conversations/{conversation_id}",
        )
        self._raise_for_status(response)

        try:
            reset = ResetResponse.model_validate(response.json())
        except (ValueError, TypeError, ValidationError) as exc:
            raise BackendProtocolError from exc

        if (
            reset.status != "reset"
            or reset.conversation_id != conversation_id
        ):
            raise BackendProtocolError

        return reset

    async def status(self) -> BackendStatus:
        health_response = await self._request("GET", "/health")
        self._raise_for_status(health_response)

        try:
            health = HealthResponse.model_validate(
                health_response.json()
            )
        except (ValueError, TypeError, ValidationError) as exc:
            raise BackendProtocolError from exc

        if health.status != "ok":
            raise BackendProtocolError

        ready_response = await self._request("GET", "/ready")

        if ready_response.status_code == 503:
            try:
                unavailable = UnavailableResponse.model_validate(
                    ready_response.json()
                )
            except (ValueError, TypeError, ValidationError) as exc:
                raise BackendProtocolError from exc

            return BackendStatus(
                backend_available=True,
                inference_available=False,
                reason=unavailable.reason,
            )

        self._raise_for_status(ready_response)

        try:
            ready = ReadyResponse.model_validate(ready_response.json())
        except (ValueError, TypeError, ValidationError) as exc:
            raise BackendProtocolError from exc

        if ready.status != "ready" or ready.inference != "available":
            raise BackendProtocolError

        return BackendStatus(
            backend_available=True,
            inference_available=True,
            model=ready.model,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        base_url = str(self._settings.backend_base_url).rstrip("/")
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout(),
                transport=self._transport,
            ) as client:
                return await client.request(
                    method,
                    f"{base_url}{path}",
                    headers=self._headers(),
                    json=json,
                )
        except httpx.TimeoutException as exc:
            raise BackendTimeoutError from exc
        except httpx.RequestError as exc:
            raise BackendUnavailableError from exc

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code in {401, 403}:
            raise BackendAuthenticationError

        if response.status_code < 200 or response.status_code >= 300:
            raise BackendUnavailableError
