"""Deterministic checks on AI-written text: done by code, not by the model."""
import re
import unicodedata

URL = re.compile(r"https?://[^\s)\]>\"']+")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?")
WORD = re.compile(r"[^\W\d_]{5,}")
STOPWORDS = frozenset("""
avec dans pour mais sont leur leurs cette ainsi entre depuis comme alors chez sans sous vers ceux
della delle degli nelle sulla nella sono anche questo questa quello molto tutti tutto dalla dallo
which their there where about these those would could should while through between during
""".split())


def extract_facts(text):
    """Numbers (comma = dot), URLs and emails found in the text."""
    urls = {u.rstrip(".,;") for u in URL.findall(text)}
    rest = EMAIL.sub(" ", URL.sub(" ", text))
    return {"numbers": {n.replace(",", ".") for n in NUMBER.findall(rest)},
            "urls": urls, "emails": set(EMAIL.findall(text))}


def compare_facts(before, after):
    """What was removed or added between two versions (should be empty for a humanizer)."""
    a, b = extract_facts(before), extract_facts(after)
    return {kind: {"removed": sorted(a[kind] - b[kind]), "added": sorted(b[kind] - a[kind])} for kind in a
            if a[kind] != b[kind]}


def unsupported_numbers(cv_text, source_texts):
    """Numbers in the CV that appear in no source (database entries, profile): suspected inventions."""
    allowed = set().union(*(extract_facts(t)["numbers"] for t in source_texts)) if source_texts else set()
    return sorted(extract_facts(cv_text)["numbers"] - allowed)


def repeated_words(text, ignore=()):
    """Meaningful words (5+ letters, compared without accents) used more than once."""
    flat = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    skip = {w.lower() for w in ignore} | STOPWORDS
    counts = {}
    for word in WORD.findall(flat):
        if word not in skip:
            counts[word] = counts.get(word, 0) + 1
    return {w: n for w, n in sorted(counts.items()) if n > 1}


def unknown_sources(source_ids, database_ids):
    """Ids cited by the AI that do not exist in the database."""
    return sorted(set(source_ids) - set(database_ids))
