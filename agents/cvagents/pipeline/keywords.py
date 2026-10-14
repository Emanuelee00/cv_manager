"""Parole chiave di un'offerta e quanto un testo le copre."""
import json
import re
import unicodedata

KEYWORDS_SCHEMA = {"type": "object", "required": ["keywords"], "properties": {"keywords": {"type": "array", "items": {"type": "string"}}}}
GENERIC = frozenset("""technologie technologies competence competences compétence compétences experience expérience skills skill
outil outils developpement développement projet projets connaissance connaissances capacité capacités bonne bonnes
logiciel logiciels application applications entreprise entreprises equipe équipe full stack""".split())


def keyword_tokens(phrases):
    """Da frasi a parole singole significative (senza parole generiche), senza doppioni."""
    found = []
    for phrase in phrases:
        for token in re.findall(r"[\w+#.]{3,}", phrase):
            if token.lower() not in GENERIC and token.lower() not in [f.lower() for f in found]:
                found.append(token)
    return found


def keywords(provider, offer):
    """Parole chiave dell'offerta (anche tradotte); se l'AI fallisce, le parole più lunghe dell'offerta."""
    ask = "Estrai da questa offerta 10-15 parole chiave su competenze, tecnologie e ruolo, anche tradotte in italiano, francese e inglese. Solo JSON."
    try:
        raw = provider.chat([{"role": "system", "content": ask}, {"role": "user", "content": offer[:6000]}], schema=KEYWORDS_SCHEMA)
        found = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["keywords"]
        return keyword_tokens([k for k in found if isinstance(k, str)])[:20]
    except (AttributeError, ValueError, KeyError, TypeError, OSError):
        return sorted(set(re.findall(r"\w{6,}", offer)), key=len, reverse=True)[:15]


def flat(text):
    return unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()


def coverage(keywords, cv_text):
    text = flat(cv_text)
    covered = [k for k in keywords if flat(k) in text]
    return covered, [k for k in keywords if k not in covered]
