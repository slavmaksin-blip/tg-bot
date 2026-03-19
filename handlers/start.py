# handlers/start.py
"""
/start and /help handlers.
Also provides the subscription-check helper used by other handlers.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from config import CHANNEL_USERNAME, CHANNEL_LINK
import database as db

logger = logging.getLogger(__name__)

# ─── Keyboard helpers ─────────────────────────────────────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Магазин", callback_data="menu_shop")],
        [InlineKeyboardButton("👤 Профиль", callback_data="menu_profile")],
        [InlineKeyboardButton("ℹ️ Помощь",  callback_data="menu_help")],
    ])


def subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")],
    ])


# ─── Subscription check ───────────────────────────────────────────────────────

async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True if channel check is disabled or the user is subscribed."""
    if not CHANNEL_USERNAME:
        return True
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ("left", "kicked")
    except Exception:
        return True  # If we can't check, don't block the user


# ─── /start ───────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.upsert_user(user.id, user.username, user.first_name)

    if not await is_subscribed(user.id, context):
        await update.message.reply_text(
            "👋 Привет! Чтобы пользоваться ботом, подпишись на наш канал.",
            reply_markup=subscribe_keyboard(),
        )
        return

    await update.message.reply_text(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "Добро пожаловать в наш магазин. Выбери нужный раздел:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ─── /help ────────────────────────────────────────────────────────────────────

HELP_TEXT = (
    "ℹ️ <b>Помощь</b>\n\n"
    "🛍 <b>Магазин</b> — просматривай товары по категориям и оплачивай через CryptoBot или xRocket.\n"
    "👤 <b>Профиль</b> — смотри историю заказов и баланс.\n\n"
    "По всем вопросам обращайся к администратору."
)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML",
                                    reply_markup=main_menu_keyboard())


# ─── Inline button: check subscription ───────────────────────────────────────

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    if await is_subscribed(user.id, context):
        await query.edit_message_text(
            f"✅ Подписка подтверждена!\n\n"
            f"👋 Привет, <b>{user.first_name}</b>! Выбери раздел:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await query.edit_message_text(
            "❌ Ты всё ещё не подписан. Подпишись и нажми «Проверить подписку».",
            reply_markup=subscribe_keyboard(),
        )


# ─── Inline button: back to main menu ────────────────────────────────────────

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    await query.edit_message_text(
        f"👋 Привет, <b>{user.first_name}</b>! Выбери нужный раздел:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ─── Inline button: help from menu ───────────────────────────────────────────

async def menu_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    back = InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")
    ]])
    await query.edit_message_text(HELP_TEXT, parse_mode="HTML", reply_markup=back)


# ─── Handler registration ─────────────────────────────────────────────────────

def register(application) -> None:
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help",  help_handler))
    application.add_handler(CallbackQueryHandler(check_sub_callback,  pattern="^check_sub$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback,  pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(menu_help_callback,  pattern="^menu_help$"))
