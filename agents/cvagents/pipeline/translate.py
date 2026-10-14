"""Traduzione di una voce alla volta, accettata solo se i fatti restano identici."""
import re

from cvagents import checks
from cvagents.pipeline.lang import detect_lang

LANG_NAMES = {"fr": "francese", "it": "italiano", "en": "inglese"}


def translate_text(provider, text, lang):
    """Traduce una voce; se i fatti o la lunghezza non tornano, resta il testo originale."""
    if len(text) < 25:
        return text
    ask = f"Traduci in {LANG_NAMES[lang]} questo testo di CV. Stesso significato, nessuna aggiunta, stessi numeri e nomi. Rispondi solo con la traduzione."
    new = re.sub(r"\s*/no_\w+|\[[A-Z_]+\]", "", provider.chat([{"role": "system", "content": ask}, {"role": "user", "content": text}])).strip()
    if not new or checks.compare_facts(text, new) or not 0.5 <= len(new) / len(text) <= 1.8:
        return text
    return new


def translate_items(provider, items, lang):
    """Traduce i testi se l'archivio è in un'altra lingua (rilevata sull'insieme, non voce per voce)."""
    if not items or detect_lang(" ".join(i["text"] for i in items)) == lang:
        return items
    keep = ("language", "interest", "certification", "skill")
    done = [i if i["section"] in keep else {**i, "text": translate_text(provider, i["text"], lang)} for i in items]
    return [{**new, "translated": True} if new["text"] != old["text"] else new for new, old in zip(done, items)]
