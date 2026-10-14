"""Collegare GitHub: con la CLI gh (anche repo privati), solo repo pubblici, oppure saltare."""
import shutil
import subprocess

from cvagents import github, github_public


def gh_ready():
    if not shutil.which("gh"):
        return False
    return subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0


def choose_github(prompter, login=""):
    """Ritorna (modo, utente). Modo: gh, public o skip."""
    options = ([("gh", "Sì, con la CLI gh già collegata (anche repo privati)")] if gh_ready() else [])
    options += [("public", "Sì, solo i repo pubblici (basta il nome utente)"), ("skip", "No, per ora salto")]
    mode = prompter.select("Colleghiamo il tuo GitHub? I progetti diventano fonti per il CV.", options)
    user = prompter.text("Nome utente GitHub:", login) if mode == "public" else ""
    return mode, user


def sync_github(prompter, conn, mode, user):
    """Legge i repo secondo il modo scelto. Ritorna quanti ne ha salvati."""
    try:
        if mode == "gh":
            return github.sync_all(conn)
        if mode == "public" and user:
            return github_public.sync_public(conn, user)
    except (OSError, subprocess.CalledProcessError) as err:
        prompter.say(f"GitHub non raggiungibile: {err}")
    return 0
