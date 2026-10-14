"""Questions to the user in the terminal (questionary). Tests use a fake prompter with the same methods."""
from contextlib import nullcontext

import questionary


class Aborted(Exception):
    """The user interrupted (Ctrl+C)."""


def answer(question):
    result = question.ask()
    if result is None:
        raise Aborted()
    return result


class QuestionaryPrompter:
    say = staticmethod(print)
    step = staticmethod(nullcontext)

    def text(self, message, default="", hidden=False):
        question = questionary.password(message) if hidden else questionary.text(message, default=default)
        return answer(question).strip()

    def confirm(self, message, default=True):
        return answer(questionary.confirm(message, default=default))

    def select(self, message, choices):
        """choices: [(value, label)]. Returns the chosen value."""
        options = [questionary.Choice(label, value=value) for value, label in choices]
        return answer(questionary.select(message, choices=options))

    def checkbox(self, message, choices):
        """choices: [(value, label)], all pre-selected. Returns the chosen values."""
        options = [questionary.Choice(label, value=value, checked=True) for value, label in choices]
        return answer(questionary.checkbox(message, choices=options))
