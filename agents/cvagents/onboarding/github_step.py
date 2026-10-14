"""Connect GitHub: with the gh CLI (private repos too), public repos only, or skip."""
import shutil
import subprocess

from cvagents import github, github_public
from cvagents.i18n import t


def gh_ready():
    if not shutil.which("gh"):
        return False
    return subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0


def choose_github(prompter, login=""):
    """Return (mode, user). Mode: gh, public or skip."""
    options = [("gh", t("github.option_gh"))] if gh_ready() else []
    options += [("public", t("github.option_public")), ("skip", t("github.option_skip"))]
    mode = prompter.select(t("github.question"), options)
    user = prompter.text(t("github.user"), login) if mode == "public" else ""
    return mode, user


def sync_github(prompter, conn, mode, user):
    """Read the repos the chosen way. Returns how many were saved."""
    try:
        with prompter.step(t("step.github")):
            if mode == "gh":
                return github.sync_all(conn)
            if mode == "public" and user:
                return github_public.sync_public(conn, user)
    except (OSError, subprocess.CalledProcessError) as err:
        prompter.say(t("github.unreachable", error=err))
    return 0
