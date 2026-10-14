"""Sceglie (e se serve prepara) l'AI: modello locale con Ollama, Claude con chiave, o Claude Code."""
import sys
from pathlib import Path

from cvagents import local_setup, ollama_install, sysinfo
from cvagents.llm import OllamaProvider, available
from cvagents.llm import ollama
from cvagents.progress import progress

LOCAL = "setup-local"


class SetupIncomplete(Exception):
    """Non si può proseguire con l'AI scelta (spiegazione nel messaggio)."""


def install_if_missing(prompter):
    binary = local_setup.find_ollama()
    if binary:
        return binary
    if sys.platform != "linux":
        raise SetupIncomplete(local_setup.install_hint() + " Poi riavvia `cvagents start`.")
    prompter.say("Ollama non è installato. " + local_setup.install_hint())
    if not prompter.confirm("Lo scarico ora in una cartella tua (senza sudo)?"):
        raise SetupIncomplete("Installa Ollama e riavvia `cvagents start`.")
    folder = prompter.text("In quale cartella?", str(Path.home() / "ollama"))
    return ollama_install.install_linux(folder, progress)


def setup_local(prompter):
    binary = install_if_missing(prompter)
    if not ollama.is_up():
        models_dir = prompter.text("Dove salvare i modelli? (vuoto = cartella predefinita di Ollama)", "")
        ollama_install.start_server(binary, models_dir or None)
    have = ollama.list_models()
    model = have[0] if have else local_setup.pick_model(sysinfo.total_ram_gb())
    if not have:
        size = local_setup.MODEL_SIZE_GB.get(model, 0)
        if not prompter.confirm(f"Scarico il modello {model} (circa {size} GB, gratis, resta sul tuo computer)?"):
            raise SetupIncomplete("Senza un modello non posso continuare.")
        local_setup.pull_model(model, on_progress=progress)
        prompter.say("")
    return OllamaProvider(model)


def ensure_provider(prompter):
    """Fa scegliere l'AI all'utente e ritorna un provider pronto."""
    found = available()
    choices = [(label, label) for _, label, _ in found]
    if not any(i == "local" for i, _, _ in found):
        choices.append((LOCAL, "Scarica un modello locale (gratis, senza chiavi, i dati restano qui)"))
    picked = prompter.select("Quale AI vuoi usare?", choices)
    if picked == LOCAL:
        return setup_local(prompter)
    return next(factory() for _, label, factory in found if label == picked)
