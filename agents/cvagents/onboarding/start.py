"""Il percorso guidato `cvagents start`: AI, anagrafica, import del CV, GitHub."""

from cvagents import github_public, importer
from cvagents.llm.base import LLMError
from cvagents.onboarding import cv_text, extract
from cvagents.onboarding.ai_setup import SetupIncomplete, ensure_provider
from cvagents.onboarding.ask_profile import ask_profile
from cvagents.onboarding.profile import save_profile

INTRO = "CV Base: ti aiuto a costruire un CV su misura per ogni offerta, usando solo fatti veri su di te."


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


def import_github(prompter, conn, login):
    if not login or not prompter.confirm(f"Leggo i repo pubblici di {login} su GitHub?"):
        return 0
    try:
        return github_public.sync_public(conn, login)
    except OSError as err:
        prompter.say(f"GitHub non raggiungibile: {err}")
        return 0


def run_start(prompter, conn, provider=None):
    """Percorso completo. Ritorna (provider, riepilogo) oppure (None, messaggio) se non si può proseguire."""
    prompter.say(INTRO)
    try:
        provider = provider or ensure_provider(prompter)
    except SetupIncomplete as err:
        return None, str(err)
    prompter.say(f"Userò: {provider.describe()}\n")
    data = ask_profile(prompter)
    save_profile(conn, data)
    voci = import_cv(prompter, conn, provider)
    repos = import_github(prompter, conn, data.get("github_login", ""))
    return provider, f"Fatto, {data['name']}: {voci} voci dal CV, {repos} repo GitHub. Ora: cvagents cv <file offerta>"
