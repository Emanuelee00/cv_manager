"""Lite mode: the review is done by code (offer keywords present or missing in the CV)."""
from cvagents.i18n import t
from cvagents.pipeline import context
from cvagents.pipeline.keywords import coverage, flat, keywords
from cvagents.pipeline.lite_items import row_to_item
from cvagents.search import search


def suggestions(conn, missing, used_ids):
    """For each missing word, the database entry that confirms it and is not in the CV yet."""
    found, skip = [], context.excluded_ids(conn)
    for word in missing:
        for row in search(conn, word, limit=4):
            if row["id"] not in used_ids and row["id"] not in skip and row["kind"] not in context.SKIP_KINDS and word.lower() in flat(row["body"] + row["title"]):
                found.append({"word": word, "row": row})
                break
    return found


def review(conn, provider, offer, cv_text, used_ids):
    """Return (score, problems, proposals). A proposal adds a real database entry."""
    words = keywords(provider, offer)[:12]
    covered, missing = coverage(words, cv_text)
    options = suggestions(conn, missing, used_ids)
    score = max(1, round(10 * len(covered) / len(words))) if words else 5
    in_archive = {s["word"] for s in options}
    problems = [t("review.in_archive" if w in in_archive else "review.not_in_archive", word=w) for w in missing[:6]]
    return score, problems, options


def option_label(option):
    return t("review.add_entry", title=option["row"]["title"], word=option["word"])


def add_option(cv, option):
    return {**cv, "items": cv["items"] + [row_to_item(option["row"])]}
