"""Photo for the CV: a file, or (with none) a shot with the computer's camera made professional, choosing which one to keep."""
import subprocess
import sys
import webbrowser
from pathlib import Path

from cvagents import settings
from cvagents.cv_layout import resolve_photo
from cvagents.i18n import t
from cvagents.photo import capture

PHOTOS = settings.PATH.parent / "photo"


def retouch(raw, dest):
    """Professional version, made in its own process (rembg is slow to load). Returns (path or "", error)."""
    done = subprocess.run([sys.executable, "-m", "cvagents.photo.retouch", str(raw), str(dest)], capture_output=True, text=True)
    return (str(dest), "") if done.returncode == 0 else ("", (done.stderr.strip().splitlines() or ["?"])[-1])


def shoot(prompter, folder):
    """Take the photo, make it professional, show it; the user keeps one of the two, retakes it or goes without."""
    while True:
        raw = capture(folder / "camera.png", lambda url: prompter.say(t("photo.opening", url=url)))
        if not raw:
            prompter.say(t("photo.none_received"))
            return ""
        with prompter.step(t("step.photo")):
            pro, error = retouch(raw, folder / "photo.png")
        if pro:
            webbrowser.open(Path(pro).as_uri())
        prompter.say(t("photo.ready", pro=pro, raw=raw) if pro else t("photo.retouch_failed", error=error, raw=raw))
        keep = [("pro", t("photo.use_pro"))] if pro else []
        choice = prompter.select(t("photo.which"), keep + [("raw", t("photo.use_raw")), ("again", t("photo.retake")), ("none", t("photo.no_photo"))])
        if choice != "again":
            return {"pro": pro, "raw": raw}.get(choice, "")


def ask_photo(prompter, path, folder=PHOTOS):
    """The photo as given; with none, offer to take one with the camera (default: no)."""
    if path or not prompter.confirm(t("photo.camera_question"), default=False):
        return resolve_photo(path)
    return shoot(prompter, folder)
