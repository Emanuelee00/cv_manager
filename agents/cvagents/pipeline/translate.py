"""Translation one entry at a time, accepted only if the facts stay identical."""
import re

from cvagents import checks
from cvagents.pipeline.lang import detect_lang

LANG_NAMES = {"fr": "French", "it": "Italian", "en": "English", "es": "Spanish"}


def translate_text(provider, text, lang):
    """Translate one entry; if facts or length do not match, the original text stays."""
    if len(text) < 25:
        return text
    ask = f"Translate this CV text into {LANG_NAMES[lang]}. Same meaning, nothing added, same numbers and names. Answer only with the translation."
    new = re.sub(r"\s*/no_\w+|\[[A-Z_]+\]", "", provider.chat([{"role": "system", "content": ask}, {"role": "user", "content": text}])).strip()
    if not new or checks.compare_facts(text, new) or not 0.5 <= len(new) / len(text) <= 1.8:
        return text
    return new


def translate_items(provider, items, lang):
    """Translate the texts if the archive is in another language (detected on the whole, not entry by entry)."""
    if not items or detect_lang(" ".join(i["text"] for i in items)) == lang:
        return items
    keep = ("language", "interest", "certification", "skill")
    done = [i if i["section"] in keep else {**i, "text": translate_text(provider, i["text"], lang)} for i in items]
    return [{**new, "translated": True} if new["text"] != old["text"] else new for new, old in zip(done, items)]
