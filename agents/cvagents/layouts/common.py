"""Pieces shared by every CV layout: escaping, contacts, photo, page shell."""
import html
import re
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


URL = re.compile(r"(?<![\w/@.-])((?:https?://)?(?:[\w-]+\.)+(?:com|io|fr|org|net)/[^\s<]*[\w/])")


def esc(text):
    return html.escape(text or "")


def linkify(text):
    """Escaped text where every web address (with or without https://) becomes a clickable link."""
    return URL.sub(lambda m: f'<a href="{m.group(1) if m.group(1).startswith("http") else "https://" + m.group(1)}">{m.group(1)}</a>', esc(text))


def contacts(p):
    """(kind, label, href) for phone, email and links; the label is what is printed, the href makes it clickable.
    A LinkedIn address ends with an automatic code (-680a2b417): the label hides it, the link keeps it."""
    found = [("phone", p["phone"], "tel:" + re.sub(r"[^+0-9]", "", p["phone"]))] if p["phone"] else []
    found += [("email", p["email"], "mailto:" + p["email"])] if p["email"] else []
    for url in p["links"]:
        kind = "github" if "github.com" in url else "linkedin" if "linkedin.com" in url else "web"
        label = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
        found.append((kind, re.sub(r"-(?=[0-9a-z]*\d)[0-9a-z]{8,10}$", "", label) if kind == "linkedin" else label, url))
    return found


def photo_tag(p):
    path = Path(p["photo"]).expanduser() if p["photo"] else None
    if path and path.is_file():
        return f'<img class="photo" src="{path.resolve().as_uri()}" alt="">'
    print(f"WARNING: no photo in the CV ({path or 'PHOTO not set in manual:candidate-profile'}).", file=sys.stderr)
    return ""


def page(lang, name, css_file, body, scale=1):
    css = (TEMPLATES / css_file).read_text(encoding="utf8")
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>CV {esc(name)}</title>'
            f"<style>{css}:root{{--k:{scale}}}</style></head><body>{body}</body></html>")
