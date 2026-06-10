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
