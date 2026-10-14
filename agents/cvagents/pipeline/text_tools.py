"""Cleaning entry texts: titles, overlong sentences, repo descriptions."""
import re

SKIP_PREFIXES = ("Tag:", "Tags:", "Languages:", "Language:", "Linguaggi:", "Linguaggio:", "Commit:", "README:", "Topic:", "Topics:",
                 "TO COMPLETE", "TO CHECK", "DA COMPLETARE", "DA VERIFICARE")
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
    """First useful sentence of the README (no headings, links or markdown), for repos without a description."""
    readme = body.split("README:", 1)[-1] if "README:" in body else ""
    for paragraph in re.split(r"\n\s*\n", readme):
        text = re.sub(r"[#*>`_\[\]()]|!\S+|https?://\S+", " ", paragraph)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 40 and not text.lower().startswith(("this activity", "*this activity", "install", "usage")):
            return text
    return ""


def repo_text(body):
    """Repo description (first line of the body) or a README summary."""
    first = body.split("\n", 1)[0].strip()
    return first if len(first) > 20 and not first.startswith(("Languages:", "Linguaggi:", "Commit:")) else readme_summary(body)
