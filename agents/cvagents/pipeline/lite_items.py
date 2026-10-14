"""Lite mode: code builds the CV entries from the database (section, title, dates, text)."""
import json
import re

from cvagents.pipeline.text_tools import SKIP_PREFIXES, clean_title, cut_sentence, repo_text

KIND_SECTION = {"experience": "experience", "project": "project", "hackathon": "project", "achievement": "project",
                "repo": "project", "education": "education", "skill": "skill", "language": "language",
                "certification": "certification", "interest": "interest"}
CAPS = {"project": 5, "experience": 4, "education": 4, "skill": 3, "language": 1, "certification": 3, "interest": 3}
def row_to_item(row):
    """A CV entry from a database row; the text comes from the descriptive lines, never from the AI."""
    meta = json.loads(row["meta"])
    org, period = meta.get("org", ""), meta.get("period", "")
    lines = [l.strip() for l in row["body"].split("\n") if l.strip() and l.strip() not in (org, period)]
    text = " ".join(l for l in lines if not l.startswith(SKIP_PREFIXES))
    title = clean_title(row["title"])
    section = KIND_SECTION.get(row["kind"], "project")
    if row["source"] == "github":
        text = repo_text(row["body"])
    if section in ("interest", "certification") or (row["source"] == "manual" and section == "skill"):
        text = title
    return {"section": section, "title": title + (f", {org}" if org and section != "language" else ""),
            "period": period, "text": cut_sentence(text) or title, "source_id": row["id"]}


def already_told(item, items):
    """An entry whose name is already told in another entry of the same section (e.g. an exchange inside a degree)."""
    key = item["title"].split(" — ")[0].split(",")[0].strip().lower()
    return len(key) > 4 and any(key in other["text"].lower() for other in items if other["section"] == item["section"])


def recency(item):
    """Sort key, most recent first: highest year in the period; "ongoing", "expected", "today" count as the future."""
    period = item.get("period", "").lower()
    years = [int(y) for y in re.findall(r"(?:19|20)\d\d", period)]
    ongoing = any(w in period for w in ("corso", "cours", "previst", "prévu", "oggi", "present", "aujourd", "ongoing", "expected", "actual", "curso"))
    return (9000 if ongoing else 0) + (max(years) if years else 0)


def build_items(rows):
    """Entries by relevance, with a cap per section, without duplicates. Repos without useful text are skipped."""
    items, count = [], {}
    for row in rows:
        item = row_to_item(row)
        usable = (row["source"] != "github" or item["text"] != item["title"]) and not already_told(item, items)
        if row["kind"] in KIND_SECTION and usable and count.get(item["section"], 0) < CAPS[item["section"]]:
            count[item["section"]] = count.get(item["section"], 0) + 1
            items.append(item)
    dated = sorted((i for i in items if i["section"] in ("education", "experience")), key=recency, reverse=True)
    return dated + [i for i in items if i["section"] not in ("education", "experience")]
