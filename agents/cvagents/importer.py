"""Import CV entries (the web app's cvbase.json format) and add entries by hand."""
import json
import uuid

from cvagents.db import upsert_item


def entry_body(entry):
    """Join the searchable fields into one text."""
    parts = [entry.get("org"), entry.get("period"), entry.get("description"), entry.get("result")]
    tags = entry.get("tags") or []
    return "\n".join(p for p in parts if p) + ("\nTags: " + ", ".join(tags) if tags else "")


def import_file(conn, path):
    """Import every entry of a cvbase.json; running it again updates without duplicates."""
    with open(path, encoding="utf8") as f:
        entries = json.load(f)["entries"]
    for e in entries:
        meta = {k: e.get(k, "") for k in ("org", "period", "link", "note")}
        upsert_item(conn, f"cv:{e['id']}", "cv", e["type"], e["title"], entry_body(e), meta)
    return len(entries)


def add_manual(conn, kind, title, body):
    """Add an entry by hand (anything done in life)."""
    id = f"manual:{uuid.uuid4()}"
    upsert_item(conn, id, "manual", kind, title, body)
    return id


def add_entries(conn, entries):
    """Save entries extracted from a CV (after the user confirmed them). Returns how many."""
    for e in entries:
        meta = {k: e.get(k, "") for k in ("org", "period", "link", "note")}
        upsert_item(conn, f"cv:{uuid.uuid4()}", "cv", e["type"], e["title"], entry_body(e), meta)
    return len(entries)
