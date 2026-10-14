"""Modello locale con Ollama: scelta del modello, ricerca del programma, download."""
import shutil
import sys
from pathlib import Path

from cvagents.llm.ollama import DEFAULT_HOST, post_lines

# (RAM minima in GiB, modello). Dimensioni da registry.ollama.ai/library/qwen3: 1.4, 2.5, 5.2, 9.3 GB.
MODEL_TIERS = ((24, "qwen3:14b"), (12, "qwen3:8b"), (6, "qwen3:4b"), (0, "qwen3:1.7b"))
MODEL_SIZE_GB = {"qwen3:1.7b": 1.4, "qwen3:4b": 2.5, "qwen3:8b": 5.2, "qwen3:14b": 9.3}
HOME_CANDIDATES = (".local/bin/ollama", "ollama/bin/ollama")


def pick_model(ram_gb):
    """Il modello Qwen3 più grande che la RAM permette (RAM sconosciuta: il più piccolo)."""
    return next(model for minimum, model in MODEL_TIERS if ram_gb >= minimum)


def find_ollama(extra_dirs=()):
    """Percorso del programma `ollama` nel PATH o in cartelle note, altrimenti None."""
    found = shutil.which("ollama")
    if found:
        return found
    for base in (Path.home(), *map(Path, extra_dirs)):
        for rel in HOME_CANDIDATES:
            if (base / rel).is_file():
                return str(base / rel)
    return None


def install_hint(platform=None):
    """Come installare Ollama sul sistema dell'utente, in italiano."""
    platform = platform or sys.platform
    if platform == "win32":
        return "Windows: scarica l'installer da https://ollama.com/download e avvialo."
    if platform == "darwin":
        return "macOS: scarica l'app da https://ollama.com/download oppure `brew install ollama`."
    return ("Linux: `curl -fsSL https://ollama.com/install.sh | sh` (chiede sudo). Senza sudo: "
            "`cvagents doctor --install-here <cartella>` lo scarica in una cartella tua.")


def pull_model(model, host=DEFAULT_HOST, on_progress=None):
    """Scarica un modello. on_progress(stato, frazione 0..1 oppure None)."""
    for chunk in post_lines(f"{host}/api/pull", {"model": model, "stream": True}, timeout=3600):
        total, done = chunk.get("total"), chunk.get("completed")
        if on_progress:
            on_progress(chunk.get("status", ""), done / total if total and done is not None else None)
        if chunk.get("error"):
            raise RuntimeError(chunk["error"])
