"""Il flusso lite per modelli piccoli: il codice fa il lavoro pesante, l'AI solo traduzione e profilo."""
from cvagents.pipeline import context, lite_items, lite_profile, lite_review, translate
from cvagents.pipeline.review import cv_as_text


def build_lite(provider, system, conn, offer, lang):
    """Prima stesura: voci scelte dal codice, tradotte con controllo, profilo scritto dall'AI."""
    rows, candidate = context.retrieve(conn, provider, offer), context.candidate_text(conn)
    items = translate.translate_items(provider, lite_items.build_items(rows), lang)
    headline, profile = lite_profile.write_profile(provider, system, offer, candidate, items, lang)
    return {"headline": headline, "profile": profile, "items": items, "questions": []}


def lite_loop(prompter, conn, provider, offer, cv):
    """Una valutazione del codice; l'utente sceglie quali voci vere aggiungere."""
    used = {i["source_id"] for i in cv["items"]}
    score, problems, options = lite_review.review(conn, provider, offer, cv_as_text(cv), used)
    prompter.say(f"\nCopertura dell'offerta: {score}/10\n" + "\n".join(f"- {p}" for p in problems))
    if not options:
        return cv
    chosen = prompter.checkbox("Quali voci aggiungo al CV?", [(i, lite_review.option_label(o)) for i, o in enumerate(options)])
    for i in chosen:
        cv = lite_review.add_option(cv, options[i])
    return cv
