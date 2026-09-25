def conversation_id_for_user(user_id: int) -> str:
    """Map one Telegram user to one backend-compatible conversation ID."""

    if isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Telegram user ID must be a positive integer")

    return f"telegram:user:{user_id}"


def is_authorized_private_chat(
    *,
    user_id: int,
    chat_type: str,
    allowed_user_ids: frozenset[int],
) -> bool:
    """Authorize only allowlisted users communicating in private chats."""

    return chat_type == "private" and user_id in allowed_user_ids
