"""Collegano la vista dal vivo al resto senza toccarlo: un provider che trasmette il testo, un prompter che mette in pausa."""


class TrackedProvider:
    """Come il provider originale, ma ogni chiamata conta e il testo scorre nel pannello."""

    def __init__(self, inner, board):
        self.inner, self.board = inner, board

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def chat(self, messages, schema=None, on_token=None):
        self.board.stream("", new_call=True)
        return self.inner.chat(messages, schema=schema, on_token=self.board.stream)


class TrackedPrompter:
    """Come il prompter originale; prima di ogni domanda ferma il pannello, `step` apre un passo."""

    def __init__(self, inner, board):
        self.inner, self.board = inner, board
        self.step = board.step

    def __getattr__(self, name):
        method = getattr(self.inner, name)
        if name == "say":
            return method
        return lambda *args, **kwargs: (self.board.pause(), method(*args, **kwargs))[1]

