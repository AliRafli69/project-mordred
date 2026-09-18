from pathlib import Path

import pytest

from app.prompts import PromptConfigurationError, load_system_prompt


def test_load_system_prompt_combines_public_and_private(
    tmp_path: Path,
) -> None:
    base_path = tmp_path / "system_prompt.txt"
    private_path = tmp_path / "system_prompt.private.txt"

    base_path.write_text("Public personality.", encoding="utf-8")
    private_path.write_text("Private preference.", encoding="utf-8")

    assert load_system_prompt(base_path, private_path) == (
        "Public personality.\n\nPrivate preference."
    )


def test_load_system_prompt_accepts_empty_private_file(
    tmp_path: Path,
) -> None:
    base_path = tmp_path / "system_prompt.txt"
    private_path = tmp_path / "system_prompt.private.txt"

    base_path.write_text("Public personality.", encoding="utf-8")
    private_path.write_text("", encoding="utf-8")

    assert load_system_prompt(base_path, private_path) == "Public personality."


def test_load_system_prompt_accepts_missing_private_file(
    tmp_path: Path,
) -> None:
    base_path = tmp_path / "system_prompt.txt"
    private_path = tmp_path / "missing-private.txt"

    base_path.write_text("Public personality.", encoding="utf-8")

    assert load_system_prompt(base_path, private_path) == "Public personality."


def test_load_system_prompt_rejects_empty_public_prompt(
    tmp_path: Path,
) -> None:
    base_path = tmp_path / "system_prompt.txt"
    private_path = tmp_path / "system_prompt.private.txt"

    base_path.write_text("", encoding="utf-8")

    with pytest.raises(PromptConfigurationError):
        load_system_prompt(base_path, private_path)
