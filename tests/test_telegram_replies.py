import pytest

from app.telegram_adapter.replies import split_reply


def test_short_reply_is_unchanged() -> None:
    assert split_reply("Hello.") == ("Hello.",)


def test_empty_reply_produces_no_messages() -> None:
    assert split_reply("") == ()


def test_long_reply_is_split_without_losing_content() -> None:
    reply = ("alpha beta gamma\n" * 400).strip()

    chunks = split_reply(reply, limit=80)

    assert len(chunks) > 1
    assert all(1 <= len(chunk) <= 80 for chunk in chunks)
    assert "".join(chunks) == reply


def test_unbroken_text_uses_hard_boundaries() -> None:
    reply = "x" * 205

    chunks = split_reply(reply, limit=100)

    assert tuple(len(chunk) for chunk in chunks) == (100, 100, 5)
    assert "".join(chunks) == reply


def test_nonpositive_limit_is_rejected() -> None:
    with pytest.raises(ValueError):
        split_reply("Hello.", limit=0)
