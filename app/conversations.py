from dataclasses import dataclass
from threading import RLock
from typing import Literal, Protocol


Role = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    role: Role
    content: str


class ConversationStore(Protocol):
    """Temporary conversation-state interface."""

    def get_messages(
        self,
        conversation_id: str,
    ) -> tuple[ConversationMessage, ...]:
        ...

    def append_exchange(
        self,
        conversation_id: str,
        *,
        user_message: str,
        assistant_message: str,
    ) -> None:
        ...

    def clear(self, conversation_id: str) -> None:
        ...


class InMemoryConversationStore:
    """Thread-safe, bounded, non-persistent conversation storage."""

    def __init__(
        self,
        *,
        max_messages: int = 12,
        max_characters: int = 24_000,
    ) -> None:
        if max_messages < 2 or max_messages % 2 != 0:
            raise ValueError("max_messages must be an even integer of at least 2")

        if max_characters < 1:
            raise ValueError("max_characters must be positive")

        self._max_messages = max_messages
        self._max_characters = max_characters
        self._conversations: dict[str, list[ConversationMessage]] = {}
        self._lock = RLock()

    def get_messages(
        self,
        conversation_id: str,
    ) -> tuple[ConversationMessage, ...]:
        with self._lock:
            return tuple(self._conversations.get(conversation_id, ()))

    def append_exchange(
        self,
        conversation_id: str,
        *,
        user_message: str,
        assistant_message: str,
    ) -> None:
        exchange = [
            ConversationMessage(role="user", content=user_message),
            ConversationMessage(
                role="assistant",
                content=assistant_message,
            ),
        ]
        exchange_characters = sum(
            len(message.content) for message in exchange
        )

        if exchange_characters > self._max_characters:
            raise ValueError(
                "A single conversation exchange exceeds the character limit"
            )

        with self._lock:
            messages = [
                *self._conversations.get(conversation_id, ()),
                *exchange,
            ]

            while (
                len(messages) > self._max_messages
                or sum(len(message.content) for message in messages)
                > self._max_characters
            ):
                del messages[:2]

            self._conversations[conversation_id] = messages

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._conversations.pop(conversation_id, None)
