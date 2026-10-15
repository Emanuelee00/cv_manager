"""File commands: build (files from a ready CV in JSON) and styles (the same CV in the three styles, with ATS scores)."""
import json
from pathlib import Path

from cvagents.i18n import ats_summary, t
from cvagents.layouts import STYLES
from cvagents.pipeline import candidate_text, write_files
from cvagents.profile import OUTPUT


def load_cv(path):
    with open(path, encoding="utf8") as f:
        return json.load(f)


def build_cmd(args, conn):
    """Create PDF/Word from a CV in JSON (used by /cv-start and /cv-loop in Claude Code, after confirmation)."""
    done = write_files(candidate_text(conn), load_cv(args.cv_json), args.lang, args.out, args.format, args.style)
    built = t("cmd.built", files=", ".join(map(str, done["files"])), pages=done["pages"])
    built += t("cmd.dropped", items=", ".join(done["dropped"])) if done["dropped"] else ""
    return built + "\n" + t("ats.score", score=done["score"], style=t(f"style.{args.style}")) + "\n" + ats_summary(done["problems"])


def styles_cmd(args, conn):
    """Render the CV in every style and rank them by ATS score (this program's estimate)."""
    cv, candidate, rows = load_cv(args.cv_json), candidate_text(conn), []
    for style in STYLES:
        done = write_files(candidate, cv, args.lang, Path(args.out) / f"style-{style}", ["pdf"], style)
        rows.append((done["score"], style, done["files"][0], done["pages"]))
    rows.sort(key=lambda row: -row[0])
    lines = [t("styles.line", style=t(f"style.{s}"), score=score, file=f, pages=p) for score, s, f, p in rows]
    return "\n".join([t("styles.title")] + lines + [t("styles.best", style=t(f"style.{rows[0][1]}")),
                                                    t("styles.worst", style=t(f"style.{rows[-1][1]}")), t("ats.estimate_note")])


FORMAT = ("--format", {"nargs": "+", "choices": ["pdf", "docx"], "default": ["pdf"]})
STYLE = ("--style", {"choices": list(STYLES), "default": "classic"})
LANG = ("--lang", {"default": "fr", "choices": ["fr", "it", "en", "es"]})
SPEC = [
    ("build", "Create PDF/Word from a CV in JSON", [("cv_json", {}), LANG, ("--out", {"default": OUTPUT}), FORMAT, STYLE], build_cmd),
    ("styles", "The same CV in the three styles, ranked by ATS score", [("cv_json", {}), LANG, ("--out", {"default": OUTPUT})], styles_cmd),
]
