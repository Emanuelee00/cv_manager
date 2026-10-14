"""Read a GitHub user's public repos without `gh` and without keys (limit: 60 requests/hour)."""
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
    return f"{repo.get('description') or ''}\nLanguage: {repo.get('language') or ''}\nTopics: {topics}\nREADME:\n{readme}"


def sync_public(conn, user, limit=15):
    """Save the `limit` most recent public repos (not forks) as GitHub entries. Returns how many."""
    repos = fetch(f"{API}/users/{user}/repos?sort=pushed&per_page=100")
    own = [r for r in repos if not r.get("fork")][:limit]
    for repo in own:
        meta = {"link": repo["html_url"], "pushedAt": repo.get("pushed_at", ""), "deep": False}
        upsert_item(conn, f"gh:{repo['name']}", "github", "repo", repo["name"], repo_body(repo), meta)
    return len(own)
