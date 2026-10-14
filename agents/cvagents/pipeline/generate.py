"""Scrive il CV come dati strutturati e lo controlla con il codice."""
import json
import re

from cvagents import checks
from cvagents.llm.base import LLMError

SECTIONS = ["education", "experience", "project", "skill", "language", "certification", "interest"]
STRING = {"type": "string"}
CV_SCHEMA = {"type": "object", "required": ["profile", "items"], "properties": {
    "headline": STRING, "profile": STRING, "questions": {"type": "array", "items": STRING},
    "items": {"type": "array", "items": {"type": "object", "required": ["section", "title", "text", "source_id"], "properties": {
        "section": {"type": "string", "enum": SECTIONS}, "title": STRING, "period": STRING, "text": STRING, "source_id": STRING}}}}}
FORMAT = ("Rispondi solo con JSON. 'profile': 3-4 frasi. 'headline': titolo mirato all'offerta. Ogni elemento di 'items' ha "
          "'source_id' = l'id tra parentesi quadre della voce degli ESTRATTI da cui viene. Non usare numeri o fatti che non "
          "sono negli ESTRATTI o nei dati del CANDIDATO. Dubbi o dati mancanti: scrivili in 'questions'.")


def parse_cv(raw):
    match = re.search(r"\{.*\}", raw, re.S)
    try:
        cv = json.loads(match.group(0))
        items = [i for i in cv["items"] if isinstance(i, dict) and i.get("section") in SECTIONS and i.get("title")]
        return {"headline": cv.get("headline", ""), "profile": cv["profile"], "items": items, "questions": cv.get("questions") or []}
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError("Il CV prodotto non è leggibile") from err


def generate(provider, system, offer, context, candidate, lang, answers=""):
    user = (f"OFFERTA:\n{offer[:5000]}\n\nCANDIDATO:\n{candidate}\n\nESTRATTI DEL DATABASE:\n{context}\n\n"
            f"RISPOSTE DEL CANDIDATO:\n{answers or 'nessuna'}\n\nScrivi il CV in lingua: {lang}.")
    raw = provider.chat([{"role": "system", "content": system + "\n\n" + FORMAT}, {"role": "user", "content": user}], schema=CV_SCHEMA)
    return parse_cv(raw)


def find_problems(cv, rows, candidate):
    """Problemi verificabili dal codice: id inventati, numeri senza fonte, parole ripetute."""
    texts = [cv["profile"]] + [f"{i['title']} {i.get('period', '')} {i['text']}" for i in cv["items"]]
    sources = [r["body"] + " " + r["title"] for r in rows] + [candidate]
    found = []
    unknown = checks.unknown_sources([i["source_id"] for i in cv["items"]], [r["id"] for r in rows])
    if unknown:
        found.append(f"Id non presenti negli estratti: {', '.join(unknown)}. Usa solo gli id degli ESTRATTI.")
    invented = checks.unsupported_numbers(" ".join(texts), sources)
    if invented:
        found.append(f"Numeri senza fonte negli estratti: {', '.join(invented)}. Toglili o usa solo numeri degli estratti.")
    repeats = checks.repeated_words(" ".join(texts))
    if repeats:
        found.append("Parole ripetute (usa ciascuna una sola volta): " + ", ".join(list(repeats)[:8]))
    return found


def repair(provider, system, cv, problems, lang):
    user = f"CV da correggere:\n{json.dumps(cv, ensure_ascii=False)}\n\nCorreggi SOLO questi problemi, senza cambiare altro:\n- " + "\n- ".join(problems)
    raw = provider.chat([{"role": "system", "content": system + "\n\n" + FORMAT}, {"role": "user", "content": user + f"\nLingua: {lang}."}], schema=CV_SCHEMA)
    return parse_cv(raw)
