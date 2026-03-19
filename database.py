# database.py
"""
SQLite database layer for the Telegram bot.
Tables: users, categories, products, orders
"""

import sqlite3
import logging
from datetime import datetime
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they do not exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username    TEXT,
                first_name  TEXT,
                balance     REAL    NOT NULL DEFAULT 0.0,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS categories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                is_active   INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL REFERENCES categories(id),
                name        TEXT    NOT NULL,
                description TEXT,
                price       REAL    NOT NULL,
                file_id     TEXT,
                is_active   INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS orders (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL REFERENCES users(telegram_id),
                product_id     INTEGER NOT NULL REFERENCES products(id),
                quantity       INTEGER NOT NULL DEFAULT 1,
                amount         REAL    NOT NULL,
                payment_method TEXT    NOT NULL,
                payment_id     TEXT,
                status         TEXT    NOT NULL DEFAULT 'pending',
                created_at     TEXT    NOT NULL
            );
        """)
    logger.info("Database initialised at %s", DATABASE_PATH)


# ─── Users ────────────────────────────────────────────────────────────────────

def upsert_user(telegram_id: int, username: str | None, first_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name
            """,
            (telegram_id, username, first_name, datetime.utcnow().isoformat()),
        )


def get_user(telegram_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()


def get_all_users() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()


def update_user_balance(telegram_id: int, delta: float) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
            (delta, telegram_id),
        )


# ─── Categories ───────────────────────────────────────────────────────────────

def get_active_categories() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM categories WHERE is_active = 1 ORDER BY name"
        ).fetchall()


def get_all_categories() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM categories ORDER BY name").fetchall()


def add_category(name: str) -> int:
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        return cur.lastrowid


def toggle_category(category_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE categories SET is_active = 1 - is_active WHERE id = ?",
            (category_id,),
        )


# ─── Products ─────────────────────────────────────────────────────────────────

def get_products_by_category(category_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE category_id = ? AND is_active = 1 ORDER BY name",
            (category_id,),
        ).fetchall()


def get_all_products() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT p.*, c.name AS category_name
            FROM products p
            JOIN categories c ON c.id = p.category_id
            ORDER BY c.name, p.name
            """
        ).fetchall()


def get_product(product_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()


def add_product(
    category_id: int,
    name: str,
    description: str,
    price: float,
    file_id: str | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO products (category_id, name, description, price, file_id) VALUES (?, ?, ?, ?, ?)",
            (category_id, name, description, price, file_id),
        )
        return cur.lastrowid


def update_product_file(product_id: int, file_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET file_id = ? WHERE id = ?", (file_id, product_id)
        )


def toggle_product(product_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET is_active = 1 - is_active WHERE id = ?",
            (product_id,),
        )


# ─── Orders ───────────────────────────────────────────────────────────────────

def create_order(
    user_id: int,
    product_id: int,
    quantity: int,
    amount: float,
    payment_method: str,
    payment_id: str | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO orders (user_id, product_id, quantity, amount,
                                payment_method, payment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                product_id,
                quantity,
                amount,
                payment_method,
                payment_id,
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid


def update_order_status(order_id: int, status: str, payment_id: str | None = None) -> None:
    with get_connection() as conn:
        if payment_id:
            conn.execute(
                "UPDATE orders SET status = ?, payment_id = ? WHERE id = ?",
                (status, payment_id, order_id),
            )
        else:
            conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?", (status, order_id)
            )


def get_order(order_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT o.*, p.name AS product_name, p.file_id
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()


def get_pending_orders() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM orders WHERE status = 'pending'"
        ).fetchall()


def get_user_orders(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT o.*, p.name AS product_name
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
            """,
            (user_id,),
        ).fetchall()


def get_all_orders() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT o.*, u.username, u.first_name, p.name AS product_name
            FROM orders o
            JOIN users u ON u.telegram_id = o.user_id
            JOIN products p ON p.id = o.product_id
            ORDER BY o.created_at DESC
            """,
        ).fetchall()
