"""Commands to fill and curate the archive: entries in JSON, public GitHub, exclusions."""
import json

from cvagents import github_public, importer
from cvagents.i18n import t
from cvagents.onboarding import set_excluded


def import_entries_cmd(args, conn):
    with open(args.json_file, encoding="utf8") as f:
        return t("cmd.entries_saved", count=importer.add_entries(conn, json.load(f)))


def github_public_cmd(args, conn):
    return t("cmd.public_repos", count=github_public.sync_public(conn, args.user), user=args.user)


def list_cmd(args, conn):
    rows = conn.execute("SELECT id, kind, title FROM items WHERE kind = ? ORDER BY title", (args.kind,)).fetchall()
    return "\n".join(f"[{r['id']}] ({r['kind']}) {r['title']}" for r in rows) or t("cmd.no_results")


def exclude_cmd(args, conn):
    ids = set_excluded(conn, args.id, not args.undo)
    return t("cmd.excluded", ids=", ".join(ids) or t("common.none"))


SPEC = [
    ("import-entries", "Save entries from a JSON file (a list of already confirmed entries)", [("json_file", {})], import_entries_cmd),
    ("github-public", "Read a user's public repos, without keys", [("user", {})], github_public_cmd),
    ("list", "List the entries of one kind (e.g. cover_letter, certification, interest)", [("--kind", {"required": True})], list_cmd),
    ("exclude", "Never use an entry in the CV (--undo to allow it again)", [("id", {}), ("--undo", {"action": "store_true"})], exclude_cmd),
]
