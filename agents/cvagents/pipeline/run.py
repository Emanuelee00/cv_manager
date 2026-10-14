"""The CV path: generate, check, review, improve, humanize, then a one-page PDF (and Word)."""
from cvagents.i18n import ats_summary, t
from cvagents.pipeline import context, generate, humanize, improve, review
from cvagents.pipeline.lang import detect_lang
from cvagents.pipeline.lite_run import build_lite, lite_loop
from cvagents.pipeline.output import write_files
from cvagents.pipeline.review import cv_as_text
from cvagents.prompts import load_agent_prompt

LITE_SECTIONS = ("Style",)
GOOD_SCORE = 8


def build_cv(prompter, provider, system, offer, rows, candidate, lang):
    """First draft, questions to the candidate, fixes for the problems found by code."""
    ctx = context.format_context(rows)
    with prompter.step(t("step.draft")):
        cv = generate.generate(provider, system, offer, ctx, candidate, lang)
    answers = "\n".join(f"- {q}: {prompter.text(q)}" for q in cv["questions"])
    if answers.replace("\n", "").strip("- "):
        with prompter.step(t("step.draft_answers")):
            cv = generate.generate(provider, system, offer, ctx, candidate, lang, answers)
    for _ in range(2):
        problems = generate.find_problems(cv, rows, candidate)
        if not problems:
            break
        with prompter.step(t("step.repair", count=len(problems))):
            cv = generate.repair(provider, system, cv, problems, lang)
    return cv


def improve_loop(prompter, provider, system, offer, cv, lang):
    """Full mode: recruiter and manager separately, up to 3 rounds; the user chooses what to improve."""
    for round_number in range(3):
        reviews = review.review_full(provider, offer, cv, prompter.step)
        with prompter.step(t("step.merge")):
            result = improve.merge_reviews(provider, reviews)
        prompter.say("\n" + t("run.score", score=result["score"]) + "\n" + "\n".join(f"- {p}" for p in result["problems"]))
        if result["score"] >= GOOD_SCORE and not result["problems"]:
            break
        chosen = prompter.checkbox(t("run.which_fixes"), [(f, f) for f in result["fixes"]]) if result["fixes"] else []
        if not chosen:
            break
        with prompter.step(t("step.rewrite", count=len(chosen))):
            cv = improve.apply_fixes(provider, system, cv, chosen, lang)
        if round_number < 2 and not prompter.confirm(t("run.another_round")):
            break
    return cv


def natural_pass(prompter, provider, cv):
    """Humanizer pass: always on request, for channel A (a person) or B (a portal)."""
    if not prompter.confirm(t("run.humanize_question"), default=not provider.local):
        return cv
    channel = prompter.select(t("run.reader_question"), [("A", t("run.reader_person")), ("B", t("run.reader_portal"))])
    with prompter.step(t("step.humanizer", channel=channel)):
        new_cv, changed = humanize.humanize_cv(provider, cv, channel)
    prompter.say(t("run.humanized") if changed else t("run.humanizer_rejected"))
    return new_cv


def produce(prompter, candidate, cv, lang, folder, formats, style="classic"):
    """Preview in the terminal, confirmation, then the files: PDF always fitted to one page, Word with the same content."""
    prompter.say("\n" + t("run.preview") + "\n" + cv_as_text(cv))
    if not prompter.confirm(t("run.create_question")):
        return []
    with prompter.step(t("step.files_docx" if "docx" in formats else "step.files")):
        done = write_files(candidate, cv, lang, folder, formats, style)
    prompter.say(t("run.files", files=", ".join(map(str, done["files"])), pages=done["pages"]) +
                 ("\n" + t("run.dropped", items=", ".join(done["dropped"])) if done["dropped"] else ""))
    prompter.say(t("ats.score", score=done["score"], style=t(f"style.{style}")) + "\n" + ats_summary(done["problems"]))
    return done["files"]


def run_cv(prompter, conn, provider, offer, lang=None, folder="output", formats=("pdf",), style="classic"):
    """Return (created files, final cv). Never writes to the database."""
    lang = lang or detect_lang(offer)
    prompter.say(t("run.header", provider=provider.describe(), lang=lang, mode=t("run.mode_lite" if provider.local else "run.mode_full")))
    system = load_agent_prompt("cv-generator", None if not provider.local else LITE_SECTIONS)
    candidate = context.candidate_text(conn)
    if provider.local:
        cv = lite_loop(prompter, conn, provider, offer, build_lite(prompter, provider, system, conn, offer, lang))
    else:
        with prompter.step(t("step.search")):
            rows = context.retrieve(conn, provider, offer)
        cv = improve_loop(prompter, provider, system, offer, build_cv(prompter, provider, system, offer, rows, candidate, lang), lang)
    cv = natural_pass(prompter, provider, cv)
    return produce(prompter, candidate, cv, lang, folder, formats, style), cv
