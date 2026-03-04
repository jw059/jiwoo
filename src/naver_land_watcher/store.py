from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from naver_land_watcher.diff_engine import payload_hash


class SQLiteStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_articles (
                    article_no TEXT PRIMARY KEY,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    last_payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_no TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    channel TEXT NOT NULL
                )
                """
            )

    def get_article_payload(self, article_no: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT payload_json FROM seen_articles WHERE article_no = ?", (article_no,)
            ).fetchone()
        if not row:
            return None
        import json

        return json.loads(row["payload_json"])

    def upsert_article(self, article_no: str, payload: dict) -> None:
        import json

        now = datetime.now(timezone.utc).isoformat()
        p_hash = payload_hash(payload)
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT article_no, first_seen_at FROM seen_articles WHERE article_no = ?",
                (article_no,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE seen_articles
                    SET last_seen_at = ?, last_payload_hash = ?, payload_json = ?
                    WHERE article_no = ?
                    """,
                    (now, p_hash, json.dumps(payload, ensure_ascii=False), article_no),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO seen_articles(article_no, first_seen_at, last_seen_at, last_payload_hash, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (article_no, now, now, p_hash, json.dumps(payload, ensure_ascii=False)),
                )

    def record_alert(self, article_no: str, channel: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO alerts(article_no, sent_at, channel) VALUES (?, ?, ?)",
                (article_no, now, channel),
            )
