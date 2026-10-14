"""Choices made with `cvagents start`, saved so `cvagents run` can redo everything. API keys are never written to disk."""
import json
from pathlib import Path

from cvagents.i18n import t

PATH = Path(__file__).resolve().parent.parent / "data" / "settings.json"
DEFAULTS = {"ui_lang": "", "ai": "", "model": "", "github": "skip", "github_user": "", "offer": "", "lang": "",
            "formats": ["pdf"], "style": "classic", "out": "output"}
RUN_COMMAND = "make run"


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
    """Readable summary of the saved choices."""
    ai = {"cli": "Claude Code", "api": t("settings.ai_api"), "local": t("settings.ai_local", model=settings["model"])}.get(settings["ai"], "?")
    github = t(f"settings.github_{settings['github']}") + (f" ({settings['github_user']})" if settings["github_user"] else "")
    formats = ", ".join(settings["formats"]) + f" · {t('style.' + settings['style'])}"
    return t("settings.summary", ai=ai, github=github, formats=formats, offer=settings["offer"] or t("settings.no_offer"))
