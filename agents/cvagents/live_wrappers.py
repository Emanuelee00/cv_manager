"""Connect the live view without touching the rest: a provider that streams text, a prompter that pauses."""


class TrackedProvider:
    """Like the original provider, but each call is counted and the text scrolls in the panel."""

    def __init__(self, inner, board):
        self.inner, self.board = inner, board

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def chat(self, messages, schema=None, on_token=None):
        self.board.stream("", new_call=True)
        return self.inner.chat(messages, schema=schema, on_token=self.board.stream)


class TrackedPrompter:
    """Like the original prompter; before each question it stops the panel, `step` opens a step."""

    def __init__(self, inner, board):
        self.inner, self.board = inner, board
        self.step = board.step

    def __getattr__(self, name):
        method = getattr(self.inner, name)
        if name == "say":
            return method
        return lambda *args, **kwargs: (self.board.pause(), method(*args, **kwargs))[1]

