"""Interface language (en, fr, it, es): every message the user reads goes through t()."""
from cvagents.messages import MESSAGES

LANGUAGES = (("en", "English"), ("fr", "Français"), ("it", "Italiano"), ("es", "Español"))
CURRENT = {"lang": "en"}


def set_language(lang):
    CURRENT["lang"] = lang if lang in dict(LANGUAGES) else "en"
    return CURRENT["lang"]


def language():
    return CURRENT["lang"]


def t(key, **values):
    """Message `key` in the current language (English if missing), with `values` filled in."""
    entry = MESSAGES[key]
    text = entry.get(CURRENT["lang"]) or entry["en"]
    return text.format(**values) if values else text


def choose_language(prompter, saved=""):
    """First question of the guided path, asked in all four languages. Returns the chosen code."""
    question = "Language · Langue · Lingua · Idioma"
    order = sorted(LANGUAGES, key=lambda pair: pair[0] != saved)
    return set_language(prompter.select(question, list(order)))


def ats_summary(problems):
    """One line per ATS problem found, or a single "ok" line."""
    return "\n".join(t(key, **values) for key, values in problems) if problems else t("ats.ok")
