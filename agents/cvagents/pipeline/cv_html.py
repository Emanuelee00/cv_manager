"""From the structured CV to HTML (CSS in templates/cv.css), fitted to one page."""
import html
import re
from pathlib import Path

from cvagents import render
from cvagents.cv_layout import INLINE, LABELS, LICENSE, ORDER, parse_profile

CSS = Path(__file__).resolve().parents[2] / "templates" / "cv.css"
DROP_ORDER = ("interest", "certification", "project", "experience")


def header_html(p, cv, lang="fr"):
    esc = html.escape
    meta = " · ".join(esc(x) for x in (p["city"], p["age"], p["citizenship"], f"{LICENSE.get(lang, 'Licence')} {p['license']}" if p["license"] else "") if x)
    contacts = [f'<a href="tel:{re.sub(r"[^+0-9]", "", p["phone"])}">{esc(p["phone"])}</a>' if p["phone"] else "",
                f'<a href="mailto:{esc(p["email"])}">{esc(p["email"])}</a>' if p["email"] else ""]
    contacts += [f'<a href="{esc(u)}">{esc(re.sub(r"^https?://(www\.)?", "", u))}</a>' for u in p["links"]]
    photo = f'<img src="{Path(p["photo"]).expanduser().resolve().as_uri()}" alt="">' if p["photo"] and Path(p["photo"]).expanduser().is_file() else ""
    return (f'<header><div><h1>{esc(p["name"].upper())}</h1><div class="sub">{esc(cv.get("headline", ""))}</div>'
            f'<div class="meta">{meta}</div><div class="meta">{" · ".join(c for c in contacts if c)}</div></div>{photo}</header>')


def section_html(kind, items, label):
    esc = html.escape
    if kind in INLINE:
        body = "<p>" + " · ".join(esc(i["text"] or i["title"]) for i in items) + "</p>"
    else:
        rows = "".join(f'<li><b>{esc(i["title"])}</b>' + (f' <span class="d">{esc(i["period"])}</span>' if i.get("period") else "") +
                       f'<br>{esc(i["text"])}</li>' for i in items)
        body = f"<ul>{rows}</ul>"
    return f"<h2>{label}</h2>{body}"


def build_html(profile_text, cv, lang="fr"):
    labels = LABELS.get(lang, LABELS["en"])
    p = parse_profile(profile_text)
    parts = [header_html(p, cv, lang), f"<h2>{labels['profile']}</h2><p>{html.escape(cv['profile'])}</p>"]
    for kind in ORDER:
        items = [i for i in cv["items"] if i["section"] == kind]
        if items:
            parts.append(section_html(kind, items, labels[kind]))
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>CV {html.escape(p["name"])}</title>'
            f"<style>{CSS.read_text(encoding='utf8')}</style></head><body>{''.join(parts)}</body></html>")


def fit_one_page(profile_text, cv, lang, folder):
    """Write HTML and PDF in `folder`; if the PDF is longer than one page, drop the least important entries one by one."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path, dropped = folder / "cv.html", folder / "cv.pdf", []
    while True:
        html_path.write_text(build_html(profile_text, cv, lang), encoding="utf8")
        ok, pages = render.fits_one_page(html_path, pdf_path)
        victim = next((i for kind in DROP_ORDER for i in reversed(cv["items"]) if i["section"] == kind), None)
        if ok or victim is None:
            return html_path, pdf_path, cv, dropped, pages
        dropped.append(victim["title"])
        cv = {**cv, "items": [i for i in cv["items"] if i is not victim]}
