import asyncio
from types import SimpleNamespace
from typing import Any

from app.telegram_adapter.runner import process_updates
from app.telegram_adapter.telegram import TelegramUnavailableError


class RecordingBackend:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def chat(
        self,
        *,
        message: str,
        conversation_id: str,
    ) -> Any:
        self.messages.append(message)
        await asyncio.sleep(0)
        return SimpleNamespace(reply=f"Reply: {message}")

    async def reset(self, *, conversation_id: str) -> Any:
        raise AssertionError("reset was not expected")

    async def status(self) -> Any:
        raise AssertionError("status was not expected")


class RecordingTelegram:
    def __init__(self, *, fail_first_send: bool = False) -> None:
        self.messages: list[str] = []
        self._fail_first_send = fail_first_send

    async def send_message(self, *, chat_id: int, text: str) -> None:
        if self._fail_first_send:
            self._fail_first_send = False
            raise TelegramUnavailableError

        self.messages.append(text)


def update(update_id: int, text: str) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {
            "from": {"id": 123},
            "chat": {"id": 123, "type": "private"},
            "text": text,
        },
    }


def test_updates_are_processed_in_received_order() -> None:
    telegram = RecordingTelegram()
    backend = RecordingBackend()

    next_offset = asyncio.run(
        process_updates(
            [
                update(10, "First"),
                update(11, "Second"),
            ],
            offset=None,
            telegram=telegram,  # type: ignore[arg-type]
            backend=backend,  # type: ignore[arg-type]
            allowed_user_ids=frozenset({123}),
        )
    )

    assert backend.messages == ["First", "Second"]
    assert telegram.messages == ["Reply: First", "Reply: Second"]
    assert next_offset == 12


def test_send_failure_is_consumed_without_repeating_backend_call() -> None:
    telegram = RecordingTelegram(fail_first_send=True)
    backend = RecordingBackend()

    next_offset = asyncio.run(
        process_updates(
            [update(20, "Process once")],
            offset=None,
            telegram=telegram,  # type: ignore[arg-type]
            backend=backend,  # type: ignore[arg-type]
            allowed_user_ids=frozenset({123}),
        )
    )

    assert backend.messages == ["Process once"]
    assert next_offset == 21


def test_existing_higher_offset_is_not_moved_backwards() -> None:
    telegram = RecordingTelegram()
    backend = RecordingBackend()

    next_offset = asyncio.run(
        process_updates(
            [update(10, "Old update")],
            offset=50,
            telegram=telegram,  # type: ignore[arg-type]
            backend=backend,  # type: ignore[arg-type]
            allowed_user_ids=frozenset({123}),
        )
    )

    assert next_offset == 50


def test_http_client_request_logging_is_suppressed() -> None:
    import logging

    from app.telegram_adapter.runner import configure_logging

    configure_logging()

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
