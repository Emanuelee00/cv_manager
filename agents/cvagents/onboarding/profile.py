"""Candidate profile and preferences, in the format the agents read from the database."""
import json

from cvagents.db import get_item, upsert_item

PROFILE_ID, PREFERENCES_ID, PHONES_ID = "manual:candidate-profile", "manual:candidate-preferences", "manual:phones"
FIELDS = ("name", "headline", "city", "email", "phones", "links", "github_login")
OPTIONAL = ("age", "citizenship", "license", "photo")
LABELS = {"age": "AGE", "citizenship": "CITIZENSHIP", "license": "LICENSE", "github_login": "GITHUB LOGIN", "photo": "PHOTO"}


def profile_body(data):
    lines = [f"NAME: {data['name']}", f"HEADLINE: {data['headline']}", f"CITY: {data['city']}"]
    lines += [f"{label}: {data[key]}" for key, label in LABELS.items() if data.get(key)]
    lines += [f"LINKS: {data.get('links', '')} · email {data['email']}", f"PHONES: see {PHONES_ID}"]
    return "\n".join(lines)


def preferences_body(data):
    shown = [key for key in OPTIONAL if data.get(key)]
    return ("Candidate preferences (final decisions, agents apply them without asking again):\n"
            "FORM: one page; order Profile → Education → Experience → Projects → Skills → Languages → Certifications → "
            "Interests; no repeated word.\n"
            f"PERSONAL DATA TO SHOW: {', '.join(shown) or 'only name and contacts'}; never marital status.\n"
            "EXCLUDED PROJECTS: none so far.")


def save_profile(conn, data):
    """Write profile, preferences (keeping exclusions already set) and phones. Returns the name."""
    upsert_item(conn, PROFILE_ID, "manual", "profile", "Candidate profile", profile_body(data))
    old = get_item(conn, PREFERENCES_ID)
    upsert_item(conn, PREFERENCES_ID, "manual", "preferences", "Candidate preferences and decisions",
                old["body"] if old else preferences_body(data), json.loads(old["meta"]) if old else {"excluded_ids": []})
    if data.get("phones"):
        upsert_item(conn, PHONES_ID, "manual", "profile", "Phones and which one to use",
                    f"Phones: {data['phones']}. If the offer is in a country with one of these local numbers, use only that one; otherwise the first.")
    return data["name"]


def set_excluded(conn, item_id, excluded=True):
    """Exclude (or allow again) an entry from the CV, in the candidate preferences. Returns the updated list."""
    old = get_item(conn, PREFERENCES_ID)
    body, meta = (old["body"], json.loads(old["meta"])) if old else ("Candidate preferences.", {})
    ids = set(meta.get("excluded_ids", []))
    ids = ids | {item_id} if excluded else ids - {item_id}
    upsert_item(conn, PREFERENCES_ID, "manual", "preferences", "Candidate preferences and decisions",
                body, {**meta, "excluded_ids": sorted(ids)})
    return sorted(ids)
