"""Extract the entries of a CV as structured data with the AI (JSON schema), without inventing."""
import json
import re

from cvagents import checks
from cvagents.i18n import t
from cvagents.llm.base import LLMError

TYPES = ["experience", "project", "hackathon", "achievement", "education", "skill", "language"]
STRING = {"type": "string"}
ENTRY_SCHEMA = {"type": "object", "required": ["entries"], "properties": {"entries": {"type": "array", "items": {
    "type": "object", "required": ["type", "title"], "properties": {
        "type": {"type": "string", "enum": TYPES}, "title": STRING, "org": STRING, "period": STRING,
        "description": STRING, "result": STRING, "tags": {"type": "array", "items": STRING}, "link": STRING}}}}}
SYSTEM = ("Extract the entries of a CV text: one per job, project, hackathon, achievement, education, group of skills or "
          "languages. Invent nothing: copy dates, numbers and names exactly as in the text, in the language of the text; "
          "leave empty what is not there. Answer only with JSON following the schema.")


def split_text(text, max_chars=3500):
    """Split the CV into chunks (by paragraph) that a small model can handle."""
    chunks, current = [], ""
    for paragraph in re.split(r"\n\s*\n", text):
        if current and len(current) + len(paragraph) > max_chars:
            chunks.append(current)
            current = ""
        current += paragraph + "\n\n"
    return [c.strip() for c in chunks + [current] if c.strip()]


def parse_entries(raw):
    """Read the JSON even if the model wrote text around it."""
    match = re.search(r"\{.*\}", raw, re.S)
    try:
        items = json.loads(match.group(0))["entries"]
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError(t("cv.unreadable_answer")) from err
    return [e for e in items if isinstance(e, dict) and e.get("title") and e.get("type") in TYPES]


def flag_invented(entry, source_text):
    """Flag in the note the numbers of the entry that are not in the original CV."""
    text = " ".join(str(v) for v in entry.values())
    suspect = checks.unsupported_numbers(text, [source_text])
    return {**entry, "note": f"TO CHECK: numbers not found in the CV: {', '.join(suspect)}"} if suspect else entry


def extract_entries(provider, text, on_chunk=None):
    entries = []
    for i, chunk in enumerate(split_text(text), 1):
        if on_chunk:
            on_chunk(i)
        raw = provider.chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": chunk}], schema=ENTRY_SCHEMA)
        entries += [flag_invented(e, chunk) for e in parse_entries(raw)]
    return entries
