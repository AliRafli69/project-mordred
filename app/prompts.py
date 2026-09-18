from pathlib import Path


BASE_PROMPT_PATH = Path("/opt/mordred/prompts/system_prompt.txt")
PRIVATE_PROMPT_PATH = Path("/run/secrets/mordred_private_prompt")
MAX_PROMPT_BYTES = 65_536


class PromptConfigurationError(RuntimeError):
    """A required personality prompt is missing or invalid."""


def read_prompt(path: Path, *, required: bool) -> str:
    """Read one bounded UTF-8 prompt without logging its contents."""

    if not path.is_file():
        if required:
            raise PromptConfigurationError(f"Required prompt is missing: {path.name}")

        return ""

    if path.stat().st_size > MAX_PROMPT_BYTES:
        raise PromptConfigurationError(f"Prompt is too large: {path.name}")

    try:
        prompt = path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError as exc:
        raise PromptConfigurationError(
            f"Prompt is not valid UTF-8: {path.name}"
        ) from exc

    if required and not prompt:
        raise PromptConfigurationError(f"Required prompt is empty: {path.name}")

    return prompt


def load_system_prompt(
    base_path: Path = BASE_PROMPT_PATH,
    private_path: Path = PRIVATE_PROMPT_PATH,
) -> str:
    """Combine the public personality with optional private instructions."""

    base_prompt = read_prompt(base_path, required=True)
    private_prompt = read_prompt(private_path, required=False)

    if not private_prompt:
        return base_prompt

    return f"{base_prompt}\n\n{private_prompt}"
