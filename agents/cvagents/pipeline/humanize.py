"""Passata di naturalezza sul testo del CV, accettata solo se i fatti restano identici."""
import json
import re

from cvagents import checks
from cvagents.llm.base import LLMError
from cvagents.prompts import load_agent_prompt

TEXTS_SCHEMA = {"type": "object", "required": ["texts"], "properties": {"texts": {"type": "array", "items": {"type": "string"}}}}
SECTIONS = ("Regola assoluta", "Cosa cerchi", "Come riscrivi")
MODES = {"A": "Modo A: tocco leggero, una persona leggerà il CV.", "B": "Modo B: riscrittura più profonda, il CV passa da un portale."}


def texts_of(cv):
    return [cv["profile"]] + [i["text"] for i in cv["items"]]


def facts_preserved(before, after):
    return not checks.compare_facts(" ".join(before), " ".join(after))


def humanize_cv(provider, cv, channel):
    """Ritorna (cv, esito). Se i fatti cambiano o il numero di testi non torna, resta l'originale."""
    system = load_agent_prompt("humanizer", sections=SECTIONS) + "\n\n" + MODES[channel] + (
        "\nRiscrivi ciascun testo mantenendo l'ordine. Rispondi solo con JSON: {\"texts\": [...]} con lo stesso numero di testi.")
    before = texts_of(cv)
    raw = provider.chat([{"role": "system", "content": system}, {"role": "user", "content": json.dumps(before, ensure_ascii=False)}], schema=TEXTS_SCHEMA)
    try:
        after = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["texts"]
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError("Risposta dello humanizer non leggibile") from err
    if len(after) != len(before) or not facts_preserved(before, after):
        return cv, "Lo humanizer ha cambiato dei fatti: tengo il testo originale."
    changed = {**cv, "profile": after[0], "items": [{**i, "text": t} for i, t in zip(cv["items"], after[1:])]}
    return changed, "Testo reso più naturale, fatti identici."
