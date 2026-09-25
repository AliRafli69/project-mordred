from typing import Any, Protocol

from app.telegram_adapter.backend import (
    BackendAuthenticationError,
    BackendProtocolError,
    BackendStatus,
    BackendTimeoutError,
    BackendUnavailableError,
    InferenceUnavailableError,
)
from app.telegram_adapter.identity import (
    conversation_id_for_user,
    is_authorized_private_chat,
)
from app.telegram_adapter.replies import split_reply


START_TEXT = (
    "Mordred is ready. Send a text message to chat.\n\n"
    "Use /help to see available commands."
)

HELP_TEXT = (
    "Available commands:\n"
    "/start — introduce the bot\n"
    "/help — show this help\n"
    "/status — check the backend and local inference\n"
    "/reset — clear this conversation's temporary backend context\n\n"
    "Send ordinary text to chat with Mordred."
)

UNAUTHORIZED_TEXT = "You are not authorized to use this bot."

PRIVATE_ONLY_TEXT = "Mordred accepts messages only in a private chat."

UNSUPPORTED_TEXT = (
    "This input is not supported. Send a plain text message or use /help."
)


class TelegramSender(Protocol):
    async def send_message(self, *, chat_id: int, text: str) -> None:
        ...


class BackendClient(Protocol):
    async def chat(
        self,
        *,
        message: str,
        conversation_id: str,
    ) -> Any:
        ...

    async def reset(self, *, conversation_id: str) -> Any:
        ...

    async def status(self) -> BackendStatus:
        ...


async def send_text(
    telegram: TelegramSender,
    *,
    chat_id: int,
    text: str,
) -> None:
    for chunk in split_reply(text):
        await telegram.send_message(chat_id=chat_id, text=chunk)


def command_name(text: str) -> str | None:
    first_token = text.split(maxsplit=1)[0]

    if not first_token.startswith("/"):
        return None

    return first_token.split("@", maxsplit=1)[0].lower()


def backend_error_text(error: Exception) -> str:
    if isinstance(error, InferenceUnavailableError):
        if error.reason == "prompt_configuration_error":
            return (
                "Mordred's personality configuration is unavailable. "
                "Check the backend prompt configuration."
            )

        if error.reason == "timeout":
            return (
                "Local inference timed out. The G14 may be asleep, "
                "disconnected, or still generating. Please try again later."
            )

        return (
            "Local inference is unavailable. Check that the G14 is awake, "
            "connected, and running LM Studio."
        )

    if isinstance(error, BackendTimeoutError):
        return (
            "The Mordred backend did not respond in time. "
            "The request was not retried automatically."
        )

    if isinstance(error, BackendAuthenticationError):
        return (
            "The Telegram adapter could not authenticate with the backend. "
            "Check the server configuration."
        )

    if isinstance(error, BackendProtocolError):
        return "The Mordred backend returned an invalid response."

    return "The Mordred backend is unavailable. Please try again later."


async def handle_update(
    update: dict[str, Any],
    *,
    telegram: TelegramSender,
    backend: BackendClient,
    allowed_user_ids: frozenset[int],
) -> None:
    """Handle one Telegram update without duplicating backend state."""

    message = update.get("message")
    if not isinstance(message, dict):
        return

    chat = message.get("chat")
    sender = message.get("from")

    if not isinstance(chat, dict) or not isinstance(sender, dict):
        return

    chat_id = chat.get("id")
    chat_type = chat.get("type")
    user_id = sender.get("id")

    if (
        isinstance(chat_id, bool)
        or not isinstance(chat_id, int)
        or not isinstance(chat_type, str)
        or isinstance(user_id, bool)
        or not isinstance(user_id, int)
    ):
        return

    if chat_type != "private":
        await send_text(
            telegram,
            chat_id=chat_id,
            text=PRIVATE_ONLY_TEXT,
        )
        return

    if not is_authorized_private_chat(
        user_id=user_id,
        chat_type=chat_type,
        allowed_user_ids=allowed_user_ids,
    ):
        await send_text(
            telegram,
            chat_id=chat_id,
            text=UNAUTHORIZED_TEXT,
        )
        return

    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        await send_text(
            telegram,
            chat_id=chat_id,
            text=UNSUPPORTED_TEXT,
        )
        return

    text = text.strip()
    command = command_name(text)
    conversation_id = conversation_id_for_user(user_id)

    if command == "/start":
        await send_text(telegram, chat_id=chat_id, text=START_TEXT)
        return

    if command == "/help":
        await send_text(telegram, chat_id=chat_id, text=HELP_TEXT)
        return

    if command == "/status":
        try:
            status = await backend.status()
        except (
            BackendAuthenticationError,
            BackendProtocolError,
            BackendTimeoutError,
            BackendUnavailableError,
        ) as exc:
            response_text = backend_error_text(exc)
        else:
            if status.inference_available:
                response_text = (
                    "Backend: available\n"
                    "Local inference: available\n"
                    f"Model: {status.model}"
                )
            else:
                response_text = (
                    "Backend: available\n"
                    "Local inference: unavailable\n"
                    f"Reason: {status.reason}"
                )

        await send_text(
            telegram,
            chat_id=chat_id,
            text=response_text,
        )
        return

    if command == "/reset":
        try:
            await backend.reset(conversation_id=conversation_id)
        except (
            BackendAuthenticationError,
            BackendProtocolError,
            BackendTimeoutError,
            BackendUnavailableError,
        ) as exc:
            response_text = backend_error_text(exc)
        else:
            response_text = (
                "Temporary backend conversation context was cleared. "
                "Existing Telegram messages were not deleted."
            )

        await send_text(
            telegram,
            chat_id=chat_id,
            text=response_text,
        )
        return

    if command is not None:
        await send_text(telegram, chat_id=chat_id, text=HELP_TEXT)
        return

    try:
        response = await backend.chat(
            message=text,
            conversation_id=conversation_id,
        )
    except (
        BackendAuthenticationError,
        BackendProtocolError,
        BackendTimeoutError,
        BackendUnavailableError,
        InferenceUnavailableError,
    ) as exc:
        response_text = backend_error_text(exc)
    else:
        response_text = response.reply

    await send_text(
        telegram,
        chat_id=chat_id,
        text=response_text,
    )
