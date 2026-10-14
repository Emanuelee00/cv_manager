"""Keywords of an offer and how much a text covers them."""
import json
import re
import unicodedata

KEYWORDS_SCHEMA = {"type": "object", "required": ["keywords"], "properties": {"keywords": {"type": "array", "items": {"type": "string"}}}}
GENERIC = frozenset("""technologie technologies competence competences compétence compétences experience expérience skills skill
outil outils developpement développement projet projets connaissance connaissances capacité capacités bonne bonnes
logiciel logiciels application applications entreprise entreprises equipe équipe full stack""".split())


def keyword_tokens(phrases):
    """From phrases to single meaningful words (no generic words), without duplicates."""
    found = []
    for phrase in phrases:
        for token in re.findall(r"[\w+#.]{3,}", phrase):
            if token.lower() not in GENERIC and token.lower() not in [f.lower() for f in found]:
                found.append(token)
    return found


def keywords(provider, offer):
    """Keywords of the offer (also translated); if the AI fails, the longest words of the offer."""
    ask = ("Extract 10-15 keywords about skills, technologies and role from this job offer, also translated into English, "
           "French, Italian and Spanish. JSON only.")
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
