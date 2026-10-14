"""Domande all'utente nel terminale (questionary). I test usano un finto prompter con gli stessi metodi."""
import questionary


class Aborted(Exception):
    """L'utente ha interrotto (Ctrl+C)."""


def answer(question):
    result = question.ask()
    if result is None:
        raise Aborted()
    return result


class QuestionaryPrompter:
    def say(self, message=""):
        print(message)

    def text(self, message, default=""):
        return answer(questionary.text(message, default=default)).strip()

    def confirm(self, message, default=True):
        return answer(questionary.confirm(message, default=default))

    def select(self, message, choices):
        """choices: [(valore, etichetta)]. Ritorna il valore scelto."""
        options = [questionary.Choice(label, value=value) for value, label in choices]
        return answer(questionary.select(message, choices=options))

    def checkbox(self, message, choices):
        """choices: [(valore, etichetta)], tutte preselezionate. Ritorna i valori scelti."""
        options = [questionary.Choice(label, value=value, checked=True) for value, label in choices]
        return answer(questionary.checkbox(message, choices=options))
