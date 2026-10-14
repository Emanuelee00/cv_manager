"""Comandi per riempire e curare l'archivio: voci in JSON, GitHub pubblico, esclusioni."""
import json

from cvagents import github_public, importer
from cvagents.onboarding import set_excluded


def import_entries_cmd(args, conn):
    with open(args.json_file, encoding="utf8") as f:
        return f"Salvate {importer.add_entries(conn, json.load(f))} voci"


def github_public_cmd(args, conn):
    return f"Salvati {github_public.sync_public(conn, args.user)} repo pubblici di {args.user}"


def exclude_cmd(args, conn):
    ids = set_excluded(conn, args.id, not args.undo)
    return "Esclusi dal CV: " + (", ".join(ids) or "nessuno")


SPEC = [
    ("import-entries", "Salva voci da un file JSON (lista di voci già confermate)", [("json_file", {})], import_entries_cmd),
    ("github-public", "Legge i repo pubblici di un utente, senza chiavi", [("user", {})], github_public_cmd),
    ("exclude", "Esclude una voce dal CV (--undo per riammetterla)", [("id", {}), ("--undo", {"action": "store_true"})], exclude_cmd),
]
