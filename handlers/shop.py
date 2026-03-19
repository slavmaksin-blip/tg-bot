# handlers/shop.py
"""
Shop: categories → products → product detail → buy (delegates to payments).
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

import database as db

logger = logging.getLogger(__name__)


# ─── Keyboard builders ────────────────────────────────────────────────────────

def _back_to_menu() -> InlineKeyboardButton:
    return InlineKeyboardButton("⬅️ Главное меню", callback_data="main_menu")


def _back_to_categories() -> InlineKeyboardButton:
    return InlineKeyboardButton("⬅️ Категории", callback_data="menu_shop")


def _back_to_products(category_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton("⬅️ Назад", callback_data=f"shop_cat_{category_id}")


# ─── Categories list ──────────────────────────────────────────────────────────

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    categories = db.get_active_categories()
    if not categories:
        kb = InlineKeyboardMarkup([[_back_to_menu()]])
        await query.edit_message_text("😔 Категорий пока нет.", reply_markup=kb)
        return

    rows = [
        [InlineKeyboardButton(cat["name"], callback_data=f"shop_cat_{cat['id']}")]
        for cat in categories
    ]
    rows.append([_back_to_menu()])
    await query.edit_message_text(
        "🛍 <b>Магазин</b>\n\nВыбери категорию:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )


# ─── Products in category ─────────────────────────────────────────────────────

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split("_")[-1])
    products = db.get_products_by_category(category_id)

    if not products:
        kb = InlineKeyboardMarkup([[_back_to_categories()]])
        await query.edit_message_text("😔 В этой категории пока нет товаров.", reply_markup=kb)
        return

    rows = [
        [InlineKeyboardButton(
            f"{p['name']}  —  {p['price']:.2f} USDT",
            callback_data=f"shop_prod_{p['id']}",
        )]
        for p in products
    ]
    rows.append([_back_to_categories()])
    await query.edit_message_text(
        "🛍 Выбери товар:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


# ─── Product detail ───────────────────────────────────────────────────────────

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[-1])
    product = db.get_product(product_id)

    if not product:
        await query.edit_message_text("❌ Товар не найден.")
        return

    text = (
        f"🏷 <b>{product['name']}</b>\n\n"
        f"{product['description'] or ''}\n\n"
        f"💰 Цена: <b>{product['price']:.2f} USDT</b>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 CryptoBot",  callback_data=f"pay_crypto_{product_id}")],
        [InlineKeyboardButton("🚀 xRocket",    callback_data=f"pay_xrocket_{product_id}")],
        [_back_to_products(product["category_id"])],
    ])
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


# ─── Handler registration ─────────────────────────────────────────────────────

def register(application) -> None:
    application.add_handler(CallbackQueryHandler(show_categories, pattern="^menu_shop$"))
    application.add_handler(CallbackQueryHandler(show_products,   pattern=r"^shop_cat_\d+$"))
    application.add_handler(CallbackQueryHandler(show_product,    pattern=r"^shop_prod_\d+$"))
