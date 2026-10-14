"""`cvagents doctor`: cosa c'è e cosa manca per far girare l'AI."""
import os
import sys

from cvagents import local_setup, sysinfo
from cvagents.llm import available, claude_cli, ollama


def report(host=ollama.DEFAULT_HOST):
    """Righe di testo per l'utente: RAM, modello consigliato, Ollama, Claude."""
    ram = sysinfo.total_ram_gb()
    model = local_setup.pick_model(ram)
    binary = local_setup.find_ollama()
    up = ollama.is_up(host)
    lines = [f"RAM: {ram:.1f} GiB" if ram else "RAM: non rilevata", f"Modello locale consigliato: {model}",
             f"Ollama: {'attivo' if up else 'installato, non attivo' if binary else 'non installato'}"]
    if up:
        lines.append("Modelli scaricati: " + (", ".join(ollama.list_models(host)) or "nessuno"))
    if not binary:
        lines.append(local_setup.install_hint())
    lines.append(f"Claude Code: {'trovato' if claude_cli.installed() else 'non trovato'}")
    lines.append(f"Chiave API Claude: {'presente' if os.environ.get('ANTHROPIC_API_KEY') else 'assente'}")
    lines.append("Utilizzabili ora: " + (", ".join(label for _, label, _ in available()) or "nessuno"))
    lines.append(f"Python {sys.version.split()[0]}")
    return lines
