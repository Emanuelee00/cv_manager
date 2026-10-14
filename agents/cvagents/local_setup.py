"""Local model with Ollama: model choice, finding the program, download."""
import shutil
import sys
from pathlib import Path

from cvagents.i18n import t
from cvagents.llm.ollama import DEFAULT_HOST, post_lines

# (minimum RAM in GiB, model). Sizes from registry.ollama.ai/library/qwen3: 1.4, 2.5, 5.2, 9.3 GB.
MODEL_TIERS = ((24, "qwen3:14b"), (12, "qwen3:8b"), (6, "qwen3:4b"), (0, "qwen3:1.7b"))
MODEL_SIZE_GB = {"qwen3:1.7b": 1.4, "qwen3:4b": 2.5, "qwen3:8b": 5.2, "qwen3:14b": 9.3}
HOME_CANDIDATES = (".local/bin/ollama", "ollama/bin/ollama")


def pick_model(ram_gb):
    """The largest Qwen3 model the RAM allows (unknown RAM: the smallest)."""
    return next(model for minimum, model in MODEL_TIERS if ram_gb >= minimum)


def find_ollama(extra_dirs=()):
    """Path of the `ollama` program in PATH or in known folders, otherwise None."""
    found = shutil.which("ollama")
    if found:
        return found
    for base in (Path.home(), *map(Path, extra_dirs)):
        for rel in HOME_CANDIDATES:
            if (base / rel).is_file():
                return str(base / rel)
    return None


def install_hint(platform=None):
    """How to install Ollama on the user's system."""
    platform = platform or sys.platform
    return t({"win32": "ollama.hint_windows", "darwin": "ollama.hint_macos"}.get(platform, "ollama.hint_linux"))


def pull_model(model, host=DEFAULT_HOST, on_progress=None):
    """Download a model. on_progress(status, fraction 0..1 or None)."""
    for chunk in post_lines(f"{host}/api/pull", {"model": model, "stream": True}, timeout=3600):
        total, done = chunk.get("total"), chunk.get("completed")
        if on_progress:
            on_progress(chunk.get("status", ""), done / total if total and done is not None else None)
        if chunk.get("error"):
            raise RuntimeError(chunk["error"])
