"""The guided path `cvagents start`: language, AI, profile, CV, GitHub, offer and format; saves the choices."""
from cvagents import importer, settings
from cvagents.i18n import choose_language, t
from cvagents.llm.base import LLMError
from cvagents.onboarding import cv_text, extract
from cvagents.onboarding.ai_setup import SetupIncomplete, ensure_provider
from cvagents.onboarding.ask_profile import ask_profile
from cvagents.onboarding.github_step import choose_github, sync_github
from cvagents.onboarding.profile import save_profile


def import_cv(prompter, conn, provider):
    """Ask for the CV (file or pasted text), extract its entries and save the confirmed ones."""
    how = prompter.select(t("cv.question"), [("file", t("cv.option_file")), ("paste", t("cv.option_paste")), ("skip", t("cv.option_skip"))])
    if how == "skip":
        return 0
    try:
        text = cv_text.read_cv_text(prompter.text(t("cv.path"))) if how == "file" else prompter.text(t("cv.paste"))
        with prompter.step(t("step.read_cv")):
            entries = extract.extract_entries(provider, text)
    except (ValueError, OSError, LLMError) as err:
        prompter.say(t("cv.failed", error=err))
        return 0
    labels = [(i, f"{e['type']}: {e['title']}" + (" ⚠ " + t("cv.to_check") if e.get("note") else "")) for i, e in enumerate(entries)]
    chosen = prompter.checkbox(t("cv.keep_question"), labels) if labels else []
    return importer.add_entries(conn, [entries[i] for i in chosen])


def ask_output(prompter, chosen):
    """Offer (text file) and CV formats."""
    chosen["offer"] = prompter.text(t("start.offer_file"), chosen.get("offer", ""))
    chosen["formats"] = prompter.checkbox(t("start.formats"), [("pdf", "PDF"), ("docx", "Word (.docx)")]) or ["pdf"]
    return chosen


def run_start(prompter, conn, provider=None, settings_path=settings.PATH, provider_wrapper=None):
    """The whole path. Returns (provider, settings, summary) or (None, None, message)."""
    ui_lang = choose_language(prompter, settings.load(settings_path)["ui_lang"])
    prompter.say(t("start.intro"))
    try:
        provider, ai, model = (provider, "local" if provider.local else "api", "") if provider else ensure_provider(prompter)
    except SetupIncomplete as err:
        return None, None, str(err)
    provider = provider_wrapper(provider) if provider_wrapper else provider
    prompter.say(t("start.using", provider=provider.describe()) + "\n")
    data = ask_profile(prompter)
    save_profile(conn, data)
    count = import_cv(prompter, conn, provider)
    mode, user = choose_github(prompter, data.get("github_login", ""))
    repos = sync_github(prompter, conn, mode, user)
    chosen = ask_output(prompter, {**settings.load(settings_path), "ui_lang": ui_lang, "ai": ai, "model": model, "github": mode, "github_user": user})
    settings.save(chosen, settings_path)
    command = settings.RUN_COMMAND + ("" if chosen["offer"] else " OFFER=<file>")
    return provider, chosen, t("start.summary", name=data["name"], entries=count, repos=repos, choices=settings.describe(chosen), command=command)
