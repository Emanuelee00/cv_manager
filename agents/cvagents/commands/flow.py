"""Comandi del percorso: start (guidato), cv e run (con le scelte salvate), build (file da un CV già pronto)."""
import json

from cvagents import settings
from cvagents.onboarding import Aborted, QuestionaryPrompter, SetupIncomplete, ensure_provider, make_provider, run_start
from cvagents.pipeline import candidate_text, run_cv, write_files


def start_cmd(args, conn):
    try:
        prompter = QuestionaryPrompter()
        provider, chosen, summary = run_start(prompter, conn)
        if provider and chosen["offer"] and prompter.confirm("Faccio partire subito il CV per questa offerta?"):
            run_cv(prompter, conn, provider, open(chosen["offer"], encoding="utf8").read(), chosen["lang"] or None, chosen["out"], chosen["formats"])
        return summary
    except Aborted:
        return "Interrotto. Quello che avevi già confermato è salvato."


def cv_cmd(args, conn):
    try:
        prompter = QuestionaryPrompter()
        provider = ensure_provider(prompter)[0]
        files, _ = run_cv(prompter, conn, provider, open(args.offer, encoding="utf8").read(), args.lang, args.out, args.format)
        return "Pronto: " + ", ".join(map(str, files)) if files else "Nessun file creato."
    except (SetupIncomplete, Aborted) as err:
        return str(err) or "Interrotto."


def run_cmd(args, conn):
    """Rilancia tutto con le scelte di `start`, senza rifare le domande iniziali."""
    chosen = settings.load()
    offer = args.offer or chosen["offer"]
    if not chosen["ai"] or not offer:
        return "Prima lancia `cvagents start` (oppure indica il file: cvagents run offerta.txt)."
    prompter = QuestionaryPrompter()
    prompter.say(settings.describe({**chosen, "offer": offer}))
    try:
        provider = make_provider(prompter, chosen["ai"], chosen["model"] or None)
        files, _ = run_cv(prompter, conn, provider, open(offer, encoding="utf8").read(), chosen["lang"] or None, chosen["out"], chosen["formats"])
        return "Pronto: " + ", ".join(map(str, files)) if files else "Nessun file creato."
    except (SetupIncomplete, Aborted) as err:
        return str(err) or "Interrotto."


def build_cmd(args, conn):
    """Crea PDF/Word da un CV in JSON (usato da /cv-start e /cv-loop in Claude Code, dopo la conferma)."""
    with open(args.cv_json, encoding="utf8") as f:
        cv = json.load(f)
    files, pages, dropped = write_files(candidate_text(conn), cv, args.lang, args.out, args.format)
    return f"File: {', '.join(map(str, files))} · PDF {pages} pagina/e" + (f" · tolte: {', '.join(dropped)}" if dropped else "")


FORMAT = ("--format", {"nargs": "+", "choices": ["pdf", "docx"], "default": ["pdf"]})
SPEC = [
    ("start", "Percorso guidato: AI, i tuoi dati, CV, GitHub, offerta e formato", [], start_cmd),
    ("cv", "CV per un'offerta, scegliendo l'AI ora", [("offer", {}), ("--lang", {"default": None, "choices": ["fr", "it", "en"]}),
                                                     ("--out", {"default": "output"}), FORMAT], cv_cmd),
    ("run", "Fa partire tutto con le scelte salvate da start", [("offer", {"nargs": "?", "default": ""})], run_cmd),
    ("build", "Crea PDF/Word da un CV in JSON", [("cv_json", {}), ("--lang", {"default": "fr"}), ("--out", {"default": "output"}), FORMAT], build_cmd),
]
