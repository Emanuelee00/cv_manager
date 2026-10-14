"""Flow commands: start (guided), cv and run (with saved choices), build (files from a ready CV)."""
import json

from cvagents import settings
from cvagents.i18n import ats_summary, t
from cvagents.live import LiveBoard
from cvagents.live_wrappers import TrackedPrompter, TrackedProvider
from cvagents.onboarding import Aborted, QuestionaryPrompter, SetupIncomplete, ensure_provider, make_provider, run_start
from cvagents.pipeline import candidate_text, run_cv, write_files


def tracked(title):
    """A prompter with the live view, and a function that hooks the same panel to a provider."""
    board = LiveBoard(title)
    return TrackedPrompter(QuestionaryPrompter(), board), lambda provider: TrackedProvider(provider, board)


def start_cmd(args, conn):
    try:
        prompter, track = tracked("CV Base")
        provider, chosen, summary = run_start(prompter, conn, provider_wrapper=track)
        if provider and chosen["offer"] and prompter.confirm(t("start.run_now")):
            run_cv(prompter, conn, provider, open(chosen["offer"], encoding="utf8").read(), chosen["lang"] or None, chosen["out"], chosen["formats"])
        return summary
    except Aborted:
        return t("common.interrupted_saved")


def cv_cmd(args, conn):
    try:
        prompter, track = tracked("CV")
        provider = track(ensure_provider(prompter)[0])
        files, _ = run_cv(prompter, conn, provider, open(args.offer, encoding="utf8").read(), args.lang, args.out, args.format)
        return t("cmd.ready", files=", ".join(map(str, files))) if files else t("cmd.no_files")
    except (SetupIncomplete, Aborted) as err:
        return str(err) or t("common.interrupted")


def run_cmd(args, conn):
    """Redo everything with the choices made in `start`, without asking the first questions again."""
    chosen = settings.load()
    offer = args.offer or chosen["offer"]
    if not chosen["ai"] or not offer:
        return t("cmd.run_needs_start")
    prompter, track = tracked(f"CV · {offer}")
    prompter.say(settings.describe({**chosen, "offer": offer}))
    try:
        provider = track(make_provider(prompter, chosen["ai"], chosen["model"] or None))
        files, _ = run_cv(prompter, conn, provider, open(offer, encoding="utf8").read(), chosen["lang"] or None, chosen["out"], chosen["formats"])
        return t("cmd.ready", files=", ".join(map(str, files))) if files else t("cmd.no_files")
    except (SetupIncomplete, Aborted) as err:
        return str(err) or t("common.interrupted")


def build_cmd(args, conn):
    """Create PDF/Word from a CV in JSON (used by /cv-start and /cv-loop in Claude Code, after confirmation)."""
    with open(args.cv_json, encoding="utf8") as f:
        cv = json.load(f)
    files, pages, dropped, problems = write_files(candidate_text(conn), cv, args.lang, args.out, args.format)
    built = t("cmd.built", files=", ".join(map(str, files)), pages=pages) + (t("cmd.dropped", items=", ".join(dropped)) if dropped else "")
    return built + "\n" + ats_summary(problems)


FORMAT = ("--format", {"nargs": "+", "choices": ["pdf", "docx"], "default": ["pdf"]})
LANG = ("--lang", {"default": None, "choices": ["fr", "it", "en", "es"]})
SPEC = [
    ("start", "Guided path: language, AI, your details, CV, GitHub, offer and format", [], start_cmd),
    ("cv", "CV for an offer, choosing the AI now", [("offer", {}), LANG, ("--out", {"default": "output"}), FORMAT], cv_cmd),
    ("run", "Redo everything with the choices saved by start", [("offer", {"nargs": "?", "default": ""})], run_cmd),
    ("build", "Create PDF/Word from a CV in JSON", [("cv_json", {}), ("--lang", {"default": "fr", "choices": ["fr", "it", "en", "es"]}),
                                                   ("--out", {"default": "output"}), FORMAT], build_cmd),
]
