"""Claude through the Anthropic API (needs ANTHROPIC_API_KEY)."""
import json
import os
import urllib.error
import urllib.request

from cvagents.i18n import t
from cvagents.llm.base import LLMError, Provider

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"


def split_system(messages):
    """The API wants the system text separate from the messages."""
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    return system, [m for m in messages if m["role"] != "system"]


class AnthropicProvider(Provider):
    name = "Claude (API Anthropic)"
    local = False

    def __init__(self, api_key=None, model=DEFAULT_MODEL, url=API_URL, max_tokens=4096):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model, self.url, self.max_tokens = model, url, max_tokens

    def chat(self, messages, schema=None, on_token=None):
        if not self.api_key:
            raise LLMError(t("llm.no_api_key"))
        system, rest = split_system(messages)
        if schema:
            system += "\n\nAnswer ONLY with valid JSON that follows this schema:\n" + json.dumps(schema)
        payload = {"model": self.model, "max_tokens": self.max_tokens, "system": system, "messages": rest}
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        request = urllib.request.Request(self.url, json.dumps(payload).encode(), headers)
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                blocks = json.load(response)["content"]
        except (urllib.error.URLError, OSError, KeyError) as err:
            raise LLMError(t("llm.bad_answer", error=err)) from err
        text = "".join(b.get("text", "") for b in blocks)
        if on_token:
            on_token(text)
        return text
