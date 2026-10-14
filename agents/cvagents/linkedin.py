"""Job offers from LinkedIn's public job pages through the original linkedin-search CLI (bun, in agents/linkedin-search).
Personal use only: keep volume low (LinkedIn ToS)."""
import json
import shutil
import subprocess
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "linkedin-search" / "src" / "cli.ts"
HOME_BUN = Path.home() / ".bun" / "bin" / "bun"


class LinkedInError(RuntimeError):
    pass


def bun():
    """Path of bun (on PATH or where its installer puts it), or None."""
    return shutil.which("bun") or (str(HOME_BUN) if HOME_BUN.is_file() else None)


def run_cli(*args):
    """Run the CLI with --format json; its errors (JSON on stderr) become LinkedInError."""
    if not bun():
        raise LinkedInError("bun not found: make install")
    try:
        done = subprocess.run([bun(), "run", str(CLI), *args, "--format", "json"], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise LinkedInError("LinkedIn did not answer in time") from None
    if done.returncode:
        try:
            raise LinkedInError(json.loads(done.stderr.strip().splitlines()[-1])["error"])
        except (ValueError, IndexError, KeyError):
            raise LinkedInError(done.stderr.strip() or "linkedin-search failed") from None
    return json.loads(done.stdout)


def search(query, location, days, limit=10):
    """Offers for `query` in `location` posted in the last `days` days: dicts with id, title, company, location, date, url."""
    args = ["search", "--location", location, "--jobage", str(days), "--limit", str(limit)]
    return run_cli(*args, *(["--query", query] if query else []))["results"]


def offer_text(job_id):
    """Full text of one offer, ready to be used as the offer of the CV."""
    job = run_cli("detail", str(job_id))
    facts = [f"{label}: {job[key]}" for label, key in (("Seniority", "seniority"), ("Employment", "employmentType"),
                                                       ("Industries", "industries")) if job.get(key)]
    header = [job["title"], f"{job.get('company') or '—'} · {job.get('location') or '—'}", *facts, job["url"]]
    return "\n".join(header) + "\n\n" + (job.get("description") or "")
