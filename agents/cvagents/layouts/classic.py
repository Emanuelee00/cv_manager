"""One-column layouts (classic and minimal): the most ATS-friendly; they differ only by their CSS."""
from cvagents.cv_layout import INLINE, LABELS, LICENSE, ORDER
from cvagents.layouts.common import contacts, esc, linkify, page, photo_tag


def header_html(p, cv, lang):
    facts = (p["city"], p["age"], p["citizenship"], f"{LICENSE.get(lang, 'Licence')} {p['license']}" if p["license"] else "")
    links = " · ".join(f'<a href="{esc(href)}">{esc(label)}</a>' for _, label, href in contacts(p))
    return (f'<header><div><h1>{esc(p["name"].upper())}</h1><div class="sub">{esc(cv.get("headline", ""))}</div>'
            f'<div class="meta">{" · ".join(esc(x) for x in facts if x)}</div><div class="meta">{links}</div></div>{photo_tag(p)}</header>')


def section_html(kind, items, label):
    if kind in INLINE:
        body = "<p>" + " · ".join(esc(i["text"] or i["title"]) for i in items) + "</p>"
    else:
        rows = "".join(f'<li><div class="h"><b>{esc(i["title"])}</b>' + (f'<span class="d">{esc(i["period"])}</span>' if i.get("period") else "") +
                       f'</div>{linkify(i["text"])}</li>' if i["title"] else f'<li style="list-style:none;margin:7px 0 5px">{linkify(i["text"])}</li>' for i in items)
        body = f"<ul>{rows}</ul>"
    return f"<h2>{label}</h2>{body}"


def reading_order(cv):
    """Section kinds in the order a parser reads them."""
    return ["profile"] + [k for k in ORDER if any(i["section"] == k for i in cv["items"])]


def render(p, cv, lang, css_file):
    labels = LABELS.get(lang, LABELS["en"])
    parts = [header_html(p, cv, lang), f"<h2>{labels['profile']}</h2><p>{esc(cv['profile'])}</p>"]
    parts += [section_html(kind, [i for i in cv["items"] if i["section"] == kind], labels[kind]) for kind in reading_order(cv)[1:]]
    return page(lang, p["name"], css_file, "".join(parts))
