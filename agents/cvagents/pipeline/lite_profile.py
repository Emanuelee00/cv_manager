"""Titolo e profilo scritti dall'AI, controllati dal codice (numeri senza fonte, elenchi di parole)."""
import json
import re

from cvagents import checks
from cvagents.pipeline.translate import LANG_NAMES

BANNED = ("expert", "experte", "esperto", "passionn", "appassionat", "passionate", "dynamique", "dinamic", "rigoureu", "rigoros",
          "motivé", "motivat", "à l'aise", "a mio agio")
PROFILE_SCHEMA = {"type": "object", "required": ["headline", "profile"],
                  "properties": {"headline": {"type": "string"}, "profile": {"type": "string"}}}


def looks_like_list(text):
    """Un profilo fatto di sole parole separate da virgole non è un profilo."""
    words = max(len(text.split()), 1)
    return text.count(",") / words > 0.15 or len(re.split(r"[.!?]", text)) < 2 and words > 25


def drop_unsupported(text, sources, name=""):
    """Toglie le frasi con numeri senza fonte, con parole vietate (es. «expert») o con il nome (terza persona)."""
    bad = set(checks.unsupported_numbers(text, sources))
    surname = name.split()[-1].lower() if name.split() else "\0"

    def keep(sentence):
        low = sentence.lower()
        return not (bad & checks.extract_facts(sentence)["numbers"]) and not any(w in low for w in BANNED) and surname not in low

    return " ".join(s for s in re.split(r"(?<=[.!?])\s+", text) if keep(s)).strip()


def ask_profile(provider, system, user):
    raw = provider.chat([{"role": "system", "content": system}, {"role": "user", "content": user}], schema=PROFILE_SCHEMA)
    try:
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        return str(data["headline"]).strip(), str(data["profile"]).strip()
    except (AttributeError, ValueError, KeyError, TypeError):
        return "", ""


def write_profile(provider, system, offer, candidate, items, lang):
    """Titolo e profilo dall'AI: se è un elenco di parole si ritenta una volta, poi si usa il titolo base del candidato."""
    facts = "\n".join(f"- {i['title']}: {i['text']}" for i in items if i["section"] in ("project", "experience", "education"))
    user = (f"OFFERTA:\n{offer[:3000]}\n\nCANDIDATO:\n{candidate}\n\nFATTI DEL CV:\n{facts}\n\n"
            f"Scrivi in {LANG_NAMES[lang]} un titolo mirato all'offerta e un profilo di 3-4 frasi complete che usa SOLO questi fatti. "
            "Prima persona sobria, senza nome né età (sono già nell'intestazione), senza superlativi né «expert». JSON.")
    sources = [candidate] + [i["text"] + " " + i["title"] for i in items]
    found = re.search(r"^NOME:\s*(.+)$", candidate, re.M)
    name = found.group(1) if found else ""
    base = re.search(r"^TITOLO BASE:\s*(.+)$", candidate, re.M)
    for strict in ("", "\nNON fare un elenco di parole: scrivi 3 frasi complete in prima persona sobria."):
        headline, profile = ask_profile(provider, system, user + strict)
        headline = headline if headline and not any(w in headline.lower() for w in BANNED) else (base.group(1) if base else "")
        profile = drop_unsupported(profile, sources, name)
        if profile and not looks_like_list(profile):
            return headline, profile
    return headline or (base.group(1) if base else ""), base.group(1) if base else ""
