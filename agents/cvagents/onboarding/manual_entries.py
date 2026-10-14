"""Starting from zero: the user types their entries one by one (job, education, project, skills, languages...)."""
from cvagents.i18n import t

KINDS = ("experience", "education", "project", "skill", "language", "certification", "interest")
WITH_PLACE_AND_DATES = ("experience", "education", "project")


def ask_entry(prompter, kind):
    """One entry of the given kind; organisation and dates only where they make sense."""
    entry = {"type": kind, "title": prompter.text(t(f"manual.title_{kind}"))}
    if kind in WITH_PLACE_AND_DATES:
        entry["org"] = prompter.text(t("manual.org"))
        entry["period"] = prompter.text(t("manual.period"))
    if kind not in ("certification", "interest"):
        entry["description"] = prompter.text(t(f"manual.description_{kind}"))
    return entry


def collect_entries(prompter):
    """Ask entries until the user chooses "done"; each one is shown and confirmed before it is kept."""
    entries = []
    prompter.say(t("manual.intro"))
    while True:
        kind = prompter.select(t("manual.which"), [(k, t(f"manual.kind_{k}")) for k in KINDS] + [("done", t("manual.done"))])
        if kind == "done":
            return entries
        entry = ask_entry(prompter, kind)
        summary = " · ".join(v for k, v in entry.items() if k != "type" and v)
        if entry["title"] and prompter.confirm(t("manual.keep", entry=summary)):
            entries.append(entry)
