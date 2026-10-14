"""Le tre scelte di AI: Claude Code (login, nessuna chiave), Claude con chiave API, modello locale gratuito."""
import os
import sys
from pathlib import Path

from cvagents import local_setup, ollama_install, sysinfo
from cvagents.llm import AnthropicProvider, ClaudeCliProvider, OllamaProvider, claude_cli, ollama
from cvagents.progress import progress

CHOICES = (("cli", "Claude Code: usa il tuo login, nessuna chiave"), ("api", "Claude con chiave API (a consumo)"),
           ("local", "Modello locale gratuito: senza chiavi, i dati restano sul computer"))
CLAUDE_TIP = "Se hai Claude Code aperto in questa cartella puoi anche scrivere /cv-start: tutto avviene nella chat, con anteprima."


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
    return ollama_install.install_linux(prompter.text("In quale cartella?", str(Path.home() / "ollama")), progress)


def setup_local(prompter, model=None):
    """Avvia Ollama se serve e scarica un modello adatto alla RAM (con conferma). Ritorna il provider."""
    binary = install_if_missing(prompter)
    if not ollama.is_up():
        ollama_install.start_server(binary, prompter.text("Dove salvare i modelli? (vuoto = predefinito)", "") or None)
    have = ollama.list_models()
    model = model or (have[0] if have else local_setup.pick_model(sysinfo.total_ram_gb()))
    if model not in have:
        size = local_setup.MODEL_SIZE_GB.get(model, "?")
        if not prompter.confirm(f"Scarico il modello {model} (circa {size} GB, gratis, resta sul tuo computer)?"):
            raise SetupIncomplete("Senza un modello locale non posso continuare.")
        local_setup.pull_model(model, on_progress=progress)
        prompter.say("")
    return OllamaProvider(model)


def make_provider(prompter, choice, model=None):
    if choice == "cli":
        if not claude_cli.installed():
            raise SetupIncomplete("Claude Code non trovato: installalo (https://claude.com/claude-code), fai login e riprova, oppure scegli un'altra opzione.")
        return ClaudeCliProvider()
    if choice == "api":
        key = os.environ.get("ANTHROPIC_API_KEY") or prompter.text("Incolla la chiave API Anthropic (non viene salvata su disco):", hidden=True)
        if not key:
            raise SetupIncomplete("Serve una chiave API.")
        os.environ["ANTHROPIC_API_KEY"] = key
        prompter.say("Per non reinserirla la prossima volta: export ANTHROPIC_API_KEY=... nel tuo terminale.")
        return AnthropicProvider(key)
    return setup_local(prompter, model)


def ensure_provider(prompter, attempts=3):
    """Mostra sempre le tre scelte con il loro stato; se una non è pronta spiega e fa riscegliere."""
    status = {"cli": "trovato" if claude_cli.installed() else "non trovato",
              "api": "chiave presente" if os.environ.get("ANTHROPIC_API_KEY") else "serve la chiave",
              "local": "attivo" if ollama.is_up() else "da preparare"}
    prompter.say(CLAUDE_TIP)
    for _ in range(attempts):
        choice = prompter.select("Quale AI vuoi usare?", [(c, f"{label} [{status[c]}]") for c, label in CHOICES])
        try:
            provider = make_provider(prompter, choice)
            return provider, choice, getattr(provider, "model", "")
        except SetupIncomplete as err:
            prompter.say(str(err))
    raise SetupIncomplete("Nessuna AI pronta. Lancia `cvagents doctor` per capire cosa manca.")
