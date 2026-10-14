"""Le domande dell'anagrafica."""
from cvagents.onboarding.profile import FIELDS, OPTIONAL


def ask_profile(prompter, existing=None):
    """Chiede i dati base e quelli facoltativi. `existing` precompila le risposte."""
    existing = existing or {}
    data = {key: prompter.text(label + ":", existing.get(key, "")) for key, label in FIELDS}
    while not data["name"]:
        data["name"] = prompter.text("Il nome è obbligatorio. Nome e cognome:")
    prompter.say("\nOra i dati facoltativi (puoi lasciarli vuoti):")
    data.update({key: prompter.text(label + ":", existing.get(key, "")) for key, label in OPTIONAL})
    return data
