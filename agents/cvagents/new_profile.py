"""Find or create the folder of a person from the name on the CV: `python -m cvagents.new_profile "First Last"` prints the profile name."""
import os
import sys
import unicodedata
from pathlib import Path

os.environ.setdefault("CVAGENTS_PROFILE", "-")  # only the folder list is needed here, not a chosen profile
from cvagents.profile import PROFILES  # noqa: E402

FILE = "person.txt"


def plain(text):
    """Lowercase, no accents, single spaces."""
    flat = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(flat.lower().split())


def find_or_create(name, root=PROFILES):
    """The profile of this person (the first name, or first_last if another person already has it); a new folder if none matches."""
    root = Path(root)
    key = plain(name)
    first = key.split()[0].replace("-", "_") if key else ""
    for folder in sorted(root.glob("*/")):
        known = plain((folder / FILE).read_text(encoding="utf8")) if (folder / FILE).is_file() else folder.name
        if known == key or (known == folder.name and folder.name == first and len(key.split()) == 1):
            return folder.name
    slug = first if not (root / first).exists() else "_".join(key.split()).replace("-", "_")
    (root / slug).mkdir(parents=True)
    (root / slug / FILE).write_text(name.strip() + "\n", encoding="utf8")
    return slug


if __name__ == "__main__":
    found = find_or_create(" ".join(sys.argv[1:]))
    Path("output", found).mkdir(parents=True, exist_ok=True)
    print(found)
