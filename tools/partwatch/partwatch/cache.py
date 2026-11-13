"""SQLite cache so daily API quotas are never the bottleneck."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .models import SourceResult


class Cache:
    def __init__(self, path: Path | str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.execute("""CREATE TABLE IF NOT EXISTS results(
            source TEXT, key TEXT, fetched REAL, payload TEXT, PRIMARY KEY(source, key))""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS history(
            key TEXT, day TEXT, lifecycle TEXT, stock INTEGER, rating TEXT,
            PRIMARY KEY(key, day))""")

    def get(self, source: str, key: str, max_age_s: float) -> SourceResult | None:
        row = self.db.execute("SELECT fetched, payload FROM results WHERE source=? AND key=?",
                              (source, key)).fetchone()
        if not row or time.time() - row[0] > max_age_s:
            return None
        return SourceResult.from_json(json.loads(row[1]))

    def put(self, key: str, result: SourceResult):
        if result.error:          # never cache failures; retry next run
            return
        self.db.execute("INSERT OR REPLACE INTO results VALUES (?,?,?,?)",
                        (result.source, key, time.time(), json.dumps(result.to_json())))
        self.db.commit()

    def record(self, key: str, lifecycle: str, stock: int, rating: str):
        day = time.strftime("%Y-%m-%d")
        self.db.execute("INSERT OR REPLACE INTO history VALUES (?,?,?,?,?)",
                        (key, day, lifecycle, stock, rating))
        self.db.commit()

    def previous(self, key: str) -> tuple[str, str] | None:
        """(lifecycle, rating) from the last run before today, to detect changes."""
        row = self.db.execute(
            "SELECT lifecycle, rating FROM history WHERE key=? AND day<? ORDER BY day DESC LIMIT 1",
            (key, time.strftime("%Y-%m-%d"))).fetchone()
        return (row[0], row[1]) if row else None
