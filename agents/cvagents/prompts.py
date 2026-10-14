"""Agent prompts (.claude/agents/*.md) reused by the command line, without duplicating them."""
import re
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "agents"
NO_TOOLS = ("NO-TOOLS MODE: you cannot run commands, read files or search the web. You work ONLY on the DATABASE EXCERPTS "
            "given in the user message. Where the instructions below mention `cvagents search` or `show`, use those excerpts. "
            "Questions for the candidate go in the dedicated field of your answer.\n\n")


def split_sections(body):
    """Split the body into (heading, text) at each `## `; text before the first heading gets an empty heading."""
    parts = re.split(r"^## ", body, flags=re.M)
    return [("", parts[0])] + [(p.split("\n", 1)[0], p.split("\n", 1)[1] if "\n" in p else "") for p in parts[1:]]


def load_agent_prompt(name, sections=None):
    """Agent body without frontmatter. `sections`: heading prefixes to keep (for small models)."""
    raw = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf8")
    body = raw.split("---", 2)[2].strip()
    if sections:
        kept = [f"## {t}\n{x}" for t, x in split_sections(body) if t.startswith(tuple(sections))]
        body = "\n".join(kept)
    return NO_TOOLS + body
