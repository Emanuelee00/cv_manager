"""Il percorso guidato `cvagents start`: AI, anagrafica, CV, GitHub, offerta e formato; salva le scelte."""
from cvagents import importer, settings
from cvagents.llm.base import LLMError
from cvagents.onboarding import cv_text, extract
from cvagents.onboarding.ai_setup import SetupIncomplete, ensure_provider
from cvagents.onboarding.ask_profile import ask_profile
from cvagents.onboarding.github_step import choose_github, sync_github
from cvagents.onboarding.profile import save_profile

INTRO = "CV Base: ti aiuto a costruire un CV su misura per ogni offerta, usando solo fatti veri su di te."
FORMATS = (("pdf", "PDF"), ("docx", "Word (.docx)"))


def import_cv(prompter, conn, provider):
    """Chiede il CV (file o testo incollato), estrae le voci e salva quelle confermate."""
    how = prompter.select("Hai già un CV?", [("file", "Sì, ho un file (pdf, docx, txt)"), ("paste", "Lo incollo come testo"),
                                            ("skip", "No, per ora salto")])
    if how == "skip":
        return 0
    try:
        text = cv_text.read_cv_text(prompter.text("Percorso del file:")) if how == "file" else prompter.text("Incolla il testo:")
        prompter.say("Leggo il CV (con un modello piccolo può volerci qualche minuto)...")
        entries = extract.extract_entries(provider, text, lambda i: prompter.say(f"  parte {i}..."))
    except (ValueError, OSError, LLMError) as err:
        prompter.say(f"Non ci sono riuscito: {err}")
        return 0
    labels = [(i, f"{e['type']}: {e['title']}" + (" ⚠ da verificare" if e.get("note") else "")) for i, e in enumerate(entries)]
    chosen = prompter.checkbox("Queste voci vanno nel tuo archivio? (togli quelle sbagliate)", labels) if labels else []
    return importer.add_entries(conn, [entries[i] for i in chosen])


def ask_output(prompter, chosen):
    """Offerta (file di testo) e formati del CV."""
    chosen["offer"] = prompter.text("File di testo con l'offerta (vuoto = la indichi dopo con `cvagents run <file>`):", chosen.get("offer", ""))
    chosen["formats"] = prompter.checkbox("In che formato vuoi il CV?", list(FORMATS)) or ["pdf"]
    return chosen


def run_start(prompter, conn, provider=None, settings_path=settings.PATH):
    """Percorso completo. Ritorna (provider, impostazioni, riepilogo) o (None, None, messaggio)."""
    prompter.say(INTRO)
    try:
        provider, ai, model = (provider, "local" if provider.local else "api", "") if provider else ensure_provider(prompter)
    except SetupIncomplete as err:
        return None, None, str(err)
    prompter.say(f"Userò: {provider.describe()}\n")
    data = ask_profile(prompter)
    save_profile(conn, data)
    voci = import_cv(prompter, conn, provider)
    mode, user = choose_github(prompter, data.get("github_login", ""))
    repos = sync_github(prompter, conn, mode, user)
    chosen = ask_output(prompter, {**settings.load(settings_path), "ai": ai, "model": model, "github": mode, "github_user": user})
    settings.save(chosen, settings_path)
    summary = (f"Fatto, {data['name']}: {voci} voci dal CV, {repos} repo GitHub.\nScelte salvate: {settings.describe(chosen)}\n"
               f"Per far partire tutto con queste scelte: {settings.RUN_COMMAND}" + ("" if chosen["offer"] else " <file offerta>"))
    return provider, chosen, summary
