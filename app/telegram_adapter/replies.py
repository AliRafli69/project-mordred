TELEGRAM_TEXT_LIMIT = 4096


def split_reply(
    text: str,
    *,
    limit: int = TELEGRAM_TEXT_LIMIT,
) -> tuple[str, ...]:
    """Split text into ordered Telegram-sized messages."""

    if limit < 1:
        raise ValueError("Reply limit must be positive")

    if not text:
        return ()

    chunks: list[str] = []
    remaining = text

    while len(remaining) > limit:
        newline_boundary = remaining.rfind("\n", 0, limit + 1)
        space_boundary = remaining.rfind(" ", 0, limit + 1)
        boundary = max(newline_boundary, space_boundary)

        if boundary < 1:
            boundary = limit
        else:
            boundary += 1

        chunks.append(remaining[:boundary])
        remaining = remaining[boundary:]

    if remaining:
        chunks.append(remaining)

    return tuple(chunks)
