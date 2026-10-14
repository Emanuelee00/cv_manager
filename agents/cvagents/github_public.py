"""Legge i repo pubblici di un utente GitHub senza `gh` e senza chiavi (limite: 60 richieste/ora)."""
import json
import urllib.request

from cvagents.db import upsert_item

API = "https://api.github.com"
README_LIMIT = 4000


def fetch(url, raw=False):
    headers = {"Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json", "User-Agent": "cvagents"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as response:
        data = response.read().decode("utf8", "replace")
    return data if raw else json.loads(data)


def repo_body(repo):
    try:
        readme = fetch(f"{API}/repos/{repo['full_name']}/readme", raw=True)[:README_LIMIT]
    except OSError:
        readme = ""
    topics = ", ".join(repo.get("topics") or [])
    return f"{repo.get('description') or ''}\nLinguaggio: {repo.get('language') or ''}\nTopic: {topics}\nREADME:\n{readme}"


def sync_public(conn, user, limit=15):
    """Salva i `limit` repo pubblici più recenti (non fork) come voci GitHub. Ritorna quanti."""
    repos = fetch(f"{API}/users/{user}/repos?sort=pushed&per_page=100")
    own = [r for r in repos if not r.get("fork")][:limit]
    for repo in own:
        meta = {"link": repo["html_url"], "pushedAt": repo.get("pushed_at", ""), "deep": False}
        upsert_item(conn, f"gh:{repo['name']}", "github", "repo", repo["name"], repo_body(repo), meta)
    return len(own)
