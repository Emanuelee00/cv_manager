"""Cosa dare all'AI: le voci del database utili all'offerta, più profilo e dati fissi."""
import json

from cvagents.pipeline.keywords import keywords
from cvagents.search import search

SKIP_KINDS = ("cv_document", "cover_letter", "style", "preferences", "profile")
ALWAYS_KINDS = ("education", "language", "interest")
BODY_LIMIT = 700
def excluded_ids(conn):
    """Id che il candidato ha escluso (nel campo meta delle sue preferenze)."""
    row = conn.execute("SELECT meta FROM items WHERE id = 'manual:preferenze-candidato'").fetchone()
    return set(json.loads(row["meta"]).get("excluded_ids", [])) if row else set()


def retrieve(conn, provider, offer, limit=8):
    """Le voci più pertinenti più quelle fisse (formazione, lingue, interessi). Le voci curate pesano il doppio dei repo."""
    scores, rows, skip = {}, {}, excluded_ids(conn)
    for word in keywords(provider, offer):
        for rank, row in enumerate(search(conn, word, limit=5)):
            if row["kind"] not in SKIP_KINDS and row["id"] not in skip:
                weight = 1 if row["source"] == "github" else 2
                scores[row["id"]] = scores.get(row["id"], 0) + (5 - rank) * weight
                rows[row["id"]] = row
    best = [rows[i] for i in sorted(scores, key=scores.get, reverse=True)[:limit]]
    fixed = conn.execute(f"SELECT * FROM items WHERE kind IN ({','.join('?' * len(ALWAYS_KINDS))})", ALWAYS_KINDS).fetchall()
    return best + [r for r in fixed if r["id"] not in scores and r["id"] not in skip]


def candidate_text(conn):
    """Anagrafica, preferenze e telefoni del candidato, come testo per l'AI."""
    ids = ("manual:profilo-candidato", "manual:preferenze-candidato", "manual:profilo-telefoni")
    found = [conn.execute("SELECT body FROM items WHERE id = ?", (i,)).fetchone() for i in ids]
    return "\n\n".join(r["body"] for r in found if r)


def format_context(rows):
    return "\n\n".join(f"[{r['id']}] ({r['kind']}) {r['title']}\n{r['body'][:BODY_LIMIT]}" for r in rows)
