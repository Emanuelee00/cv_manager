"""Keyword search (FTS5, BM25 ranking) over the archive."""
import re


def build_match(query):
    """Turn free text into an FTS5 query: words joined by OR, as prefixes (develop* finds developer)."""
    words = re.findall(r"\w{2,}", query)
    return " OR ".join(f'"{w}"*' for w in words)


def search(conn, query, limit=8, source=None):
    match = build_match(query)
    if not match:
        return []
    sql = (
        "SELECT i.id, i.source, i.kind, i.title, i.body, i.meta, bm25(items_fts, 0, 3, 1) AS score "
        "FROM items_fts JOIN items i ON i.id = items_fts.id "
        "WHERE items_fts MATCH ?" + (" AND i.source = ?" if source else "") +
        " ORDER BY score LIMIT ?"
    )
    args = (match, source, limit) if source else (match, limit)
    return conn.execute(sql, args).fetchall()
