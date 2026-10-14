"""SQLite archive: one table of entries and an FTS5 index for search."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "cvbase.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY, source TEXT NOT NULL, kind TEXT NOT NULL,
    title TEXT NOT NULL, body TEXT NOT NULL, meta TEXT NOT NULL, updated TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    id UNINDEXED, title, body, tokenize = 'unicode61 remove_diacritics 2'
);
"""


def connect(path=DEFAULT_DB):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_item(conn, id, source, kind, title, body, meta=None):
    """Insert or update an entry (and its index) by id."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO items VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id, source, kind, title, body, json.dumps(meta or {}, ensure_ascii=False), now),
    )
    conn.execute("DELETE FROM items_fts WHERE id = ?", (id,))
    conn.execute("INSERT INTO items_fts (id, title, body) VALUES (?, ?, ?)", (id, title, body))
    conn.commit()


def get_item(conn, id):
    return conn.execute("SELECT * FROM items WHERE id = ?", (id,)).fetchone()


def count_items(conn, source=None):
    query = "SELECT COUNT(*) FROM items" + (" WHERE source = ?" if source else "")
    return conn.execute(query, (source,) if source else ()).fetchone()[0]
