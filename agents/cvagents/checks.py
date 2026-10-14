"""Controlli deterministici sul testo prodotto dall'AI: li fa il codice, non il modello."""
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
    """Numeri (virgola = punto), URL ed email presenti nel testo."""
    urls = {u.rstrip(".,;") for u in URL.findall(text)}
    rest = EMAIL.sub(" ", URL.sub(" ", text))
    return {"numbers": {n.replace(",", ".") for n in NUMBER.findall(rest)},
            "urls": urls, "emails": set(EMAIL.findall(text))}


def compare_facts(before, after):
    """Cosa è stato tolto o aggiunto tra due versioni (dovrebbe essere vuoto per un humanizer)."""
    a, b = extract_facts(before), extract_facts(after)
    return {kind: {"removed": sorted(a[kind] - b[kind]), "added": sorted(b[kind] - a[kind])} for kind in a
            if a[kind] != b[kind]}


def unsupported_numbers(cv_text, source_texts):
    """Numeri nel CV che non compaiono in nessuna fonte (voci del database, profilo): sospetti inventati."""
    allowed = set().union(*(extract_facts(t)["numbers"] for t in source_texts)) if source_texts else set()
    return sorted(extract_facts(cv_text)["numbers"] - allowed)


def repeated_words(text, ignore=()):
    """Parole significative (5+ lettere, senza accenti per il confronto) usate più di una volta."""
    flat = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    skip = {w.lower() for w in ignore} | STOPWORDS
    counts = {}
    for word in WORD.findall(flat):
        if word not in skip:
            counts[word] = counts.get(word, 0) + 1
    return {w: n for w, n in sorted(counts.items()) if n > 1}


def unknown_sources(source_ids, database_ids):
    """Id citati dall'AI che non esistono nel database."""
    return sorted(set(source_ids) - set(database_ids))
