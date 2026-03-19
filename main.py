"""
main.py — entry point for the Telegram bot.

Run:
    python main.py
"""

import logging
import aiohttp

from telegram.ext import Application

import database as db
from config import BOT_TOKEN
from handlers import start, shop, payments, admin, profile

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def on_startup(application: Application) -> None:
    """Create a shared aiohttp session used by all payment API calls."""
    application.bot_data["http_session"] = aiohttp.ClientSession()


async def on_shutdown(application: Application) -> None:
    """Close the shared aiohttp session gracefully."""
    session: aiohttp.ClientSession = application.bot_data.get("http_session")
    if session and not session.closed:
        await session.close()


def main() -> None:
    db.init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    # Register handlers (order matters for ConversationHandlers)
    admin.register(app)    # admin conversations must be registered before generic handlers
    start.register(app)
    shop.register(app)
    payments.register(app)
    profile.register(app)

    logger.info("Bot is starting…")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
