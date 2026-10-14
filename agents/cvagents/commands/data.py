"""Database commands: import, add, search, show, stats."""
import json

from cvagents import importer
from cvagents.db import count_items, get_item
from cvagents.i18n import t
from cvagents.search import search as run_search


def import_cmd(args, conn):
    return t("cmd.imported", count=importer.import_file(conn, args.path))


def add_cmd(args, conn):
    return importer.add_manual(conn, args.kind, args.title, args.body)


def search_cmd(args, conn):
    rows = run_search(conn, args.query, args.limit, args.source)
    lines = (f"[{r['id']}] ({r['source']}/{r['kind']}) {r['title']}\n{r['body'][:300]}" for r in rows)
    return "\n\n".join(lines) or t("cmd.no_results")


def show_cmd(args, conn):
    row = get_item(conn, args.id)
    return f"{row['title']}\n\n{row['body']}\n\n{row['meta']}" if row else t("cmd.not_found")


def stats_cmd(args, conn):
    return json.dumps({s: count_items(conn, s) for s in ("cv", "manual", "github")})


SPEC = [
    ("import", "Import entries from a cvbase.json", [("path", {})], import_cmd),
    ("add", "Add an entry by hand", [("kind", {}), ("title", {}), ("body", {})], add_cmd),
    ("search", "Search the archive", [("query", {}), ("--limit", {"type": int, "default": 8}),
                                     ("--source", {"choices": ["cv", "manual", "github"]})], search_cmd),
    ("show", "Show a whole entry", [("id", {})], show_cmd),
    ("stats", "Count entries by source", [], stats_cmd),
]
