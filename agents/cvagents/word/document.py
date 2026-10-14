"""Compone il CV strutturato in un documento Word."""
import re
from pathlib import Path

from cvagents.cv_layout import INLINE, LABELS, LICENSE, ORDER, parse_profile
from cvagents.word.layout import header_table, picture, png_size
from cvagents.word.package import write_package
from cvagents.word.parts import GREY, NAVY, TEAL, link, para, run


def add_rel(rels, kind, target):
    """Registra un link o la foto e ne ritorna l'id."""
    rid = f"rId{len(rels) + 1}"
    rels.append((rid, kind, target))
    return rid


def header(p, cv, lang, rels):
    meta = " · ".join(x for x in (p["city"], p["age"], p["citizenship"], f"{LICENSE.get(lang, 'Licence')} {p['license']}" if p["license"] else "") if x)
    pieces = []
    if p["phone"]:
        pieces.append(link(p["phone"], add_rel(rels, "hyperlink", "tel:" + re.sub(r"[^+0-9]", "", p["phone"]))))
    if p["email"]:
        pieces.append(link(p["email"], add_rel(rels, "hyperlink", "mailto:" + p["email"])))
    pieces += [link(re.sub(r"^https?://(www\.)?", "", u), add_rel(rels, "hyperlink", u)) for u in p["links"]]
    contacts = []
    for piece in pieces:
        contacts += ([run(" · ", size=17, color=GREY)] if contacts else []) + [piece]
    left = (para([run(p["name"].upper(), True, 40, NAVY)], 0) + para([run(cv.get("headline", ""), True, 21, TEAL)], 20) +
            para([run(meta, size=17, color=GREY)], 20) + para(contacts, 0))
    photo = Path(p["photo"]).expanduser() if p["photo"] else None
    ok = bool(photo and photo.is_file() and png_size(photo))
    right = para([picture(add_rel(rels, "image", "media/foto.png"))], 0) if ok else ""
    return header_table(left, right), (photo if ok else None)


def item(i):
    top = [run(i["title"], True)] + ([run(i["period"], size=18, color=GREY, tab=True)] if i.get("period") else [])
    return para(top, 0, tabs=True) + para([run(i["text"])], 40)


def section(kind, items, label):
    body = [para([run(label, True, 19, TEAL)], 30, 120, border=True)]
    if kind in INLINE:
        return body[0] + para([run(" · ".join(i["text"] or i["title"] for i in items))], 40)
    return body[0] + "".join(item(i) for i in items)


def build_docx(profile_text, cv, lang, path):
    """Scrive il CV Word in `path`. Ritorna il percorso."""
    rels, labels, p = [], LABELS.get(lang, LABELS["en"]), parse_profile(profile_text)
    head, photo = header(p, cv, lang, rels)
    body = head + para([run(labels["profile"], True, 19, TEAL)], 30, 120, border=True) + para([run(cv["profile"])], 40)
    for kind in ORDER:
        items = [i for i in cv["items"] if i["section"] == kind]
        body += section(kind, items, labels[kind]) if items else ""
    return write_package(path, body, rels, photo)
