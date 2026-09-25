import pytest

from app.telegram_adapter.identity import (
    conversation_id_for_user,
    is_authorized_private_chat,
)


def test_conversation_id_is_stable_and_backend_compatible() -> None:
    assert conversation_id_for_user(123456789) == "telegram:user:123456789"


@pytest.mark.parametrize("user_id", [0, -1, True])
def test_conversation_id_rejects_invalid_user_id(user_id: int) -> None:
    with pytest.raises(ValueError):
        conversation_id_for_user(user_id)


def test_allowlisted_user_in_private_chat_is_authorized() -> None:
    assert is_authorized_private_chat(
        user_id=123,
        chat_type="private",
        allowed_user_ids=frozenset({123}),
    )


def test_unlisted_user_is_rejected() -> None:
    assert not is_authorized_private_chat(
        user_id=999,
        chat_type="private",
        allowed_user_ids=frozenset({123}),
    )


@pytest.mark.parametrize("chat_type", ["group", "supergroup", "channel"])
def test_non_private_chat_is_rejected(chat_type: str) -> None:
    assert not is_authorized_private_chat(
        user_id=123,
        chat_type=chat_type,
        allowed_user_ids=frozenset({123}),
    )
