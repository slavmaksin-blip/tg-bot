# handlers/profile.py
"""
User profile: show info, balance, and purchase history.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

import database as db

logger = logging.getLogger(__name__)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user = db.get_user(user_id)

    if not user:
        await query.edit_message_text("❌ Профиль не найден. Напиши /start.")
        return

    orders = db.get_user_orders(user_id)
    completed = [o for o in orders if o["status"] == "completed"]

    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"Имя: <b>{user['first_name']}</b>\n"
        f"Username: @{user['username'] or '—'}\n"
        f"Telegram ID: <code>{user['telegram_id']}</code>\n"
        f"Баланс: <b>{user['balance']:.2f} USDT</b>\n"
        f"Всего заказов: {len(orders)}\n"
        f"Выполненных: {len(completed)}\n"
    )

    if completed:
        text += "\n📦 <b>История покупок:</b>\n"
        for o in completed[:10]:
            text += f"• {o['product_name']} — {o['amount']:.2f} USDT ({o['created_at'][:10]})\n"

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")
    ]])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


def register(application) -> None:
    application.add_handler(CallbackQueryHandler(show_profile, pattern="^menu_profile$"))
