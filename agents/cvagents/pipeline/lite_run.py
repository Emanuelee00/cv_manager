"""The lite flow for small models: code does the heavy lifting, the AI only translates and writes the profile."""
from cvagents.i18n import t
from cvagents.pipeline import context, lite_items, lite_profile, lite_review, translate
from cvagents.pipeline.review import cv_as_text


def build_lite(prompter, provider, system, conn, offer, lang):
    """First draft: entries chosen by code, translated with checks, profile written by the AI."""
    with prompter.step(t("step.keywords")):
        rows, candidate = context.retrieve(conn, provider, offer), context.candidate_text(conn)
        items = lite_items.build_items(rows)
    with prompter.step(t("step.translate", count=len(items))):
        items = translate.translate_items(provider, items, lang)
    with prompter.step(t("step.profile")):
        headline, profile = lite_profile.write_profile(provider, system, offer, candidate, items, lang)
    return {"headline": headline, "profile": profile, "items": items, "questions": [], "profile_by_ai": True}


def lite_loop(prompter, conn, provider, offer, cv):
    """One review done by code; the user chooses which real entries to add."""
    used = {i["source_id"] for i in cv["items"]}
    with prompter.step(t("step.coverage")):
        score, problems, options = lite_review.review(conn, provider, offer, cv_as_text(cv), used)
    prompter.say("\n" + t("run.coverage", score=score) + "\n" + "\n".join(f"- {p}" for p in problems))
    if not options:
        return cv
    chosen = prompter.checkbox(t("run.which_entries"), [(i, lite_review.option_label(o)) for i, o in enumerate(options)])
    for i in chosen:
        cv = lite_review.add_option(cv, options[i])
    return cv
