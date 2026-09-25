import asyncio
from types import SimpleNamespace
from typing import Any

from app.telegram_adapter.backend import (
    BackendStatus,
    InferenceUnavailableError,
)
from app.telegram_adapter.handler import handle_update


class FakeTelegram:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))


class FakeBackend:
    def __init__(self) -> None:
        self.chat_calls: list[tuple[str, str]] = []
        self.reset_calls: list[str] = []
        self.status_calls = 0
        self.chat_error: Exception | None = None
        self.status_result = BackendStatus(
            backend_available=True,
            inference_available=True,
            model="test-model",
        )

    async def chat(
        self,
        *,
        message: str,
        conversation_id: str,
    ) -> Any:
        self.chat_calls.append((message, conversation_id))

        if self.chat_error is not None:
            raise self.chat_error

        return SimpleNamespace(reply="Mordred reply.")

    async def reset(self, *, conversation_id: str) -> Any:
        self.reset_calls.append(conversation_id)
        return SimpleNamespace(
            status="reset",
            conversation_id=conversation_id,
        )

    async def status(self) -> BackendStatus:
        self.status_calls += 1
        return self.status_result


def update(
    *,
    user_id: int = 123,
    chat_id: int = 123,
    chat_type: str = "private",
    text: str | None = "Hello.",
) -> dict[str, Any]:
    message: dict[str, Any] = {
        "from": {"id": user_id},
        "chat": {"id": chat_id, "type": chat_type},
    }

    if text is not None:
        message["text"] = text
    else:
        message["photo"] = [{"file_id": "test"}]

    return {"update_id": 1, "message": message}


def run_handler(
    incoming: dict[str, Any],
    telegram: FakeTelegram,
    backend: FakeBackend,
) -> None:
    asyncio.run(
        handle_update(
            incoming,
            telegram=telegram,
            backend=backend,
            allowed_user_ids=frozenset({123}),
        )
    )


def test_unauthorized_user_is_rejected_before_backend_call() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()

    run_handler(update(user_id=999), telegram, backend)

    assert backend.chat_calls == []
    assert backend.reset_calls == []
    assert backend.status_calls == 0
    assert "not authorized" in telegram.messages[0][1]


def test_group_message_is_rejected_before_backend_call() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()

    run_handler(
        update(chat_id=-1001, chat_type="supergroup"),
        telegram,
        backend,
    )

    assert backend.chat_calls == []
    assert backend.reset_calls == []
    assert backend.status_calls == 0
    assert "private chat" in telegram.messages[0][1]


def test_start_does_not_call_backend() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()

    run_handler(update(text="/start"), telegram, backend)

    assert backend.chat_calls == []
    assert "Mordred is ready" in telegram.messages[0][1]


def test_text_calls_backend_with_stable_conversation_id() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()

    run_handler(update(text="  Explain recursion.  "), telegram, backend)

    assert backend.chat_calls == [
        ("Explain recursion.", "telegram:user:123")
    ]
    assert telegram.messages == [(123, "Mordred reply.")]


def test_reset_calls_backend_and_explains_scope() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()

    run_handler(update(text="/reset"), telegram, backend)

    assert backend.reset_calls == ["telegram:user:123"]
    assert "backend conversation context was cleared" in (
        telegram.messages[0][1]
    )
    assert "Telegram messages were not deleted" in (
        telegram.messages[0][1]
    )


def test_status_reports_offline_inference() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()
    backend.status_result = BackendStatus(
        backend_available=True,
        inference_available=False,
        reason="inference_unavailable",
    )

    run_handler(update(text="/status"), telegram, backend)

    assert backend.status_calls == 1
    assert "Backend: available" in telegram.messages[0][1]
    assert "Local inference: unavailable" in telegram.messages[0][1]


def test_unsupported_input_does_not_call_backend() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()

    run_handler(update(text=None), telegram, backend)

    assert backend.chat_calls == []
    assert "not supported" in telegram.messages[0][1]


def test_inference_failure_has_clear_user_message() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()
    backend.chat_error = InferenceUnavailableError(
        "inference_unavailable"
    )

    run_handler(update(text="Hello."), telegram, backend)

    assert len(backend.chat_calls) == 1
    assert "G14" in telegram.messages[0][1]
    assert "LM Studio" in telegram.messages[0][1]


def test_prompt_configuration_failure_points_to_backend_prompt() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()
    backend.chat_error = InferenceUnavailableError(
        "prompt_configuration_error"
    )

    run_handler(update(text="Hello."), telegram, backend)

    assert len(backend.chat_calls) == 1
    assert telegram.messages == [
        (
            123,
            "Mordred's personality configuration is unavailable. "
            "Check the backend prompt configuration.",
        )
    ]


def test_long_backend_reply_is_split_in_order() -> None:
    telegram = FakeTelegram()
    backend = FakeBackend()

    async def long_chat(
        *,
        message: str,
        conversation_id: str,
    ) -> Any:
        return SimpleNamespace(reply="x" * 9000)

    backend.chat = long_chat  # type: ignore[method-assign]

    run_handler(update(text="Long answer."), telegram, backend)

    assert [len(text) for _, text in telegram.messages] == [
        4096,
        4096,
        808,
    ]
    assert "".join(text for _, text in telegram.messages) == "x" * 9000
