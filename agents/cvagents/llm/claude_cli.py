"""Claude tramite Claude Code installato (`claude -p`), usa il login già fatto dall'utente."""
import shutil
import subprocess

from cvagents.llm.base import LLMError, Provider


def flatten(messages):
    """`claude -p` prende un solo testo: i messaggi diventano un copione unico."""
    names = {"system": "ISTRUZIONI", "user": "UTENTE", "assistant": "ASSISTENTE"}
    return "\n\n".join(f"[{names[m['role']]}]\n{m['content']}" for m in messages)


class ClaudeCliProvider(Provider):
    name = "Claude Code (claude -p)"
    local = False

    def __init__(self, command="claude"):
        self.command = command

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
    return shutil.which(command) is not None
