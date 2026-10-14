"""`cvagents doctor`: what is there and what is missing to run the AI."""
import os
import sys

from cvagents import linkedin, local_setup, sysinfo
from cvagents.i18n import t
from cvagents.llm import available, claude_cli, ollama


def report(host=ollama.DEFAULT_HOST):
    """Lines for the user: RAM, suggested model, Ollama, Claude, bun for the LinkedIn search."""
    ram = sysinfo.total_ram_gb()
    binary = local_setup.find_ollama()
    up = ollama.is_up(host)
    state = t("doctor.ollama_up") if up else t("doctor.ollama_installed") if binary else t("doctor.ollama_missing")
    lines = [t("doctor.ram", ram=f"{ram:.1f}") if ram else t("doctor.ram_unknown"),
             t("doctor.model", model=local_setup.pick_model(ram)), f"Ollama: {state}"]
    if up:
        lines.append(t("doctor.models", models=", ".join(ollama.list_models(host)) or t("common.none")))
    if not binary:
        lines.append(local_setup.install_hint())
    lines.append(f"Claude Code: {t('common.found') if claude_cli.installed() else t('common.not_found')}")
    lines.append(t("doctor.api_key", state=t("common.present") if os.environ.get("ANTHROPIC_API_KEY") else t("common.absent")))
    lines.append(t("doctor.usable", names=", ".join(label for _, label, _ in available()) or t("common.none")))
    lines.append(f"bun (LinkedIn): {t('common.found') if linkedin.bun() else t('common.not_found')}")
    lines.append(f"Python {sys.version.split()[0]}")
    return lines
