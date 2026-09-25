import asyncio
import logging
from typing import Any

from app.telegram_adapter.backend import MordredBackendClient
from app.telegram_adapter.config import TelegramSettings
from app.telegram_adapter.handler import handle_update
from app.telegram_adapter.telegram import (
    TelegramBotClient,
    TelegramError,
)


logger = logging.getLogger("mordred.telegram")


async def process_updates(
    updates: list[dict[str, Any]],
    *,
    offset: int | None,
    telegram: TelegramBotClient,
    backend: MordredBackendClient,
    allowed_user_ids: frozenset[int],
) -> int | None:
    """Process updates sequentially and return the next polling offset."""

    next_offset = offset

    for update in updates:
        update_id = update.get("update_id")

        if isinstance(update_id, bool) or not isinstance(update_id, int):
            logger.warning("Ignored a Telegram update without a valid ID")
            continue

        try:
            await handle_update(
                update,
                telegram=telegram,
                backend=backend,
                allowed_user_ids=allowed_user_ids,
            )
        except TelegramError:
            logger.exception(
                "Telegram response delivery failed; update will be consumed"
            )
        finally:
            candidate_offset = update_id + 1
            if next_offset is None or candidate_offset > next_offset:
                next_offset = candidate_offset

    return next_offset


async def run() -> None:
    """Run the Telegram adapter using ordered long polling."""

    settings = TelegramSettings()
    telegram = TelegramBotClient(settings)
    backend = MordredBackendClient(settings)
    offset: int | None = None

    await telegram.delete_webhook()
    logger.info("Telegram adapter started in long-polling mode")

    while True:
        try:
            updates = await telegram.get_updates(offset=offset)
        except TelegramError:
            logger.exception("Telegram long polling failed")
            await asyncio.sleep(5)
            continue

        offset = await process_updates(
            updates,
            offset=offset,
            telegram=telegram,
            backend=backend,
            allowed_user_ids=settings.allowed_user_id_set,
        )


def configure_logging() -> None:
    """Configure operational logs without exposing Telegram request URLs."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main() -> None:
    configure_logging()
    asyncio.run(run())


if __name__ == "__main__":
    main()
