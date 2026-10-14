"""Interfaccia comune dei provider AI: stessi messaggi, stessa risposta."""


class LLMError(RuntimeError):
    """Il provider non risponde o risponde in modo inutilizzabile."""


class Provider:
    """Un provider espone `chat(messages)` e dice se i dati restano sul computer."""

    name = "base"
    local = False

    def chat(self, messages, schema=None, on_token=None):
        """messages: [{'role': 'system'|'user'|'assistant', 'content': str}]. Ritorna il testo."""
        raise NotImplementedError

    def describe(self):
        where = "sul tuo computer" if self.local else "inviati a un servizio esterno"
        return f"{self.name} (dati {where})"
