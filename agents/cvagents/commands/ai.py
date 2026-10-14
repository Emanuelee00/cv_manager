"""Comandi dell'AI: doctor (controlli, installazione e download del modello locale)."""
from cvagents import doctor, local_setup, ollama_install, sysinfo
from cvagents.llm import ollama
from cvagents.onboarding.prompter import Aborted, QuestionaryPrompter
from cvagents.onboarding.start import run_start
from cvagents.progress import progress


def install_step(args):
    binary = ollama_install.install_linux(args.install_here, progress)
    return f"\nOllama installato in {binary}"


def pull_step(args):
    binary = local_setup.find_ollama(args.install_here or ())
    if not ollama.is_up() and binary:
        ollama_install.start_server(binary, args.models_dir)
    model = args.model or local_setup.pick_model(sysinfo.total_ram_gb())
    local_setup.pull_model(model, on_progress=progress)
    return f"\nModello {model} pronto"


def doctor_cmd(args, conn):
    steps = ([install_step] if args.install_here else []) + ([pull_step] if args.pull else [])
    done = [step(args) for step in steps]
    return "\n".join(done + doctor.report())


def start_cmd(args, conn):
    try:
        return run_start(QuestionaryPrompter(), conn)[1]
    except Aborted:
        return "Interrotto. Quello che avevi già confermato è salvato."


SPEC = [
    ("start", "Percorso guidato: AI, i tuoi dati, import del CV", [], start_cmd),
    ("doctor", "Controlla cosa c'è per l'AI; --install-here e --pull per il modello locale", [
        ("--install-here", {"default": None, "help": "installa Ollama in questa cartella, senza sudo (Linux)"}),
        ("--pull", {"action": "store_true", "help": "scarica il modello consigliato"}),
        ("--model", {"default": None}), ("--models-dir", {"default": None})], doctor_cmd),
]
