"""Modo lite: la valutazione la fa il codice (parole chiave dell'offerta presenti o assenti nel CV)."""
from cvagents.pipeline import context
from cvagents.pipeline.keywords import coverage, flat, keywords
from cvagents.pipeline.lite_items import row_to_item
from cvagents.search import search


def suggestions(conn, missing, used_ids):
    """Per ogni parola assente, la voce del database che la conferma e che non è ancora nel CV."""
    found, skip = [], context.excluded_ids(conn)
    for word in missing:
        for row in search(conn, word, limit=4):
            if row["id"] not in used_ids and row["id"] not in skip and row["kind"] not in context.SKIP_KINDS and word.lower() in flat(row["body"] + row["title"]):
                found.append({"word": word, "row": row})
                break
    return found


def review(conn, provider, offer, cv_text, used_ids):
    """Ritorna (punteggio, problemi, proposte). Una proposta aggiunge una voce vera del database."""
    words = keywords(provider, offer)[:12]
    covered, missing = coverage(words, cv_text)
    options = suggestions(conn, missing, used_ids)
    score = max(1, round(10 * len(covered) / len(words))) if words else 5
    covered_by_options = {s["word"] for s in options}
    problems = [f"L'offerta cita «{w}»: " + ("una voce del database lo conferma, non è nel CV" if w in covered_by_options else
                "nessuna voce del database lo conferma (se è vero, aggiungilo a mano)") for w in missing[:6]]
    return score, problems, options


def option_label(option):
    return f"Aggiungere «{option['row']['title']}» (copre «{option['word']}»)"


def add_option(cv, option):
    return {**cv, "items": cv["items"] + [row_to_item(option["row"])]}
