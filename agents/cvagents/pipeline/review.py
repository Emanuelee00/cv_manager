"""Valutazione del CV: recruiter e hiring manager (insieme in modo lite, separati in parallelo in modo completo)."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext

from cvagents.llm.base import LLMError
from cvagents.prompts import load_agent_prompt

STRING = {"type": "string"}
REVIEW_SCHEMA = {"type": "object", "required": ["score", "problems", "fixes"], "properties": {
    "score": {"type": "integer"}, "problems": {"type": "array", "items": STRING}, "fixes": {"type": "array", "items": STRING}}}
LITE_ASK = ("Sei insieme una recruiter e un hiring manager tecnico. Valuta il CV per l'offerta: cosa è generico, cosa non è "
            "dimostrato, cosa manca rispetto all'offerta, cosa suona da testo IA. Non inventare. Rispondi solo con JSON: "
            "'score' da 1 a 10, 'problems' (max 5, ognuno cita la riga), 'fixes' (max 5 azioni concrete e brevi).")


def cv_as_text(cv):
    lines = [cv.get("headline", ""), cv["profile"]]
    lines += [f"[{i['section']}] {i['title']} {i.get('period', '')}: {i['text']}" + ("  (tradotto in automatico: rileggi)" if i.get("translated") else "")
              for i in cv["items"]]
    return "\n".join(lines)


def parse_review(raw):
    try:
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        return {"score": int(data["score"]), "problems": [str(p) for p in data["problems"]], "fixes": [str(f) for f in data["fixes"]]}
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError("La valutazione non è leggibile") from err


def review_lite(provider, offer, cv):
    raw = provider.chat([{"role": "system", "content": LITE_ASK},
                         {"role": "user", "content": f"OFFERTA:\n{offer[:4000]}\n\nCV:\n{cv_as_text(cv)}"}], schema=REVIEW_SCHEMA)
    return parse_review(raw)


def review_full(provider, offer, cv, step=nullcontext):
    """HR e manager con i loro prompt completi, in parallelo (ognuno con il suo passo a schermo). Ritorna i due testi."""
    message = f"OFFERTA:\n{offer[:6000]}\n\nCV:\n{cv_as_text(cv)}"
    labels = {"hr-reviewer": "Recruiter", "manager": "Manager tecnico"}

    def ask(name):
        with step(labels[name]):
            return provider.chat([{"role": "system", "content": load_agent_prompt(name)}, {"role": "user", "content": message}])

    with ThreadPoolExecutor(max_workers=2) as pool:
        hr, manager = pool.map(ask, ("hr-reviewer", "manager"))
    return {"hr": hr, "manager": manager}
