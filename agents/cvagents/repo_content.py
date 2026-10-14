"""Contenuto di un repo: README e i tuoi commit (sul ramo principale o su tutti i rami)."""
import subprocess
from urllib.parse import quote

MAX_BRANCHES = 30
COMMIT_FORMAT = '.[] | .sha + " " + (.commit.message | split("\\n")[0])'


def optional_readme(run_gh, full):
    """Il README può mancare: in quel caso il repo si salva comunque, senza."""
    try:
        return run_gh("api", f"repos/{full}/readme", "-H", "Accept: application/vnd.github.raw")
    except subprocess.CalledProcessError:
        return ""


def list_branches(run_gh, full):
    path = f"repos/{full}/branches?per_page={MAX_BRANCHES}"
    return [b for b in run_gh("api", path, "--jq", ".[].name").split("\n") if b]


def my_commits(run_gh, full, login, all_branches=False):
    """Righe '[ramo] messaggio', senza duplicati. Senza all_branches legge solo il ramo principale."""
    seen = {}
    for branch in list_branches(run_gh, full) if all_branches else [None]:
        sha_param = f"sha={quote(branch, safe='')}&" if branch else ""
        url = f"repos/{full}/commits?{sha_param}author={login}&per_page=50"
        for line in run_gh("api", url, "--jq", COMMIT_FORMAT).splitlines():
            sha, message = line.split(" ", 1)
            seen.setdefault(sha, f"[{branch}] {message}" if branch else message)
    return "\n".join(seen.values())
