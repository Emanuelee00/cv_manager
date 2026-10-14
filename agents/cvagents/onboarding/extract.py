"""Estrae le voci di un CV in dati strutturati con l'AI (schema JSON), senza inventare."""
import json
import re

from cvagents import checks
from cvagents.llm.base import LLMError

TYPES = ["experience", "project", "hackathon", "achievement", "education", "skill", "language"]
STRING = {"type": "string"}
ENTRY_SCHEMA = {"type": "object", "required": ["entries"], "properties": {"entries": {"type": "array", "items": {
    "type": "object", "required": ["type", "title"], "properties": {
        "type": {"type": "string", "enum": TYPES}, "title": STRING, "org": STRING, "period": STRING,
        "description": STRING, "result": STRING, "tags": {"type": "array", "items": STRING}, "link": STRING}}}}}
SYSTEM = ("Estrai dal testo di un CV le sue voci: una per esperienza, progetto, hackathon, risultato, formazione, "
          "gruppo di competenze o lingue. Non inventare nulla: copia date, numeri e nomi esattamente come nel testo; "
          "lascia vuoto ciò che non c'è. Rispondi solo con JSON secondo lo schema.")


def split_text(text, max_chars=3500):
    """Spezza il CV in blocchi (per paragrafi) che un modello piccolo regge."""
    chunks, current = [], ""
    for paragraph in re.split(r"\n\s*\n", text):
        if current and len(current) + len(paragraph) > max_chars:
            chunks.append(current)
            current = ""
        current += paragraph + "\n\n"
    return [c.strip() for c in chunks + [current] if c.strip()]


def parse_entries(raw):
    """Legge il JSON anche se il modello ci scrive attorno del testo."""
    match = re.search(r"\{.*\}", raw, re.S)
    try:
        items = json.loads(match.group(0))["entries"]
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError("Risposta non leggibile come elenco di voci") from err
    return [e for e in items if isinstance(e, dict) and e.get("title") and e.get("type") in TYPES]


def flag_invented(entry, source_text):
    """Segna nelle note i numeri della voce che non compaiono nel CV originale."""
    text = " ".join(str(v) for v in entry.values())
    suspect = checks.unsupported_numbers(text, [source_text])
    return {**entry, "note": f"DA VERIFICARE: numeri non trovati nel CV: {', '.join(suspect)}"} if suspect else entry


def extract_entries(provider, text, on_chunk=None):
    entries = []
    for i, chunk in enumerate(split_text(text), 1):
        if on_chunk:
            on_chunk(i)
        raw = provider.chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": chunk}], schema=ENTRY_SCHEMA)
        entries += [flag_invented(e, chunk) for e in parse_entries(raw)]
    return entries
