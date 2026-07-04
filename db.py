import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                public_key TEXT NOT NULL,
                private_key TEXT NOT NULL,
                username TEXT
            )
        """)


def add_user(telegram_id: int, public_key: str, private_key: str, username: str | None = None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, public_key, private_key, username) VALUES (?, ?, ?, ?)",
            (telegram_id, public_key, private_key, username),
        )


def get_user(telegram_id: int) -> tuple | None:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT public_key, private_key FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()


def user_exists(telegram_id: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return row is not None


def get_all_users() -> list[tuple[int, str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT telegram_id, public_key, private_key FROM users"
        ).fetchall()


def update_username(telegram_id: int, username: str | None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET username = ? WHERE telegram_id = ?", (username, telegram_id)
        )
