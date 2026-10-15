"""Humanizer pass on the CV text, accepted only if the facts stay identical."""
import json
import re

from cvagents import checks
from cvagents.i18n import t
from cvagents.llm.base import LLMError
from cvagents.prompts import load_agent_prompt

TEXTS_SCHEMA = {"type": "object", "required": ["texts"], "properties": {"texts": {"type": "array", "items": {"type": "string"}}}}
SECTIONS = ("Absolute rule", "The candidate's tone", "What you look for", "How you rewrite")
MODES = {"A": "Mode A: light touch, a person will read the CV.", "B": "Mode B: deeper rewrite, the CV goes through a portal."}


def texts_of(cv):
    return [cv["profile"]] + [i["text"] for i in cv["items"]]


def facts_preserved(before, after):
    return not checks.compare_facts(" ".join(before), " ".join(after))


def humanize_cv(provider, cv, channel):
    """Return (cv, changed). If facts change or the number of texts differs, the original stays."""
    system = load_agent_prompt("humanizer", sections=SECTIONS) + "\n\n" + MODES[channel] + (
        "\nRewrite each text keeping the order and the language. Answer only with JSON: {\"texts\": [...]} with the same number of texts.")
    before = texts_of(cv)
    raw = provider.chat([{"role": "system", "content": system}, {"role": "user", "content": json.dumps(before, ensure_ascii=False)}], schema=TEXTS_SCHEMA)
    try:
        after = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))["texts"]
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError(t("run.unreadable_humanizer")) from err
    if len(after) != len(before) or not facts_preserved(before, after):
        return cv, False
    return {**cv, "profile": after[0], "items": [{**i, "text": text} for i, text in zip(cv["items"], after[1:])]}, True
