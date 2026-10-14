"""The guided path `cvagents start`: language, CV or from zero, AI, profile, entries, GitHub, offer (or LinkedIn search), format and style."""
from cvagents import ats_score, importer, settings
from cvagents.i18n import choose_language, t
from cvagents.layouts import STYLES
from cvagents.llm.base import LLMError
from cvagents.onboarding import cv_text, extract
from cvagents.onboarding.ai_setup import SetupIncomplete, ensure_provider
from cvagents.onboarding.ask_profile import ask_profile
from cvagents.onboarding.github_step import choose_github, sync_github
from cvagents.onboarding.job_search import ask_offer
from cvagents.onboarding.manual_entries import collect_entries
from cvagents.onboarding.profile import save_profile


def read_cv(prompter, how):
    """The CV text: pasted, or from a file asked again until it can be read (empty = skip)."""
    if how == "paste":
        return prompter.text(t("cv.paste"))
    while True:
        raw = prompter.text(t("cv.path"))
        if not raw:
            return ""
        try:
            return cv_text.read_cv_text(raw)
        except (ValueError, OSError) as err:
            prompter.say(t("cv.failed", error=err))


def import_cv(prompter, conn, provider, how):
    """Read the CV (file or pasted text), extract its entries and save the confirmed ones; or collect them by hand."""
    if how == "scratch":
        return importer.add_entries(conn, collect_entries(prompter))
    text = read_cv(prompter, how)
    if not text:
        return 0
    try:
        with prompter.step(t("step.read_cv")):
            entries = extract.extract_entries(provider, text)
    except (ValueError, OSError, LLMError) as err:
        prompter.say(t("cv.failed", error=err))
        return 0
    labels = [(i, f"{e['type']}: {e['title']}" + (" ⚠ " + t("cv.to_check") if e.get("note") else "")) for i, e in enumerate(entries)]
    chosen = prompter.checkbox(t("cv.keep_question"), labels) if labels else []
    return importer.add_entries(conn, [entries[i] for i in chosen])


def ask_output(prompter, chosen, profile):
    """Offer (text file or LinkedIn search), formats and style; each style shows the best ATS score it allows."""
    chosen["offer"] = ask_offer(prompter, profile, chosen.get("offer", ""))
    chosen["formats"] = prompter.checkbox(t("start.formats"), [("pdf", "PDF"), ("docx", "Word (.docx)")]) or ["pdf"]
    styles = sorted(STYLES, key=lambda s: -ats_score.best_possible(STYLES[s]))
    chosen["style"] = prompter.select(t("style.question"), [(s, t("style.option", style=t(f"style.{s}"), score=ats_score.best_possible(STYLES[s]),
                                                                   hint=t(f"style.hint_{s}"))) for s in styles])
    return chosen


def run_start(prompter, conn, provider=None, settings_path=settings.PATH, provider_wrapper=None):
    """The whole path. Returns (provider, settings, summary) or (None, None, message)."""
    ui_lang = choose_language(prompter, settings.load(settings_path)["ui_lang"])
    prompter.say(t("start.intro"))
    how = prompter.select(t("cv.question"), [("file", t("cv.option_file")), ("paste", t("cv.option_paste")), ("scratch", t("cv.option_scratch"))])
    try:
        provider, ai, model = (provider, "local" if provider.local else "api", "") if provider else ensure_provider(prompter)
    except SetupIncomplete as err:
        return None, None, str(err)
    provider = provider_wrapper(provider) if provider_wrapper else provider
    prompter.say(t("start.using", provider=provider.describe()) + "\n")
    data = ask_profile(prompter)
    save_profile(conn, data)
    count = import_cv(prompter, conn, provider, how)
    mode, user = choose_github(prompter, data.get("github_login", ""))
    repos = sync_github(prompter, conn, mode, user)
    chosen = ask_output(prompter, {**settings.load(settings_path), "ui_lang": ui_lang, "ai": ai, "model": model, "github": mode, "github_user": user}, data)
    settings.save(chosen, settings_path)
    command = settings.RUN_COMMAND + ("" if chosen["offer"] else " OFFER=<file>")
    return provider, chosen, t("start.summary", name=data["name"], entries=count, repos=repos, choices=settings.describe(chosen), command=command)
