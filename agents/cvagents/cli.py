"""Command line: cvagents <command> (or python -m cvagents <command>)."""
import argparse

from cvagents import settings
from cvagents.commands import HANDLERS, SPEC
from cvagents.db import connect
from cvagents.i18n import set_language


def build_parser():
    parser = argparse.ArgumentParser(prog="cvagents")
    parser.add_argument("--db", default=None, help="path of the SQLite database")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, help_text, arguments, _ in SPEC:
        command = sub.add_parser(name, help=help_text)
        for flag, options in arguments:
            command.add_argument(flag, **options)
    return parser


def main():
    args = build_parser().parse_args()
    set_language(settings.load()["ui_lang"])
    print(HANDLERS[args.cmd](args, connect(args.db) if args.db else connect()))
