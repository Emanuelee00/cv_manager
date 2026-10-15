"""Modern two-column layout (like a classic French template): sidebar on the left with photo, contact, languages,
skills and interests; main column on the right. In the file the main column comes FIRST, so parsers read name,
profile and experience before the sidebar; CSS places the sidebar on the left."""
from cvagents.cv_layout import INLINE, LABELS, LICENSE
from cvagents.layouts.common import contacts, esc, linkify, page, photo_tag
from cvagents.layouts.icons import icon
from cvagents.layouts.text_parts import language_levels, skill_tags

MAIN = ("experience", "project", "certification")
SIDE = ("education", "skill", "language", "interest")


def name_html(name):
    """'Ada Rossi' -> 'Ada ROSSI', the last word in capitals as in French CVs."""
    words = name.split()
    return esc(" ".join(words[:-1])) + (" " if len(words) > 1 else "") + f"<b>{esc(words[-1].upper())}</b>" if words else ""


def entry_html(item):
    """One entry of the main column: title and period on one line, then the whole text (nothing is cut)."""
    period = f'<span class="when">{esc(item["period"])}</span>' if item.get("period") else ""
    head = f'<div class="what"><span>{esc(item["title"])}</span>{period}</div>' if item["title"] else ""
    text = f'<p class="txt">{linkify(item["text"])}</p>' if item["text"] else ""
    return f'<div class="entry">{head}{text}</div>'


def aside_html(p, cv, lang, labels):
    rows = [(kind, label, href) for kind, label, href in contacts(p)] + ([("city", p["city"], "")] if p["city"] else [])
    contact = "".join(f'<li>{icon(kind)}' + (f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label)) + "</li>" for kind, label, href in rows)
    facts = [x for x in (p["age"], p["citizenship"], f"{LICENSE.get(lang, 'Licence')} {p['license']}" if p["license"] else "") if x]
    languages = "".join(f'<div class="lang"><span>{esc(n)}</span><span class="lv">{esc(lv)}</span>' +
                        (f'<div class="bar"><i style="width:{pc}%"></i></div>' if pc else "") + "</div>"
                        for i in cv["items"] if i["section"] == "language" for n, lv, pc in language_levels(i["text"]))
    skills = "".join(f"<li>{esc(s)}</li>" for s in skill_tags([i["text"] for i in cv["items"] if i["section"] == "skill"], limit=40))
    edu = "".join(f'<div class="edu"><b>{esc(i["title"])}</b>' + (f'<span>{esc(i["period"])}</span>' if i.get("period") else "") +
                  (f'<p>{esc(i["text"])}</p>' if i["text"] else "") + "</div>" for i in cv["items"] if i["section"] == "education")
    interests = "".join(f"<li>{esc(i['text'] or i['title'])}</li>" for i in cv["items"] if i["section"] == "interest")
    blocks = [(labels["contact"], f"<ul class='contact'>{contact}</ul>" + (f"<p class='facts'>{esc(' · '.join(facts))}</p>" if facts else "")),
              (labels["education"], edu), (labels["skill"], f"<ul class='skills'>{skills}</ul>" if skills else ""), (labels["language"], languages),
              (labels["interest"], f"<ul>{interests}</ul>" if interests else "")]
    return "<aside>" + photo_tag(p) + "".join(f"<h3>{title}</h3>{body}" for title, body in blocks if body) + "</aside>"


def reading_order(cv):
    present = {i["section"] for i in cv["items"]}
    return ["profile"] + [k for k in MAIN if k in present] + [k for k in SIDE if k in present]


def render(p, cv, lang, scale=1, css_file="modern.css"):
    labels = LABELS.get(lang, LABELS["en"])
    inline = lambda k: '<p class="txt">' + " · ".join(esc(i["text"] or i["title"]) for i in cv["items"] if i["section"] == k) + "</p>"
    sections = "".join(f"<h2>{labels[k]}</h2>" + (inline(k) if k in INLINE else "".join(entry_html(i) for i in cv["items"] if i["section"] == k))
                       for k in MAIN if any(i["section"] == k for i in cv["items"]))
    main = (f'<main><div class="who"><h1>{name_html(p["name"])}</h1><div class="sub">{esc(cv.get("headline", ""))}</div></div>'
            f'<h2>{labels["profile"]}</h2><p>{esc(cv["profile"])}</p>{sections}</main>')
    return page(lang, p["name"], css_file, f'<div class="sheet"><div class="band"></div>{main}{aside_html(p, cv, lang, labels)}</div>', scale)
