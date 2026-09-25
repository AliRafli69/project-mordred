import pytest

from app.telegram_adapter.config import (
    TelegramSettings,
    parse_allowed_user_ids,
)


def test_allowed_user_ids_are_parsed_from_comma_separated_value() -> None:
    assert parse_allowed_user_ids("123, 456,123") == frozenset({123, 456})


@pytest.mark.parametrize("value", ["", "123,", "abc", "0", "-1"])
def test_invalid_allowed_user_ids_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        parse_allowed_user_ids(value)


def test_telegram_secrets_are_masked() -> None:
    settings = TelegramSettings(
        bot_token="telegram-secret",
        allowed_user_ids="123",
        backend_api_key="backend-secret",
    )

    rendered = repr(settings)

    assert "telegram-secret" not in rendered
    assert "backend-secret" not in rendered
    assert settings.allowed_user_id_set == frozenset({123})
