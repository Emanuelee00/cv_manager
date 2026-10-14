"""The three AI choices: Claude Code (login, no key), Claude with an API key, a free local model."""
import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

from cvagents import local_setup, ollama_install, sysinfo
from cvagents.i18n import t
from cvagents.llm import AnthropicProvider, ClaudeCliProvider, OllamaProvider, claude_cli, ollama
from cvagents.progress import progress

CHOICES = ("cli", "api", "local")


class SetupIncomplete(Exception):
    """The chosen AI cannot be used (the message explains why)."""


def install_if_missing(prompter):
    binary = local_setup.find_ollama()
    if binary:
        return binary
    if sys.platform != "linux":
        raise SetupIncomplete(local_setup.install_hint() + " " + t("ai.restart"))
    prompter.say(t("ai.ollama_missing") + " " + local_setup.install_hint())
    if not prompter.confirm(t("ai.install_here")):
        raise SetupIncomplete(t("ai.install_then_restart"))
    return ollama_install.install_linux(prompter.text(t("ai.which_folder"), str(Path.home() / "ollama")), progress)


def setup_local(prompter, model=None):
    """Start Ollama if needed and download a model that fits the RAM (after confirmation). Returns the provider."""
    binary = install_if_missing(prompter)
    if not ollama.is_up():
        ollama_install.start_server(binary, prompter.text(t("ai.models_dir"), "") or None)
    have = ollama.list_models()
    model = model or (have[0] if have else local_setup.pick_model(sysinfo.total_ram_gb()))
    if model not in have:
        size = local_setup.MODEL_SIZE_GB.get(model, "?")
        if not prompter.confirm(t("ai.download_model", model=model, size=size)):
            raise SetupIncomplete(t("ai.no_model"))
        local_setup.pull_model(model, on_progress=progress)
        prompter.say("")
    return OllamaProvider(model)


def make_provider(prompter, choice, model=None):
    if choice == "cli":
        if not claude_cli.installed():
            raise SetupIncomplete(t("ai.claude_missing"))
        return ClaudeCliProvider()
    if choice == "api":
        key = os.environ.get("ANTHROPIC_API_KEY") or prompter.text(t("ai.paste_key"), hidden=True)
        if not key:
            raise SetupIncomplete(t("ai.key_needed"))
        os.environ["ANTHROPIC_API_KEY"] = key
        prompter.say(t("ai.key_tip"))
        return AnthropicProvider(key)
    return setup_local(prompter, model)


def move_to_chat(prompter, prompt="/cv-start"):
    """With VS Code installed, offer to go on in the Claude Code chat: opens it with `prompt` (the extension's vscode:// link)."""
    code = shutil.which("code")
    if not code or not prompter.confirm(t("ai.open_chat"), default=True):
        return False
    uri = "vscode://anthropic.claude-code/open?" + urllib.parse.urlencode({"prompt": prompt})
    return subprocess.run([code, "--open-url", uri], capture_output=True).returncode == 0


def ensure_provider(prompter, attempts=3):
    """Always show the three choices with their state; if one is not ready, explain and let the user choose again."""
    status = {"cli": t("common.found") if claude_cli.installed() else t("common.not_found"),
              "api": t("ai.key_present") if os.environ.get("ANTHROPIC_API_KEY") else t("ai.key_missing"),
              "local": t("ai.local_up") if ollama.is_up() else t("ai.local_todo")}
    prompter.say(t("ai.claude_code_tip"))
    for _ in range(attempts):
        choice = prompter.select(t("ai.question"), [(c, f"{t('ai.choice_' + c)} [{status[c]}]") for c in CHOICES])
        try:
            provider = make_provider(prompter, choice)
            return provider, choice, getattr(provider, "model", "")
        except SetupIncomplete as err:
            prompter.say(str(err))
    raise SetupIncomplete(t("ai.none_ready"))
