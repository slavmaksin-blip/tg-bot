# handlers/payments.py
"""
Payment integration for CryptoBot and xRocket.

Flow:
  1. User clicks "Buy via CryptoBot" or "Buy via xRocket" in the shop.
  2. Bot creates an invoice via the payment API and sends the pay link.
  3. A background job polls every PAYMENT_CHECK_INTERVAL seconds.
  4. When the invoice is paid the bot marks the order as "completed" and
     delivers the product (file or text) to the user.
"""

import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

import database as db
from config import (
    CRYPTOBOT_API_URL,
    CRYPTOBOT_API_KEY,
    XROCKET_API_URL,
    XROCKET_API_KEY,
    PAYMENT_CHECK_INTERVAL,
    PAYMENT_CURRENCY,
)

logger = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=10)


def _session(context: ContextTypes.DEFAULT_TYPE) -> aiohttp.ClientSession:
    """Return the shared aiohttp session stored in bot_data."""
    return context.application.bot_data["http_session"]


# ─── CryptoBot helpers ────────────────────────────────────────────────────────

async def cryptobot_create_invoice(amount: float, description: str,
                                   context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    """Create a CryptoBot invoice and return the API response dict."""
    url = f"{CRYPTOBOT_API_URL}/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY}
    payload = {
        "asset": PAYMENT_CURRENCY,
        "amount": str(round(amount, 2)),
        "description": description,
        "expires_in": 3600,
    }
    try:
        async with _session(context).post(url, json=payload, headers=headers,
                                          timeout=_TIMEOUT) as resp:
            data = await resp.json()
            if data.get("ok"):
                return data["result"]
    except Exception as exc:
        logger.error("CryptoBot createInvoice error: %s", exc)
    return None


async def cryptobot_get_invoice(invoice_id: str,
                                context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    """Fetch a CryptoBot invoice by ID."""
    url = f"{CRYPTOBOT_API_URL}/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY}
    params = {"invoice_ids": invoice_id}
    try:
        async with _session(context).get(url, params=params, headers=headers,
                                         timeout=_TIMEOUT) as resp:
            data = await resp.json()
            if data.get("ok") and data["result"]["items"]:
                return data["result"]["items"][0]
    except Exception as exc:
        logger.error("CryptoBot getInvoice error: %s", exc)
    return None


# ─── xRocket helpers ──────────────────────────────────────────────────────────

async def xrocket_create_invoice(amount: float, description: str,
                                  context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    """Create an xRocket invoice and return the API response dict."""
    url = f"{XROCKET_API_URL}/tg-invoices"
    headers = {
        "Rocket-Pay-Key": XROCKET_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "currency": PAYMENT_CURRENCY,
        "amount": round(amount, 2),
        "description": description,
        "expiredIn": 3600,
    }
    try:
        async with _session(context).post(url, json=payload, headers=headers,
                                          timeout=_TIMEOUT) as resp:
            data = await resp.json()
            if data.get("success"):
                return data["data"]
    except Exception as exc:
        logger.error("xRocket createInvoice error: %s", exc)
    return None


async def xrocket_get_invoice(invoice_id: str,
                               context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    """Fetch an xRocket invoice by ID."""
    url = f"{XROCKET_API_URL}/tg-invoices/{invoice_id}"
    headers = {"Rocket-Pay-Key": XROCKET_API_KEY}
    try:
        async with _session(context).get(url, headers=headers,
                                         timeout=_TIMEOUT) as resp:
            data = await resp.json()
            if data.get("success"):
                return data["data"]
    except Exception as exc:
        logger.error("xRocket getInvoice error: %s", exc)
    return None


# ─── Product delivery ─────────────────────────────────────────────────────────

async def deliver_product(user_id: int, order_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    order = db.get_order(order_id)
    if not order:
        return

    text = (
        f"✅ Оплата получена!\n\n"
        f"📦 Ваш заказ: <b>{order['product_name']}</b>\n"
        f"🔖 Номер заказа: #{order_id}"
    )

    if order["file_id"]:
        await context.bot.send_document(
            chat_id=user_id,
            document=order["file_id"],
            caption=text,
            parse_mode="HTML",
        )
    else:
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")


# ─── Background payment checker ───────────────────────────────────────────────

async def check_pending_payments(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job that polls all pending orders and completes paid ones."""
    pending = db.get_pending_orders()
    for order in pending:
        order_id = order["id"]
        payment_id = order["payment_id"]
        method = order["payment_method"]

        if not payment_id:
            continue

        if method == "cryptobot":
            invoice = await cryptobot_get_invoice(payment_id, context)
            if invoice and invoice.get("status") == "paid":
                db.update_order_status(order_id, "completed")
                await deliver_product(order["user_id"], order_id, context)

        elif method == "xrocket":
            invoice = await xrocket_get_invoice(payment_id, context)
            if invoice and invoice.get("status") == "paid":
                db.update_order_status(order_id, "completed")
                await deliver_product(order["user_id"], order_id, context)


# ─── Buy via CryptoBot ────────────────────────────────────────────────────────

async def pay_crypto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[-1])
    product = db.get_product(product_id)
    if not product:
        await query.edit_message_text("❌ Товар не найден.")
        return

    await query.edit_message_text("⏳ Создаю счёт через CryptoBot…")

    invoice = await cryptobot_create_invoice(
        product["price"], f"Оплата товара: {product['name']}", context
    )

    if not invoice:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Назад", callback_data=f"shop_prod_{product_id}")
        ]])
        await query.edit_message_text(
            "❌ Не удалось создать счёт. Попробуй позже.", reply_markup=kb
        )
        return

    order_id = db.create_order(
        user_id=update.effective_user.id,
        product_id=product_id,
        quantity=1,
        amount=product["price"],
        payment_method="cryptobot",
        payment_id=str(invoice["invoice_id"]),
    )

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("💳 Оплатить", url=invoice["pay_url"])
    ]])
    await query.edit_message_text(
        f"💳 <b>Счёт создан</b>\n\n"
        f"Товар: {product['name']}\n"
        f"Сумма: <b>{product['price']:.2f} {PAYMENT_CURRENCY}</b>\n\n"
        f"После оплаты товар будет доставлен автоматически.\n"
        f"🔖 Заказ #{order_id}",
        parse_mode="HTML",
        reply_markup=kb,
    )


# ─── Buy via xRocket ──────────────────────────────────────────────────────────

async def pay_xrocket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[-1])
    product = db.get_product(product_id)
    if not product:
        await query.edit_message_text("❌ Товар не найден.")
        return

    await query.edit_message_text("⏳ Создаю счёт через xRocket…")

    invoice = await xrocket_create_invoice(
        product["price"], f"Оплата товара: {product['name']}", context
    )

    if not invoice:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Назад", callback_data=f"shop_prod_{product_id}")
        ]])
        await query.edit_message_text(
            "❌ Не удалось создать счёт. Попробуй позже.", reply_markup=kb
        )
        return

    order_id = db.create_order(
        user_id=update.effective_user.id,
        product_id=product_id,
        quantity=1,
        amount=product["price"],
        payment_method="xrocket",
        payment_id=str(invoice["id"]),
    )

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Оплатить", url=invoice["link"])
    ]])
    await query.edit_message_text(
        f"🚀 <b>Счёт создан</b>\n\n"
        f"Товар: {product['name']}\n"
        f"Сумма: <b>{product['price']:.2f} {PAYMENT_CURRENCY}</b>\n\n"
        f"После оплаты товар будет доставлен автоматически.\n"
        f"🔖 Заказ #{order_id}",
        parse_mode="HTML",
        reply_markup=kb,
    )


# ─── Handler registration ─────────────────────────────────────────────────────

def register(application) -> None:
    application.add_handler(CallbackQueryHandler(pay_crypto_callback,   pattern=r"^pay_crypto_\d+$"))
    application.add_handler(CallbackQueryHandler(pay_xrocket_callback,  pattern=r"^pay_xrocket_\d+$"))

    # Start background job to poll for completed payments
    application.job_queue.run_repeating(
        check_pending_payments,
        interval=PAYMENT_CHECK_INTERVAL,
        first=10,
    )

