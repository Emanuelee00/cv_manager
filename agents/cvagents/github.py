"""Legge i repository GitHub tramite la CLI `gh` (login dal browser, nessun token da gestire)."""
import json
import subprocess

from cvagents.db import get_item, upsert_item
from cvagents.repo_content import my_commits, optional_readme

README_LIMIT = 6000
REPO_FIELDS = "name,description,url,isFork,pushedAt"


def run_gh(*args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return result.stdout


def repo_body(repo, login, all_branches):
    """Testo di un repo: descrizione, linguaggi, README e i tuoi messaggi di commit."""
    full = f"{login}/{repo['name']}"
    langs = ", ".join(json.loads(run_gh("api", f"repos/{full}/languages")))
    readme = optional_readme(run_gh, full)
    commits = my_commits(run_gh, full, login, all_branches)
    return (
        f"{repo.get('description') or ''}\nLinguaggi: {langs}\n"
        f"Commit:\n{commits}\nREADME:\n{readme[:README_LIMIT]}"
    )


def sync_repo(conn, repo, login, all_branches=False):
    """Un repo letto in profondità (tutti i rami) resta tale nelle sincronizzazioni successive."""
    old = get_item(conn, f"gh:{repo['name']}")
    deep = all_branches or bool(old and json.loads(old["meta"]).get("deep"))
    meta = {"link": repo["url"], "pushedAt": repo.get("pushedAt", ""), "deep": deep}
    upsert_item(conn, f"gh:{repo['name']}", "github", "repo", repo["name"], repo_body(repo, login, deep), meta)


def sync_all(conn, include_forks=False):
    """Legge tutti i tuoi repo (solo ramo principale, tranne quelli già scelti in profondità)."""
    login = run_gh("api", "user", "--jq", ".login").strip()
    repos = json.loads(run_gh("repo", "list", "--limit", "200", "--json", REPO_FIELDS))
    done = 0
    for repo in (r for r in repos if include_forks or not r["isFork"]):
        try:
            sync_repo(conn, repo, login)
            done += 1
        except subprocess.CalledProcessError as err:
            print(f"saltato {repo['name']}: {err.stderr.strip()}")
    return done


def sync_deep(conn, name):
    """Legge un solo repo su tutti i rami e lo segna come 'in profondità'."""
    login = run_gh("api", "user", "--jq", ".login").strip()
    repo = json.loads(run_gh("repo", "view", f"{login}/{name}", "--json", REPO_FIELDS))
    sync_repo(conn, repo, login, all_branches=True)
