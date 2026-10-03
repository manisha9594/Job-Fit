"""SQLite application tracker. Lives in the gitignored data/ dir."""
from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "data" / "tracker.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    url TEXT DEFAULT '',
    location TEXT DEFAULT '',
    date_applied TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'applied',
    notes TEXT DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""

STATUSES = ("applied", "screening", "interview", "offer", "rejected", "withdrawn")


class Tracker:
    def __init__(self, db_path: str | Path | None = None):
        raw = db_path or os.getenv("TRACKER_DB") or DEFAULT_DB
        self.db_path = Path(raw)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add(self, company: str, role: str, url: str = "", location: str = "",
            date_applied: str | None = None, status: str = "applied",
            notes: str = "") -> dict:
        if not company.strip() or not role.strip():
            raise ValueError("company and role are required")
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        now = time.time()
        date_applied = date_applied or time.strftime("%Y-%m-%d")
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO applications (company, role, url, location, date_applied,"
                " status, notes, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (company.strip(), role.strip(), url, location, date_applied,
                 status, notes, now, now),
            )
            row_id = cur.lastrowid
        return self.get(row_id)

    def get(self, app_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        return dict(row) if row else None

    def list(self, status: str | None = None) -> list[dict]:
        q = "SELECT * FROM applications"
        params: tuple = ()
        if status:
            if status not in STATUSES:
                raise ValueError(f"status must be one of {STATUSES}")
            q += " WHERE status = ?"
            params = (status,)
        q += " ORDER BY date_applied DESC, id DESC"
        with self._connect() as conn:
            rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, app_id: int, status: str) -> dict | None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
                (status, time.time(), app_id),
            )
            if cur.rowcount == 0:
                return None
        return self.get(app_id)

    def delete(self, app_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        return cur.rowcount > 0

    def due_followups(self, days: int = 7) -> list[dict]:
        """Applications still in 'applied' older than `days` — nudge to follow up."""
        cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM applications WHERE status = 'applied'"
                " AND date_applied <= ? ORDER BY date_applied ASC", (cutoff,)).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) c FROM applications GROUP BY status").fetchall()
        counts = {r["status"]: r["c"] for r in rows}
        return {"total": sum(counts.values()),
                "by_status": {s: counts.get(s, 0) for s in STATUSES}}
