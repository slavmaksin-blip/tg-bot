# handlers/admin.py
"""
Admin panel — only accessible to users listed in config.ADMIN_IDS.

Commands:
  /admin          — show admin menu
  /add_category   — add a new category (multi-step conversation)
  /add_product    — add a new product   (multi-step conversation)
  /orders         — list all orders
  /broadcast      — send a message to all users
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database as db
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Conversation states
(
    ADD_CAT_NAME,
    ADD_PROD_CATEGORY, ADD_PROD_NAME, ADD_PROD_DESC, ADD_PROD_PRICE, ADD_PROD_FILE,
    BROADCAST_TEXT,
) = range(7)


def admin_only(func):
    """Decorator that silently ignores non-admin callers."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            return ConversationHandler.END
        return await func(update, context)
    return wrapper


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Все заказы",       callback_data="adm_orders")],
        [InlineKeyboardButton("📋 Все товары",        callback_data="adm_products")],
        [InlineKeyboardButton("📁 Все категории",     callback_data="adm_categories")],
        [InlineKeyboardButton("👥 Все пользователи", callback_data="adm_users")],
    ])


# ─── /admin ───────────────────────────────────────────────────────────────────

@admin_only
async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🔧 <b>Панель администратора</b>",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(),
    )


# ─── View orders ──────────────────────────────────────────────────────────────

@admin_only
async def adm_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    orders = db.get_all_orders()
    if not orders:
        await query.edit_message_text("📦 Заказов нет.", reply_markup=admin_menu_keyboard())
        return

    lines = ["📦 <b>Последние заказы</b>\n"]
    for o in orders[:20]:
        user_label = f"@{o['username']}" if o["username"] else o["first_name"]
        lines.append(
            f"#{o['id']} | {user_label} | {o['product_name']} | "
            f"{o['amount']:.2f} USDT | {o['status']} | {o['payment_method']}"
        )

    await query.edit_message_text(
        "\n".join(lines), parse_mode="HTML", reply_markup=admin_menu_keyboard()
    )


# ─── View products ────────────────────────────────────────────────────────────

@admin_only
async def adm_products_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    products = db.get_all_products()
    if not products:
        await query.edit_message_text("📋 Товаров нет.", reply_markup=admin_menu_keyboard())
        return

    lines = ["📋 <b>Все товары</b>\n"]
    for p in products:
        status = "✅" if p["is_active"] else "❌"
        lines.append(f"{status} [{p['id']}] {p['name']} — {p['price']:.2f} USDT ({p['category_name']})")

    await query.edit_message_text(
        "\n".join(lines), parse_mode="HTML", reply_markup=admin_menu_keyboard()
    )


# ─── View categories ──────────────────────────────────────────────────────────

@admin_only
async def adm_categories_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    categories = db.get_all_categories()
    if not categories:
        await query.edit_message_text("📁 Категорий нет.", reply_markup=admin_menu_keyboard())
        return

    lines = ["📁 <b>Все категории</b>\n"]
    for c in categories:
        status = "✅" if c["is_active"] else "❌"
        lines.append(f"{status} [{c['id']}] {c['name']}")

    await query.edit_message_text(
        "\n".join(lines), parse_mode="HTML", reply_markup=admin_menu_keyboard()
    )


# ─── View users ───────────────────────────────────────────────────────────────

@admin_only
async def adm_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    users = db.get_all_users()
    lines = [f"👥 <b>Пользователи</b> ({len(users)})\n"]
    for u in users[:30]:
        label = f"@{u['username']}" if u["username"] else u["first_name"]
        lines.append(f"• {label} (id: {u['telegram_id']})")

    await query.edit_message_text(
        "\n".join(lines), parse_mode="HTML", reply_markup=admin_menu_keyboard()
    )


# ─── /add_category conversation ───────────────────────────────────────────────

@admin_only
async def add_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📁 Введи название новой категории:")
    return ADD_CAT_NAME


async def add_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❌ Название не может быть пустым. Попробуй ещё раз:")
        return ADD_CAT_NAME
    cat_id = db.add_category(name)
    await update.message.reply_text(f"✅ Категория <b>{name}</b> добавлена (ID {cat_id}).", parse_mode="HTML")
    return ConversationHandler.END


@admin_only
async def add_category_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END


# ─── /add_product conversation ────────────────────────────────────────────────

@admin_only
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    categories = db.get_active_categories()
    if not categories:
        await update.message.reply_text("❌ Сначала создай хотя бы одну категорию (/add_category).")
        return ConversationHandler.END

    lines = ["📁 Выбери номер категории:\n"]
    for c in categories:
        lines.append(f"{c['id']}. {c['name']}")
    context.user_data["categories"] = {c["id"]: c["name"] for c in categories}
    await update.message.reply_text("\n".join(lines))
    return ADD_PROD_CATEGORY


async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cat_id = int(update.message.text.strip())
        if cat_id not in context.user_data["categories"]:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Неверный номер. Попробуй ещё раз:")
        return ADD_PROD_CATEGORY
    context.user_data["new_product"] = {"category_id": cat_id}
    await update.message.reply_text("📝 Введи название товара:")
    return ADD_PROD_NAME


async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_product"]["name"] = update.message.text.strip()
    await update.message.reply_text("📄 Введи описание товара:")
    return ADD_PROD_DESC


async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_product"]["description"] = update.message.text.strip()
    await update.message.reply_text("💰 Введи цену в USDT (например: 9.99):")
    return ADD_PROD_PRICE


async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Неверная цена. Введи положительное число:")
        return ADD_PROD_PRICE
    context.user_data["new_product"]["price"] = price
    await update.message.reply_text(
        "📎 Прикрепи файл товара (документ/фото) или напиши /skip чтобы пропустить:"
    )
    return ADD_PROD_FILE


async def add_product_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    file_id = None
    if update.message.document:
        file_id = update.message.document.file_id
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id

    p = context.user_data["new_product"]
    prod_id = db.add_product(p["category_id"], p["name"], p["description"], p["price"], file_id)
    await update.message.reply_text(
        f"✅ Товар <b>{p['name']}</b> добавлен (ID {prod_id}).", parse_mode="HTML"
    )
    return ConversationHandler.END


async def add_product_skip_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    p = context.user_data["new_product"]
    prod_id = db.add_product(p["category_id"], p["name"], p["description"], p["price"], None)
    await update.message.reply_text(
        f"✅ Товар <b>{p['name']}</b> добавлен без файла (ID {prod_id}).", parse_mode="HTML"
    )
    return ConversationHandler.END


@admin_only
async def add_product_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END


# ─── /broadcast conversation ──────────────────────────────────────────────────

@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📢 Введи сообщение для рассылки всем пользователям:")
    return BROADCAST_TEXT


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    import asyncio
    text = update.message.text
    users = db.get_all_users()
    sent = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u["telegram_id"], text=text)
            sent += 1
            await asyncio.sleep(0.05)  # stay within Telegram flood limits
        except Exception:
            pass
    await update.message.reply_text(f"✅ Сообщение отправлено {sent} из {len(users)} пользователей.")
    return ConversationHandler.END


@admin_only
async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Рассылка отменена.")
    return ConversationHandler.END


# ─── Handler registration ─────────────────────────────────────────────────────

def register(application) -> None:
    application.add_handler(CommandHandler("admin", admin_handler))
    application.add_handler(CallbackQueryHandler(adm_orders_callback,     pattern="^adm_orders$"))
    application.add_handler(CallbackQueryHandler(adm_products_callback,   pattern="^adm_products$"))
    application.add_handler(CallbackQueryHandler(adm_categories_callback, pattern="^adm_categories$"))
    application.add_handler(CallbackQueryHandler(adm_users_callback,      pattern="^adm_users$"))

    # Add category conversation
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_category", add_category_start)],
        states={
            ADD_CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name)],
        },
        fallbacks=[CommandHandler("cancel", add_category_cancel)],
    ))

    # Add product conversation
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_product", add_product_start)],
        states={
            ADD_PROD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_category)],
            ADD_PROD_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            ADD_PROD_DESC:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_desc)],
            ADD_PROD_PRICE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            ADD_PROD_FILE: [
                MessageHandler(filters.Document.ALL | filters.PHOTO, add_product_file),
                CommandHandler("skip", add_product_skip_file),
            ],
        },
        fallbacks=[CommandHandler("cancel", add_product_cancel)],
    ))

    # Broadcast conversation
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)],
        },
        fallbacks=[CommandHandler("cancel", broadcast_cancel)],
    ))
