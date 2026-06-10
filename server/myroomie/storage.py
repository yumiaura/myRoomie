"""Dead-simple SQLite persistence: one roomie per row, stored as JSON."""
from __future__ import annotations

import sqlite3
import threading

from .models import PetState


class Store:
    def __init__(self, path: str) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS pets (id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(username TEXT PRIMARY KEY, salt TEXT NOT NULL, pw_hash TEXT NOT NULL)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, username TEXT NOT NULL)"
        )
        self.conn.commit()

    def save(self, state: PetState) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO pets (id, data) VALUES (?, ?)",
                (state.id, state.model_dump_json()),
            )
            self.conn.commit()

    def get(self, pet_id: str) -> PetState | None:
        cursor = self.conn.execute("SELECT data FROM pets WHERE id = ?", (pet_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return PetState.model_validate_json(row[0])

    def list_ids(self) -> list[str]:
        cursor = self.conn.execute("SELECT id FROM pets ORDER BY rowid")
        return [row[0] for row in cursor.fetchall()]

    # --- Accounts ----------------------------------------------------
    def create_user(self, username: str, salt: str, pw_hash: str) -> bool:
        """Insert a user; return False if the username is already taken."""
        with self.lock:
            try:
                self.conn.execute(
                    "INSERT INTO users (username, salt, pw_hash) VALUES (?, ?, ?)",
                    (username, salt, pw_hash),
                )
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_user(self, username: str) -> tuple[str, str] | None:
        """Return (salt, pw_hash) for the user, or None."""
        cursor = self.conn.execute(
            "SELECT salt, pw_hash FROM users WHERE username = ?", (username,)
        )
        return cursor.fetchone()

    def save_token(self, token: str, username: str) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO tokens (token, username) VALUES (?, ?)",
                (token, username),
            )
            self.conn.commit()

    def user_for_token(self, token: str) -> str | None:
        cursor = self.conn.execute(
            "SELECT username FROM tokens WHERE token = ?", (token,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def delete_token(self, token: str) -> None:
        with self.lock:
            self.conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
            self.conn.commit()
