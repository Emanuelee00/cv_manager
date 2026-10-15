"""One folder per person: data/profiles/<name>/ (archive, settings, photo, offers, CVs) and output/<name>/."""
import os
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
PROFILES = DATA / "profiles"


def profile_name():
    """`CVAGENTS_PROFILE`, else the only profile that exists; with several, stop so data never mixes."""
    name = os.environ.get("CVAGENTS_PROFILE", "").strip()
    found = sorted(p.name for p in PROFILES.iterdir() if p.is_dir()) if PROFILES.is_dir() else []
    if name:
        return name
    if len(found) > 1:
        sys.exit(f"Several profiles ({', '.join(found)}): set CVAGENTS_PROFILE=<name> before the command.")
    return found[0] if found else "default"


NAME = profile_name()
DIR = PROFILES / NAME
OUTPUT = f"output/{NAME}"
