"""Dalla valutazione ai miglioramenti: unisce i pareri e riscrive solo ciò che l'utente accetta."""
import json

from cvagents.pipeline.generate import CV_SCHEMA, FORMAT, parse_cv
from cvagents.pipeline.review import REVIEW_SCHEMA, parse_review


def merge_reviews(provider, reviews):
    """Riassume i pareri di HR e manager in punteggio, problemi e azioni brevi."""
    ask = ("Unisci le due valutazioni in una: 'score' (la media, intero), 'problems' (max 5) e 'fixes' (max 5 azioni concrete "
           "e brevi). Non aggiungere nulla che non sia nelle valutazioni. Solo JSON.")
    raw = provider.chat([{"role": "system", "content": ask},
                         {"role": "user", "content": f"HR:\n{reviews['hr'][:6000]}\n\nMANAGER:\n{reviews['manager'][:6000]}"}],
                        schema=REVIEW_SCHEMA)
    return parse_review(raw)


def apply_fixes(provider, system, cv, fixes, lang):
    user = (f"CV attuale:\n{json.dumps(cv, ensure_ascii=False)}\n\nApplica SOLO queste azioni, senza cambiare altro e senza "
            "inventare fatti:\n- " + "\n- ".join(fixes) + f"\nLingua: {lang}.")
    raw = provider.chat([{"role": "system", "content": system + "\n\n" + FORMAT}, {"role": "user", "content": user}], schema=CV_SCHEMA)
    return parse_cv(raw)
