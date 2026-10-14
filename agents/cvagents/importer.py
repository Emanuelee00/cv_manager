"""Import delle voci del CV (formato dell'app, cvbase.json) e aggiunta manuale."""
import json
import uuid

from cvagents.db import upsert_item


def entry_body(entry):
    """Unisce i campi utili alla ricerca in un solo testo."""
    parts = [entry.get("org"), entry.get("period"), entry.get("description"), entry.get("result")]
    tags = entry.get("tags") or []
    return "\n".join(p for p in parts if p) + ("\nTag: " + ", ".join(tags) if tags else "")


def import_file(conn, path):
    """Importa tutte le voci di un cvbase.json; rieseguirlo aggiorna senza duplicare."""
    with open(path, encoding="utf8") as f:
        entries = json.load(f)["entries"]
    for e in entries:
        meta = {k: e.get(k, "") for k in ("org", "period", "link", "note")}
        upsert_item(conn, f"cv:{e['id']}", "cv", e["type"], e["title"], entry_body(e), meta)
    return len(entries)


def add_manual(conn, kind, title, body):
    """Aggiunge a mano una voce (qualsiasi cosa fatta nella vita)."""
    id = f"manual:{uuid.uuid4()}"
    upsert_item(conn, id, "manual", kind, title, body)
    return id
