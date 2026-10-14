"""The profile questions."""
from cvagents.cv_layout import resolve_photo
from cvagents.i18n import t
from cvagents.onboarding.profile import FIELDS, OPTIONAL


def ask_profile(prompter, existing=None):
    """Ask the basic and the optional details. `existing` pre-fills the answers."""
    existing = existing or {}
    data = {key: prompter.text(t(f"profile.{key}") + ":", existing.get(key, "")) for key in FIELDS}
    while not data["name"]:
        data["name"] = prompter.text(t("profile.name_required"))
    prompter.say("\n" + t("profile.optional_intro"))
    data.update({key: prompter.text(t(f"profile.{key}") + ":", existing.get(key, "")) for key in OPTIONAL})
    data["photo"] = resolve_photo(data["photo"])
    return data
