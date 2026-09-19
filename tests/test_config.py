from app.config import Settings


def test_settings_validate_and_mask_secrets() -> None:
    settings = Settings(
        lm_studio_base_url="http://example.invalid:1234",
        lm_studio_api_key="inference-secret",
        lm_studio_model="test-model",
        backend_api_key="backend-secret",
    )

    assert str(settings.lm_studio_base_url) == "http://example.invalid:1234/"
    assert settings.lm_studio_model == "test-model"
    assert settings.connect_timeout_seconds == 3.0
    assert settings.read_timeout_seconds == 90.0

    assert settings.chat_temperature == 0.7
    assert settings.chat_max_output_tokens == 1024

    assert settings.conversation_max_messages == 12
    assert settings.conversation_max_characters == 24_000

    rendered = repr(settings)

    assert "inference-secret" not in rendered
    assert "backend-secret" not in rendered
    assert "**********" in rendered
