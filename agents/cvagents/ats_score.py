"""ATS score in percent: this program's own estimate, from weighted criteria the sources agree on (not an official measure)."""

CRITERIA = (("text", 25), ("contacts", 15), ("titles", 20), ("one_column", 15), ("no_bars", 10), ("no_icons", 5),
            ("plain_characters", 5), ("no_tables", 5))


def criteria_met(problems, layout):
    """Which criteria hold, from the problems found in the produced file and the facts of the layout."""
    keys = {key for key, _ in problems}
    return {"text": "ats.no_text" not in keys, "contacts": not keys & {"ats.missing_name", "ats.missing_email", "ats.no_text"},
            "titles": not keys & {"ats.headings", "ats.no_text"}, "one_column": layout["columns"] == 1,
            "no_bars": not layout["bars"], "no_icons": not layout["icons"], "plain_characters": True,
            "no_tables": "ats.word_tables" not in keys}


def score(problems, layout):
    met = criteria_met(problems, layout)
    return sum(weight for name, weight in CRITERIA if met[name])


def best_possible(layout):
    """Score of a style when its file has no problems: what the style itself allows."""
    return score([], layout)
