"""Le scelte fatte con `cvagents start`, salvate per rilanciare tutto con `cvagents run`. Mai chiavi API su disco."""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "settings.json"
DEFAULTS = {"ai": "", "model": "", "github": "skip", "github_user": "", "offer": "", "lang": "", "formats": ["pdf"], "out": "output"}
RUN_COMMAND = "uv run cvagents run"


def load(path=PATH):
    path = Path(path)
    return {**DEFAULTS, **json.loads(path.read_text(encoding="utf8"))} if path.is_file() else dict(DEFAULTS)


def save(settings, path=PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = {k: v for k, v in settings.items() if k in DEFAULTS}
    path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf8")
    return path


def describe(settings):
    """Riepilogo leggibile delle scelte, per l'utente."""
    ai = {"cli": "Claude Code", "api": "Claude con chiave API", "local": f"modello locale {settings['model']}"}.get(settings["ai"], "?")
    return (f"AI: {ai} · GitHub: {settings['github']}" + (f" ({settings['github_user']})" if settings["github_user"] else "") +
            f" · formato: {', '.join(settings['formats'])} · offerta: {settings['offer'] or 'da indicare'}")
