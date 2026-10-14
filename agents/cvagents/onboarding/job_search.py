"""The offer step: a text file, or a LinkedIn search (what, where, how many days) for who does not know what to look for."""
from cvagents import linkedin, settings
from cvagents.i18n import t

OFFERS = settings.PATH.parent / "offers"


def save_offer(job_id, text, folder):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"linkedin-{job_id}.txt"
    path.write_text(text, encoding="utf8")
    return str(path)


def pick_job(prompter, jobs):
    """The id of the chosen offer, or "" for none of these."""
    choices = [(j["id"], " · ".join(x for x in (j["title"], j.get("company"), j.get("location"), j.get("date")) if x)) for j in jobs]
    choice = prompter.select(t("jobs.pick"), choices + [("none", t("jobs.none"))])
    return "" if choice == "none" else choice


def search_linkedin(prompter, profile, folder=OFFERS):
    """Ask what, where and how many days; show the offers; save the chosen one. Returns its path, or "" if none."""
    query = prompter.text(t("jobs.what"), profile.get("headline", ""))
    where = prompter.text(t("jobs.where"), profile.get("city", ""))
    days = prompter.text(t("jobs.days"), "3")
    try:
        with prompter.step(t("step.jobs")):
            jobs = linkedin.search(query, where, int(days) if days.isdigit() and int(days) > 0 else 3)
        if not jobs:
            prompter.say(t("jobs.no_results"))
            return ""
        job_id = pick_job(prompter, jobs)
        if not job_id:
            return ""
        with prompter.step(t("step.job_detail")):
            return save_offer(job_id, linkedin.offer_text(job_id), folder)
    except linkedin.LinkedInError as err:
        prompter.say(t("jobs.failed", error=err))
        return ""


def ask_offer(prompter, profile, current="", folder=OFFERS):
    """Path of the offer: from LinkedIn if the user wants to search there, otherwise (or if nothing was chosen) a file."""
    how = prompter.select(t("jobs.question"), [("file", t("jobs.option_file")), ("linkedin", t("jobs.option_linkedin"))])
    path = search_linkedin(prompter, profile, folder) if how == "linkedin" else ""
    if path:
        prompter.say(t("jobs.saved", path=path))
    return path or prompter.text(t("start.offer_file"), current)
