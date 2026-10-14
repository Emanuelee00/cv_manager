"""Headline and profile written by the AI, checked by code (numbers without a source, word lists, overclaiming)."""
import json
import re

from cvagents import checks
from cvagents.pipeline.translate import LANG_NAMES

BANNED = ("expert", "experte", "esperto", "passionn", "appassionat", "passionate", "dynamique", "dinamic", "rigoureu", "rigoros",
          "motivé", "motivat", "à l'aise", "a mio agio")
PROFILE_SCHEMA = {"type": "object", "required": ["headline", "profile"],
                  "properties": {"headline": {"type": "string"}, "profile": {"type": "string"}}}


def looks_like_list(text):
    """A profile made only of comma-separated words is not a profile."""
    words = max(len(text.split()), 1)
    return text.count(",") / words > 0.15 or len(re.split(r"[.!?]", text)) < 2 and words > 25


def drop_unsupported(text, sources, name=""):
    """Drop sentences with numbers without a source, banned words (e.g. "expert") or the name (third person)."""
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
    """Headline and profile from the AI: if it is a list of words, retry once, then fall back to the candidate's headline."""
    facts = "\n".join(f"- {i['title']}: {i['text']}" for i in items if i["section"] in ("project", "experience", "education"))
    user = (f"OFFER:\n{offer[:3000]}\n\nCANDIDATE:\n{candidate}\n\nCV FACTS:\n{facts}\n\n"
            f"Write in {LANG_NAMES[lang]} a headline aimed at the offer and a profile of 3-4 complete sentences that uses ONLY these facts. "
            "Plain first person, no name or age (they are already in the header), no superlatives, never 'expert'. JSON.")
    sources = [candidate] + [i["text"] + " " + i["title"] for i in items]
    found = re.search(r"^NAME:\s*(.+)$", candidate, re.M)
    name = found.group(1) if found else ""
    base = re.search(r"^HEADLINE:\s*(.+)$", candidate, re.M)
    for strict in ("", "\nDo NOT write a list of words: write 3 complete sentences in plain first person."):
        headline, profile = ask_profile(provider, system, user + strict)
        headline = headline if headline and not any(w in headline.lower() for w in BANNED) else (base.group(1) if base else "")
        profile = drop_unsupported(profile, sources, name)
        if profile and not looks_like_list(profile):
            return headline, profile
    return headline or (base.group(1) if base else ""), base.group(1) if base else ""
