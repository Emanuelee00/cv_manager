"""CV review by recruiter and technical hiring manager, in parallel (full mode)."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext

from cvagents.i18n import t
from cvagents.llm.base import LLMError
from cvagents.prompts import load_agent_prompt

STRING = {"type": "string"}
REVIEW_SCHEMA = {"type": "object", "required": ["score", "problems", "fixes"], "properties": {
    "score": {"type": "integer"}, "problems": {"type": "array", "items": STRING}, "fixes": {"type": "array", "items": STRING}}}


def cv_as_text(cv):
    """The CV as plain lines (for the reviewers and the terminal preview); machine translations are marked."""
    lines = [cv.get("headline", ""), cv["profile"] + (f"  ({t('run.reread_profile')})" if cv.get("profile_by_ai") else "")]
    lines += [f"[{i['section']}] {i['title']} {i.get('period', '')}: {i['text']}" + (f"  ({t('run.translated')})" if i.get("translated") else "")
              for i in cv["items"]]
    return "\n".join(lines)


def parse_review(raw):
    try:
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        return {"score": int(data["score"]), "problems": [str(p) for p in data["problems"]], "fixes": [str(f) for f in data["fixes"]]}
    except (AttributeError, ValueError, KeyError, TypeError) as err:
        raise LLMError(t("run.unreadable_review")) from err


def review_full(provider, offer, cv, step=nullcontext):
    """Recruiter and manager with their full prompts, in parallel (each with its own step on screen). Returns both texts."""
    message = f"OFFER:\n{offer[:6000]}\n\nCV:\n{cv_as_text(cv)}"
    labels = {"hr-reviewer": t("step.recruiter"), "manager": t("step.manager")}

    def ask(name):
        with step(labels[name]):
            return provider.chat([{"role": "system", "content": load_agent_prompt(name)}, {"role": "user", "content": message}])

    with ThreadPoolExecutor(max_workers=2) as pool:
        hr, manager = pool.map(ask, ("hr-reviewer", "manager"))
    return {"hr": hr, "manager": manager}
