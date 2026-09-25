import asyncio
import json

import httpx
import pytest

from app.telegram_adapter.config import TelegramSettings
from app.telegram_adapter.telegram import (
    TelegramBotClient,
    TelegramProtocolError,
    TelegramTimeoutError,
)


def settings() -> TelegramSettings:
    return TelegramSettings(
        bot_token="test-token",
        allowed_user_ids="123",
        backend_api_key="backend-secret",
        poll_timeout_seconds=30,
    )


def test_get_updates_uses_long_polling_and_offset() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == (
            "https://api.telegram.org/bottest-token/getUpdates"
        )
        assert json.loads(request.content) == {
            "timeout": 30,
            "allowed_updates": ["message"],
            "offset": 42,
        }
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [{"update_id": 42, "message": {}}],
            },
        )

    client = TelegramBotClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    updates = asyncio.run(client.get_updates(offset=42))

    assert updates[0]["update_id"] == 42


def test_delete_webhook_preserves_pending_updates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/deleteWebhook")
        assert json.loads(request.content) == {
            "drop_pending_updates": False
        }
        return httpx.Response(200, json={"ok": True, "result": True})

    client = TelegramBotClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(client.delete_webhook())


def test_send_message_uses_target_chat_and_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/sendMessage")
        assert json.loads(request.content) == {
            "chat_id": 123,
            "text": "Hello.",
        }
        return httpx.Response(
            200,
            json={"ok": True, "result": {"message_id": 1}},
        )

    client = TelegramBotClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(client.send_message(chat_id=123, text="Hello."))


def test_failed_telegram_response_is_controlled() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"ok": False, "description": "test failure"},
        )
    )
    client = TelegramBotClient(settings(), transport=transport)

    with pytest.raises(TelegramProtocolError):
        asyncio.run(client.get_updates(offset=None))


def test_telegram_timeout_is_controlled() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("test timeout", request=request)

    client = TelegramBotClient(
        settings(),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(TelegramTimeoutError):
        asyncio.run(client.get_updates(offset=None))
