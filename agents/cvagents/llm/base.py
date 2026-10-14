"""Common interface of the AI providers: same messages in, same text out."""
from cvagents.i18n import t



class LLMError(RuntimeError):
    """The provider does not answer, or answers with something unusable."""


class Provider:
    """A provider exposes `chat(messages)` and says whether data stays on the computer."""

    name = "base"
    local = False

    def chat(self, messages, schema=None, on_token=None):
        """messages: [{'role': 'system'|'user'|'assistant', 'content': str}]. Returns the text."""
        raise NotImplementedError

    def describe(self):
        return t("llm.describe_local" if self.local else "llm.describe_remote", name=self.name)
