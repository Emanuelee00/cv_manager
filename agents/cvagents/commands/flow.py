"""Flow commands: start (guided), cv and run (with saved choices)."""
from cvagents import settings
from cvagents.i18n import t
from cvagents.live import LiveBoard
from cvagents.live_wrappers import TrackedPrompter, TrackedProvider
from cvagents.onboarding import Aborted, QuestionaryPrompter, SetupIncomplete, ensure_provider, make_provider, run_start
from cvagents.pipeline import run_cv


def tracked(title):
    """A prompter with the live view, and a function that hooks the same panel to a provider."""
    board = LiveBoard(title)
    return TrackedPrompter(QuestionaryPrompter(), board), lambda provider: TrackedProvider(provider, board)


def start_cmd(args, conn):
    try:
        prompter, track = tracked("CV Base")
        provider, chosen, summary = run_start(prompter, conn, provider_wrapper=track)
        if provider and chosen["offer"] and prompter.confirm(t("start.run_now")):
            run_cv(prompter, conn, provider, open(chosen["offer"], encoding="utf8").read(), chosen["lang"] or None, chosen["out"],
                   chosen["formats"], chosen["style"])
        return summary
    except Aborted:
        return t("common.interrupted_saved")


def cv_cmd(args, conn):
    try:
        prompter, track = tracked("CV")
        provider = track(ensure_provider(prompter)[0])
        files, _ = run_cv(prompter, conn, provider, open(args.offer, encoding="utf8").read(), args.lang, args.out, args.format, args.style)
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
        files, _ = run_cv(prompter, conn, provider, open(offer, encoding="utf8").read(), chosen["lang"] or None, chosen["out"],
                          chosen["formats"], chosen["style"])
        return t("cmd.ready", files=", ".join(map(str, files))) if files else t("cmd.no_files")
    except (SetupIncomplete, Aborted) as err:
        return str(err) or t("common.interrupted")


FORMAT = ("--format", {"nargs": "+", "choices": ["pdf", "docx"], "default": ["pdf"]})
STYLE = ("--style", {"choices": ["classic", "modern", "minimal"], "default": "classic"})
LANG = ("--lang", {"default": None, "choices": ["fr", "it", "en", "es"]})
SPEC = [
    ("start", "Guided path: language, CV or from scratch, AI, your details, GitHub, offer, format and style", [], start_cmd),
    ("cv", "CV for an offer, choosing the AI now", [("offer", {}), LANG, ("--out", {"default": "output"}), FORMAT, STYLE], cv_cmd),
    ("run", "Redo everything with the choices saved by start", [("offer", {"nargs": "?", "default": ""})], run_cmd),
]
