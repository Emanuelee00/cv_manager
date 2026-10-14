"""Read GitHub repositories through the `gh` CLI (browser login, no token to manage)."""
import json
import subprocess

from cvagents.db import get_item, upsert_item
from cvagents.i18n import t
from cvagents.repo_content import my_commits, optional_readme

README_LIMIT = 6000
REPO_FIELDS = "name,description,url,isFork,pushedAt"


def run_gh(*args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return result.stdout


def repo_body(repo, login, all_branches):
    """Text of a repo: description, languages, README and your commit messages."""
    full = f"{login}/{repo['name']}"
    langs = ", ".join(json.loads(run_gh("api", f"repos/{full}/languages")))
    readme = optional_readme(run_gh, full)
    commits = my_commits(run_gh, full, login, all_branches)
    return (
        f"{repo.get('description') or ''}\nLanguages: {langs}\n"
        f"Commit:\n{commits}\nREADME:\n{readme[:README_LIMIT]}"
    )


def sync_repo(conn, repo, login, all_branches=False):
    """A repo read in depth (all branches) stays that way in later syncs."""
    old = get_item(conn, f"gh:{repo['name']}")
    deep = all_branches or bool(old and json.loads(old["meta"]).get("deep"))
    meta = {"link": repo["url"], "pushedAt": repo.get("pushedAt", ""), "deep": deep}
    upsert_item(conn, f"gh:{repo['name']}", "github", "repo", repo["name"], repo_body(repo, login, deep), meta)


def sync_all(conn, include_forks=False):
    """Read all your repos (default branch only, except those already marked as deep)."""
    login = run_gh("api", "user", "--jq", ".login").strip()
    repos = json.loads(run_gh("repo", "list", "--limit", "200", "--json", REPO_FIELDS))
    done = 0
    for repo in (r for r in repos if include_forks or not r["isFork"]):
        try:
            sync_repo(conn, repo, login)
            done += 1
        except subprocess.CalledProcessError as err:
            print(t("github.skipped", repo=repo["name"], error=err.stderr.strip()))
    return done


def sync_deep(conn, name):
    """Read one repo on every branch and mark it as deep."""
    login = run_gh("api", "user", "--jq", ".login").strip()
    repo = json.loads(run_gh("repo", "view", f"{login}/{name}", "--json", REPO_FIELDS))
    sync_repo(conn, repo, login, all_branches=True)
