"""From reviews to improvements: merge the opinions and rewrite only what the user accepts."""
import json

from cvagents.pipeline.generate import CV_SCHEMA, FORMAT, parse_cv
from cvagents.pipeline.review import REVIEW_SCHEMA, parse_review


def merge_reviews(provider, reviews):
    """Summarise the recruiter and manager opinions into score, problems and short actions."""
    ask = ("Merge the two reviews into one: 'score' (the average, an integer), 'problems' (max 5) and 'fixes' (max 5 short, "
           "concrete actions). Add nothing that is not in the reviews. Write in the language of the reviews. JSON only.")
    raw = provider.chat([{"role": "system", "content": ask},
                         {"role": "user", "content": f"RECRUITER:\n{reviews['hr'][:6000]}\n\nMANAGER:\n{reviews['manager'][:6000]}"}],
                        schema=REVIEW_SCHEMA)
    return parse_review(raw)


def apply_fixes(provider, system, cv, fixes, lang):
    user = (f"Current CV:\n{json.dumps(cv, ensure_ascii=False)}\n\nApply ONLY these actions, change nothing else and invent "
            "no facts:\n- " + "\n- ".join(fixes) + f"\nLanguage: {lang}.")
    raw = provider.chat([{"role": "system", "content": system + "\n\n" + FORMAT}, {"role": "user", "content": user}], schema=CV_SCHEMA)
    return parse_cv(raw)
