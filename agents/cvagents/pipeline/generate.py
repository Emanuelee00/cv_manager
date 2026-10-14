"""Write the CV as structured data and check it with code."""
import json
import re

from cvagents import checks
from cvagents.i18n import t
from cvagents.llm.base import LLMError

SECTIONS = ["education", "experience", "project", "skill", "language", "certification", "interest"]
STRING = {"type": "string"}
CV_SCHEMA = {"type": "object", "required": ["profile", "items"], "properties": {
    "headline": STRING, "profile": STRING, "questions": {"type": "array", "items": STRING},
    "items": {"type": "array", "items": {"type": "object", "required": ["section", "title", "text", "source_id"], "properties": {
        "section": {"type": "string", "enum": SECTIONS}, "title": STRING, "period": STRING, "text": STRING, "source_id": STRING}}}}}
FORMAT = ("Answer only with JSON. 'profile': 3-4 sentences. 'headline': a title aimed at the offer. Every element of 'items' has "
          "'source_id' = the id in square brackets of the EXCERPT it comes from. Do not use numbers or facts that are not in the "
          "EXCERPTS or in the CANDIDATE data. Doubts or missing data: write them in 'questions'.")


def parse_cv(raw):
    match = re.search(r"\{.*\}", raw, re.S)
    try:
        cv = json.loads(match.group(0))
        items = [i for i in cv["items"] if isinstance(i, dict) and i.get("section") in SECTIONS and i.get("title")]
        return {"headline": cv.get("headline", ""), "profile": cv["profile"], "items": items, "questions": cv.get("questions") or []}
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError(t("cv.unreadable_cv")) from err


def generate(provider, system, offer, context, candidate, lang, answers=""):
    user = (f"OFFER:\n{offer[:5000]}\n\nCANDIDATE:\n{candidate}\n\nDATABASE EXCERPTS:\n{context}\n\n"
            f"CANDIDATE ANSWERS:\n{answers or 'none'}\n\nWrite the CV in this language: {lang}.")
    raw = provider.chat([{"role": "system", "content": system + "\n\n" + FORMAT}, {"role": "user", "content": user}], schema=CV_SCHEMA)
    return parse_cv(raw)


def find_problems(cv, rows, candidate):
    """Problems code can verify: invented ids, numbers without a source, repeated words."""
    texts = [cv["profile"]] + [f"{i['title']} {i.get('period', '')} {i['text']}" for i in cv["items"]]
    sources = [r["body"] + " " + r["title"] for r in rows] + [candidate]
    found = []
    unknown = checks.unknown_sources([i["source_id"] for i in cv["items"]], [r["id"] for r in rows])
    if unknown:
        found.append(f"Ids not in the excerpts: {', '.join(unknown)}. Use only the ids of the EXCERPTS.")
    invented = checks.unsupported_numbers(" ".join(texts), sources)
    if invented:
        found.append(f"Numbers with no source in the excerpts: {', '.join(invented)}. Remove them or use only numbers from the excerpts.")
    repeats = checks.repeated_words(" ".join(texts))
    if repeats:
        found.append("Repeated words (use each only once): " + ", ".join(list(repeats)[:8]))
    return found


def repair(provider, system, cv, problems, lang):
    user = f"CV to fix:\n{json.dumps(cv, ensure_ascii=False)}\n\nFix ONLY these problems, change nothing else:\n- " + "\n- ".join(problems)
    raw = provider.chat([{"role": "system", "content": system + "\n\n" + FORMAT}, {"role": "user", "content": user + f"\nLanguage: {lang}."}], schema=CV_SCHEMA)
    return parse_cv(raw)
