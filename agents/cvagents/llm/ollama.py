"""Modello locale tramite Ollama (HTTP su localhost, nessuna chiave)."""
import json
import re
import urllib.error
import urllib.request

from cvagents.llm.base import LLMError, Provider

DEFAULT_HOST = "http://127.0.0.1:11434"


def post_lines(url, payload, timeout=600):
    """POST JSON e restituisce le righe JSON della risposta (anche in streaming)."""
    request = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for line in response:
                if line.strip():
                    yield json.loads(line)
    except (urllib.error.URLError, OSError) as err:
        raise LLMError(f"Ollama non risponde su {url}: {err}") from err


def is_up(host=DEFAULT_HOST):
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=2):
            return True
    except (urllib.error.URLError, OSError):
        return False


def list_models(host=DEFAULT_HOST):
    with urllib.request.urlopen(f"{host}/api/tags", timeout=5) as response:
        return [m["name"] for m in json.load(response).get("models", [])]


class OllamaProvider(Provider):
    name = "Ollama (modello locale)"
    local = True

    def __init__(self, model, host=DEFAULT_HOST, temperature=0.2):
        self.model, self.host, self.temperature = model, host, temperature

    def chat(self, messages, schema=None, on_token=None):
        payload = {"model": self.model, "messages": messages, "stream": True, "think": False, "keep_alive": "30m",
                   "options": {"temperature": self.temperature}}
        if schema:
            payload["format"] = schema
        parts = []
        for chunk in post_lines(f"{self.host}/api/chat", payload):
            token = chunk.get("message", {}).get("content", "")
            parts.append(token)
            if token and on_token:
                on_token(token)
        return re.sub(r"<think>.*?</think>", "", "".join(parts), flags=re.S).strip()
