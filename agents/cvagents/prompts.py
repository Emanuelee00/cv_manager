"""I prompt degli agenti (.claude/agents/*.md) riusati dalla riga di comando, senza duplicarli."""
import re
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "agents"
NO_TOOLS = ("MODALITÀ SENZA STRUMENTI: non puoi eseguire comandi, leggere file né cercare in internet. Lavori SOLO sugli "
            "ESTRATTI DEL DATABASE forniti nel messaggio dell'utente. Dove le istruzioni qui sotto parlano di `cvagents "
            "search` o `show`, usa quegli estratti. Le domande per il candidato vanno nell'apposito campo della risposta.\n\n")


def split_sections(body):
    """Divide il corpo in (titolo, testo) per ogni `## `; il testo prima del primo titolo ha titolo vuoto."""
    parts = re.split(r"^## ", body, flags=re.M)
    return [("", parts[0])] + [(p.split("\n", 1)[0], p.split("\n", 1)[1] if "\n" in p else "") for p in parts[1:]]


def load_agent_prompt(name, sections=None):
    """Corpo dell'agente senza frontmatter. `sections`: prefissi dei titoli da tenere (per modelli piccoli)."""
    raw = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf8")
    body = raw.split("---", 2)[2].strip()
    if sections:
        kept = [f"## {t}\n{x}" for t, x in split_sections(body) if t.startswith(tuple(sections))]
        body = "\n".join(kept)
    return NO_TOOLS + body
