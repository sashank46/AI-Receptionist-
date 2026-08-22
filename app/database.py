"""
database.py
Sets up the SQLite database used to store appointments and per-call
conversation state. SQLite is enough for a capstone demo — no external
DB server to install or pay for.
"""
import sqlite3
from contextlib import contextmanager
from app.config import DB_PATH


def init_db():
    """Create tables if they don't already exist. Safe to call every startup."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_name TEXT,
                caller_phone TEXT,
                service TEXT,
                appt_date TEXT,   -- YYYY-MM-DD
                appt_time TEXT,   -- HH:MM (24h)
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS call_state (
                call_sid TEXT PRIMARY KEY,
                history_json TEXT NOT NULL,
                caller_phone TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
