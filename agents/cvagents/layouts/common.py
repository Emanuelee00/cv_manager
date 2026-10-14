"""Pieces shared by every CV layout: escaping, contacts, photo, page shell."""
import html
import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


def esc(text):
    return html.escape(text or "")


def contacts(p):
    """(kind, label, href) for phone, email and links; the label is what is printed, the href makes it clickable."""
    found = [("phone", p["phone"], "tel:" + re.sub(r"[^+0-9]", "", p["phone"]))] if p["phone"] else []
    found += [("email", p["email"], "mailto:" + p["email"])] if p["email"] else []
    for url in p["links"]:
        kind = "github" if "github.com" in url else "linkedin" if "linkedin.com" in url else "web"
        found.append((kind, re.sub(r"^https?://(www\.)?", "", url).rstrip("/"), url))
    return found


def photo_tag(p):
    path = Path(p["photo"]).expanduser() if p["photo"] else None
    return f'<img class="photo" src="{path.resolve().as_uri()}" alt="">' if path and path.is_file() else ""


def page(lang, name, css_file, body):
    css = (TEMPLATES / css_file).read_text(encoding="utf8")
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>CV {esc(name)}</title>'
            f"<style>{css}</style></head><body>{body}</body></html>")
