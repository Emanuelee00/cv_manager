"""Commands on external sources: GitHub and PDF rendering."""
from cvagents import github, render
from cvagents.i18n import t


def github_sync_cmd(args, conn):
    return t("cmd.github_synced", count=github.sync_all(conn))


def github_deep_cmd(args, conn):
    github.sync_deep(conn, args.repo)
    return t("cmd.github_deep", repo=args.repo)


def render_cmd(args, conn):
    ok, pages = render.fits_one_page(args.html, args.pdf)
    return t("cmd.pages_ok" if ok else "cmd.pages_too_many", pages=pages)


SPEC = [
    ("github-sync", "Read your GitHub repos with gh (default branch only)", [], github_sync_cmd),
    ("github-deep", "Read one repo on every branch", [("repo", {})], github_deep_cmd),
    ("render", "HTML to PDF and page count", [("html", {}), ("--pdf", {"default": None})], render_cmd),
]
