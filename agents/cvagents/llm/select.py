"""Quali provider AI sono utilizzabili adesso su questa macchina."""
import os

from cvagents.llm import claude_cli, ollama
from cvagents.llm.anthropic import AnthropicProvider
from cvagents.llm.claude_cli import ClaudeCliProvider
from cvagents.llm.ollama import OllamaProvider


def available(model=None, host=ollama.DEFAULT_HOST):
    """Elenco di (id, etichetta, factory). Il locale compare solo se Ollama risponde."""
    found = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        found.append(("api", AnthropicProvider.name, AnthropicProvider))
    if claude_cli.installed():
        found.append(("cli", ClaudeCliProvider.name, ClaudeCliProvider))
    if ollama.is_up(host):
        found.append(("local", OllamaProvider.name, lambda: OllamaProvider(model or first_local(host), host)))
    return found


def first_local(host):
    models = ollama.list_models(host)
    if not models:
        raise RuntimeError("Ollama è attivo ma non ha modelli: usa `cvagents doctor`")
    return models[0]
