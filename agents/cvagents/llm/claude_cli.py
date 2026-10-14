"""Claude tramite Claude Code installato (`claude -p`), usa il login già fatto dall'utente."""
import glob
import os
import shutil
import subprocess

from cvagents.llm.base import LLMError, Provider


def flatten(messages):
    """`claude -p` prende un solo testo: i messaggi diventano un copione unico."""
    names = {"system": "ISTRUZIONI", "user": "UTENTE", "assistant": "ASSISTENTE"}
    return "\n\n".join(f"[{names[m['role']]}]\n{m['content']}" for m in messages)


def find_claude(command="claude"):
    """`claude` nel PATH, oppure il programma incluso nell'estensione VS Code di Claude Code."""
    found = shutil.which(command)
    if found:
        return found
    pattern = os.path.expanduser("~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude")
    candidates = sorted(glob.glob(pattern))
    return candidates[-1] if candidates else None


class ClaudeCliProvider(Provider):
    name = "Claude Code (claude -p)"
    local = False

    def __init__(self, command=None):
        self.command = command or find_claude() or "claude"

    def chat(self, messages, schema=None, on_token=None):
        prompt = flatten(messages)
        if schema:
            prompt += "\n\nRispondi SOLO con JSON valido che rispetta questo schema:\n" + str(schema)
        done = subprocess.run([self.command, "-p"], input=prompt, capture_output=True, text=True)
        if done.returncode != 0:
            raise LLMError(f"claude -p ha fallito: {done.stderr.strip()[:300]}")
        if on_token:
            on_token(done.stdout)
        return done.stdout


def installed(command="claude"):
    return find_claude(command) is not None
