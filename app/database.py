"""SQLite 資料層：users + recognition_logs"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import settings
from app.utils import bytes_to_embedding, embedding_to_bytes


class Database:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = str(db_path or settings.DB_PATH)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id    TEXT PRIMARY KEY,
                    name       TEXT NOT NULL,
                    embedding  BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS recognition_logs (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    TEXT,
                    similarity REAL NOT NULL,
                    is_live    INTEGER NOT NULL DEFAULT 0,
                    timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_logs_ts
                    ON recognition_logs(timestamp DESC);
                """
            )

    # ---- users ----

    def add_user(self, user_id: str, name: str, embedding: np.ndarray) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (user_id, name, embedding) VALUES (?, ?, ?)",
                (user_id, name, embedding_to_bytes(embedding)),
            )

    def get_all_users(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT user_id, name, embedding, created_at FROM users ORDER BY created_at DESC"
            )
            return [
                {
                    "user_id": r[0],
                    "name": r[1],
                    "embedding": bytes_to_embedding(r[2]),
                    "created_at": r[3],
                }
                for r in cur.fetchall()
            ]

    def get_user(self, user_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT user_id, name, embedding, created_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "user_id": row[0],
                "name": row[1],
                "embedding": bytes_to_embedding(row[2]),
                "created_at": row[3],
            }

    def delete_user(self, user_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    # ---- logs ----

    def log_recognition(
        self, user_id: Optional[str], similarity: float, is_live: bool
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO recognition_logs (user_id, similarity, is_live) VALUES (?, ?, ?)",
                (user_id, float(similarity), 1 if is_live else 0),
            )

    def get_recent_logs(self, limit: int = 50) -> list[dict]:
        """取得最近的辨識記錄"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT l.user_id, u.name, l.similarity, l.timestamp, l.is_live
                FROM recognition_logs l
                LEFT JOIN users u ON l.user_id = u.user_id
                ORDER BY l.timestamp DESC LIMIT ?
                """,
                (limit,),
            )
            return [
                {
                    "user_id": row[0],
                    "name": row[1],
                    "similarity": row[2],
                    "timestamp": row[3],
                    "is_live": bool(row[4]),
                }
                for row in cursor.fetchall()
            ]


_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
