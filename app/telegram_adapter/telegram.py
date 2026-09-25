from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.telegram_adapter.config import TelegramSettings
from app.telegram_adapter.replies import TELEGRAM_TEXT_LIMIT


class TelegramError(Exception):
    """Base class for controlled Telegram API failures."""


class TelegramTimeoutError(TelegramError):
    """A Telegram API request timed out."""


class TelegramUnavailableError(TelegramError):
    """Telegram could not be reached."""


class TelegramProtocolError(TelegramError):
    """Telegram returned an unsuccessful or malformed response."""


class TelegramResponse(BaseModel):
    ok: bool
    result: Any = None
    description: str | None = None


class TelegramBotClient:
    """Minimal asynchronous Telegram Bot API client."""

    def __init__(
        self,
        settings: TelegramSettings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        token = settings.bot_token.get_secret_value()
        self._base_url = f"https://api.telegram.org/bot{token}"
        self._poll_timeout = settings.poll_timeout_seconds
        self._connect_timeout = settings.connect_timeout_seconds
        self._transport = transport

    async def delete_webhook(self) -> None:
        response = await self._request(
            "deleteWebhook",
            json={"drop_pending_updates": False},
        )

        if response.result is not True:
            raise TelegramProtocolError

    async def get_updates(
        self,
        *,
        offset: int | None,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": self._poll_timeout,
            "allowed_updates": ["message"],
        }
        if offset is not None:
            payload["offset"] = offset

        response = await self._request(
            "getUpdates",
            json=payload,
            read_timeout=float(self._poll_timeout + 10),
        )

        if not isinstance(response.result, list) or any(
            not isinstance(update, dict) for update in response.result
        ):
            raise TelegramProtocolError

        return response.result

    async def send_message(self, *, chat_id: int, text: str) -> None:
        if not text or len(text) > TELEGRAM_TEXT_LIMIT:
            raise ValueError("Telegram message text has an invalid length")

        response = await self._request(
            "sendMessage",
            json={"chat_id": chat_id, "text": text},
        )

        if not isinstance(response.result, dict):
            raise TelegramProtocolError

    async def _request(
        self,
        method: str,
        *,
        json: dict[str, Any],
        read_timeout: float = 30.0,
    ) -> TelegramResponse:
        timeout = httpx.Timeout(
            timeout=read_timeout,
            connect=self._connect_timeout,
        )

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                transport=self._transport,
            ) as client:
                raw_response = await client.post(
                    f"{self._base_url}/{method}",
                    json=json,
                )
        except httpx.TimeoutException as exc:
            raise TelegramTimeoutError from exc
        except httpx.RequestError as exc:
            raise TelegramUnavailableError from exc

        if raw_response.status_code != 200:
            raise TelegramProtocolError

        try:
            response = TelegramResponse.model_validate(
                raw_response.json()
            )
        except (ValueError, TypeError, ValidationError) as exc:
            raise TelegramProtocolError from exc

        if not response.ok:
            raise TelegramProtocolError

        return response
