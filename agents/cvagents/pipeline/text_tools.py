"""Pulizia dei testi delle voci: titoli, frasi troppo lunghe, descrizioni dei repo."""
import re

SKIP_PREFIXES = ("Tag:", "Linguaggi:", "Commit:", "README:", "Linguaggio:", "Topic:", "DA COMPLETARE", "DA VERIFICARE")
MAX_CHARS = 260


def clean_title(title):
    return re.sub(r"\s+—\s+Anthropic Academy$", "", title)


def cut_sentence(text, limit=MAX_CHARS):
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("; "))
    return cut[:end + 1] if end > limit // 2 else cut.rsplit(" ", 1)[0] + "…"


def readme_summary(body):
    """Prima frase utile del README (senza titoli, link o markdown), per i repo senza descrizione."""
    readme = body.split("README:", 1)[-1] if "README:" in body else ""
    for paragraph in re.split(r"\n\s*\n", readme):
        text = re.sub(r"[#*>`_\[\]()]|!\S+|https?://\S+", " ", paragraph)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 40 and not text.lower().startswith(("this activity", "*this activity", "install", "usage")):
            return text
    return ""


def repo_text(body):
    """Descrizione del repo (prima riga del corpo) oppure riassunto del README."""
    first = body.split("\n", 1)[0].strip()
    return first if len(first) > 20 and not first.startswith(("Linguaggi:", "Commit:")) else readme_summary(body)
