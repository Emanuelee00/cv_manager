"""Riga di comando: python -m cvagents <comando>."""
import argparse
import json

from cvagents import github, importer, render
from cvagents.db import connect, count_items, get_item
from cvagents.search import search

COMMANDS = {
    "import": "Importa le voci da un cvbase.json",
    "add": "Aggiunge una voce a mano",
    "github-sync": "Legge i tuoi repo GitHub (solo ramo principale)",
    "github-deep": "Legge un repo su tutti i rami",
    "search": "Cerca nell'archivio",
    "show": "Mostra una voce intera",
    "stats": "Conta le voci per fonte",
    "render": "Da HTML a PDF e conta le pagine",
}


def build_parser():
    parser = argparse.ArgumentParser(prog="cvagents")
    parser.add_argument("--db", default=None, help="percorso del database SQLite")
    sub = parser.add_subparsers(dest="cmd", required=True)
    args_of = {"import": ["path"], "add": ["kind", "title", "body"], "search": ["query"], "show": ["id"], "github-deep": ["repo"], "render": ["html"]}
    for name, help_text in COMMANDS.items():
        p = sub.add_parser(name, help=help_text)
        for arg in args_of.get(name, []):
            p.add_argument(arg)
    sub.choices["render"].add_argument("--pdf", default=None, help="dove salvare il PDF")
    sub.choices["search"].add_argument("--limit", type=int, default=8)
    sub.choices["search"].add_argument("--source", choices=["cv", "manual", "github"])
    return parser


def run(args, conn):
    if args.cmd == "import":
        return f"Importate {importer.import_file(conn, args.path)} voci"
    if args.cmd == "add":
        return importer.add_manual(conn, args.kind, args.title, args.body)
    if args.cmd == "github-sync":
        return f"Sincronizzati {github.sync_all(conn)} repo"
    if args.cmd == "render":
        ok, pages = render.fits_one_page(args.html, args.pdf)
        return f"{pages} pagina/e" + (" (ok, una pagina)" if ok else " (NON sta in una pagina)")
    if args.cmd == "github-deep":
        github.sync_deep(conn, args.repo)
        return f"Repo {args.repo} letto su tutti i rami"
    if args.cmd == "search":
        rows = search(conn, args.query, args.limit, args.source)
        return "\n\n".join(f"[{r['id']}] ({r['source']}/{r['kind']}) {r['title']}\n{r['body'][:300]}" for r in rows) or "Nessun risultato"
    if args.cmd == "show":
        row = get_item(conn, args.id)
        return f"{row['title']}\n\n{row['body']}\n\n{row['meta']}" if row else "Voce non trovata"
    return json.dumps({s: count_items(conn, s) for s in ("cv", "manual", "github")})


def main():
    args = build_parser().parse_args()
    print(run(args, connect(args.db) if args.db else connect()))
