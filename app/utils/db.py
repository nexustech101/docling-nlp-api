# db.py
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
import bcrypt

DB_PATH = "messages.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                salt TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                expire_in_seconds INTEGER NOT NULL,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id)
            )
        """)
        conn.commit()

# User helpers


def register_user(username: str, password: str) -> bool:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                (username, hashed)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate_user(username: str, password: str) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, hashed_password FROM users WHERE username = ?", 
            (username,)
        )
        row = cursor.fetchone()
        if row and bcrypt.checkpw(password.encode(), row[1].encode()):
            return row[0]
    return None


def get_user_id(username: str) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row[0] if row else None


def get_user_by_username(username: str) -> Optional[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return {"username": row[0]} if row else None

# Messaging logic


def add_message(sender_id: int, recipient_id: int, message: str, salt: Optional[str], expire_in_seconds: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (sender_id, recipient_id, message, salt, expire_in_seconds) VALUES (?, ?, ?, ?, ?)",
            (sender_id, recipient_id, message, salt, expire_in_seconds)
        )
        conn.commit()


def get_messages_for_user(user_id: int) -> List[Tuple]:
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now(timezone.utc)
        cursor.execute(
            "SELECT id, sender_id, message, salt, timestamp, expire_in_seconds FROM messages WHERE recipient_id = ?",
            (user_id,)
        )
        results = cursor.fetchall()
        valid = []
        for id, sid, msg, salt, ts, expire in results:
            try:
                timestamp = datetime.fromisoformat(ts)
            except Exception:
                timestamp = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            timestamp = timestamp.replace(tzinfo=timezone.utc)
            if now < timestamp + timedelta(seconds=expire):
                valid.append((id, sid, msg, salt, ts, expire))
            else:
                delete_message_by_id(id)
        return valid


def delete_message_by_id(message_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        conn.commit()
