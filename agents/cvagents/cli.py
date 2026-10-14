"""Riga di comando: cvagents <comando> (oppure python -m cvagents <comando>)."""
import argparse

from cvagents.commands import HANDLERS, SPEC
from cvagents.db import connect


def build_parser():
    parser = argparse.ArgumentParser(prog="cvagents")
    parser.add_argument("--db", default=None, help="percorso del database SQLite")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, help_text, arguments, _ in SPEC:
        command = sub.add_parser(name, help=help_text)
        for flag, options in arguments:
            command.add_argument(flag, **options)
    return parser


def main():
    args = build_parser().parse_args()
    print(HANDLERS[args.cmd](args, connect(args.db) if args.db else connect()))
