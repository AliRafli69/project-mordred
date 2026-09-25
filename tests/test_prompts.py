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



def test_load_system_prompt_rejects_unreadable_private_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_path = tmp_path / "system_prompt.txt"
    private_path = tmp_path / "system_prompt.private.txt"

    base_path.write_text("Public personality.", encoding="utf-8")
    private_path.write_text("Private preference.", encoding="utf-8")

    original_read_text = Path.read_text

    def controlled_read_text(
        candidate: Path,
        *args: object,
        **kwargs: object,
    ) -> str:
        if candidate == private_path:
            raise PermissionError("test permission failure")

        return original_read_text(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", controlled_read_text)

    with pytest.raises(
        PromptConfigurationError,
        match=r"Prompt cannot be read: system_prompt\.private\.txt",
    ):
        load_system_prompt(base_path, private_path)
