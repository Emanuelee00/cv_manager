"""Comandi su fonti esterne: GitHub e render del PDF."""
from cvagents import github, render


def github_sync_cmd(args, conn):
    return f"Sincronizzati {github.sync_all(conn)} repo"


def github_deep_cmd(args, conn):
    github.sync_deep(conn, args.repo)
    return f"Repo {args.repo} letto su tutti i rami"


def render_cmd(args, conn):
    ok, pages = render.fits_one_page(args.html, args.pdf)
    return f"{pages} pagina/e" + (" (ok, una pagina)" if ok else " (NON sta in una pagina)")


SPEC = [
    ("github-sync", "Legge i tuoi repo GitHub (solo ramo principale)", [], github_sync_cmd),
    ("github-deep", "Legge un repo su tutti i rami", [("repo", {})], github_deep_cmd),
    ("render", "Da HTML a PDF e conta le pagine", [("html", {}), ("--pdf", {"default": None})], render_cmd),
]
