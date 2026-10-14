"""Turn CV texts into the small pieces the modern layout shows: bullets, skill tags, language levels."""
import re

LEVELS = (("native", 100), ("maternelle", 100), ("madrelingua", 100), ("materna", 100), ("nativo", 100), ("bilingu", 100),
          ("c2", 95), ("c1", 85), ("b2", 70), ("b1", 55), ("a2", 35), ("a1", 20),
          ("notion", 20), ("nozion", 20), ("basic", 20), ("básico", 20), ("base", 20))


def bullets(text, limit=4):
    """Sentences of a description as bullet points (at most `limit`)."""
    parts = [s.strip(" .;") for s in re.split(r"(?<=[.;])\s+(?=[A-ZÀ-ÖØ-Ý0-9])", text) if s.strip(" .;")]
    return parts[:limit] or [text]


def skill_tags(texts, limit=14):
    """Single skills from comma/dot separated lists, without duplicates."""
    found = []
    for text in texts:
        for part in re.split(r"[,·;]|\.\s", text):
            part = part.strip(" .")
            if part and len(part) < 40 and part.lower() not in [f.lower() for f in found]:
                found.append(part)
    return found[:limit]


def language_levels(text):
    """[(language, level as written, percent or None)] from 'Italian (native), French (fluent, C2), ...'."""
    found = []
    for chunk in re.split(r"[,·;](?![^()]*\))", text):
        match = re.match(r"\s*([^()]+?)\s*\(([^)]*)\)", chunk)
        if not match:
            continue
        name, level = match.group(1).strip(" ."), match.group(2).strip()
        low = level.lower()
        percent = next((value for word, value in LEVELS if word in low), None)
        cefr = re.findall(r"[ABC][12](?:/[ABC][12])?", level)
        found.append((name[:1].upper() + name[1:], cefr[-1] if cefr else level, percent))
    return found
