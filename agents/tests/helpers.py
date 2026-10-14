"""Finti prompter e provider per i test."""
from cvagents.llm.base import Provider


class ScriptedPrompter:
    """Risponde da una lista; per select/confirm/checkbox usa i valori scelti dal test."""

    def __init__(self, texts=(), selects=(), confirms=(), checks=None):
        self.texts, self.selects, self.confirms, self.checks = list(texts), list(selects), list(confirms), checks
        self.said, self.asked = [], []

    def say(self, message=""):
        self.said.append(message)

    def text(self, message, default=""):
        self.asked.append(message)
        return self.texts.pop(0) if self.texts else default

    def confirm(self, message, default=True):
        self.asked.append(message)
        return self.confirms.pop(0) if self.confirms else default

    def select(self, message, choices):
        self.asked.append(message)
        return self.selects.pop(0) if self.selects else choices[0][0]

    def checkbox(self, message, choices):
        self.asked.append(message)
        return [v for v, _ in choices] if self.checks is None else self.checks


class FakeProvider(Provider):
    name = "Finto"
    local = True

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def chat(self, messages, schema=None, on_token=None):
        self.calls.append((messages, schema))
        return self.replies.pop(0) if self.replies else "{}"
