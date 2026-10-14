"""Modern two-column layout (like a classic French template): sidebar on the left with photo, contact, languages,
skills and interests; main column on the right. In the file the main column comes FIRST, so parsers read name,
profile and experience before the sidebar; CSS places the sidebar on the left."""
from cvagents.cv_layout import LABELS, LICENSE
from cvagents.layouts.common import contacts, esc, page, photo_tag
from cvagents.layouts.icons import icon
from cvagents.layouts.text_parts import bullets, language_levels, skill_tags

MAIN = ("education", "experience", "project")
SIDE = ("skill", "language", "certification", "interest")


def name_html(name):
    """'Ada Rossi' -> 'Ada ROSSI', the last word in capitals as in French CVs."""
    words = name.split()
    return esc(" ".join(words[:-1])) + (" " if len(words) > 1 else "") + f"<b>{esc(words[-1].upper())}</b>" if words else ""


def entry_html(item):
    points = "".join(f"<li>{esc(b)}</li>" for b in bullets(item["text"]))
    period = f'<div class="when">{esc(item["period"])}</div>' if item.get("period") else ""
    return f'<div class="entry"><div class="what">{esc(item["title"])}</div>{period}<ul>{points}</ul></div>'


def aside_html(p, cv, lang, labels):
    rows = [(kind, label, href) for kind, label, href in contacts(p)] + ([("city", p["city"], "")] if p["city"] else [])
    contact = "".join(f'<li>{icon(kind)}' + (f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label)) + "</li>" for kind, label, href in rows)
    facts = [x for x in (p["age"], p["citizenship"], f"{LICENSE.get(lang, 'Licence')} {p['license']}" if p["license"] else "") if x]
    languages = "".join(f'<div class="lang"><span>{esc(n)}</span><span class="lv">{esc(lv)}</span>' +
                        (f'<div class="bar"><i style="width:{pc}%"></i></div>' if pc else "") + "</div>"
                        for i in cv["items"] if i["section"] == "language" for n, lv, pc in language_levels(i["text"]))
    skills = "".join(f"<li>{esc(s)}</li>" for s in skill_tags([i["text"] for i in cv["items"] if i["section"] == "skill"]))
    plain = {kind: "".join(f"<li>{esc(i['text'] or i['title'])}</li>" for i in cv["items"] if i["section"] == kind)
             for kind in ("certification", "interest")}
    blocks = [(labels["contact"], f"<ul class='contact'>{contact}</ul>" + (f"<p class='facts'>{esc(' · '.join(facts))}</p>" if facts else "")),
              (labels["skill"], f"<ul class='skills'>{skills}</ul>" if skills else ""), (labels["language"], languages),
              (labels["certification"], f"<ul>{plain['certification']}</ul>" if plain["certification"] else ""),
              (labels["interest"], f"<ul>{plain['interest']}</ul>" if plain["interest"] else "")]
    return "<aside>" + photo_tag(p) + "".join(f"<h3>{title}</h3>{body}" for title, body in blocks if body) + "</aside>"


def reading_order(cv):
    present = {i["section"] for i in cv["items"]}
    return ["profile"] + [k for k in MAIN if k in present] + [k for k in SIDE if k in present]


def render(p, cv, lang, css_file="modern.css"):
    labels = LABELS.get(lang, LABELS["en"])
    sections = "".join(f"<h2>{labels[k]}</h2>" + "".join(entry_html(i) for i in cv["items"] if i["section"] == k)
                       for k in MAIN if any(i["section"] == k for i in cv["items"]))
    main = (f'<main><div class="who"><h1>{name_html(p["name"])}</h1><div class="sub">{esc(cv.get("headline", ""))}</div></div>'
            f'<h2>{labels["profile"]}</h2><p>{esc(cv["profile"])}</p>{sections}</main>')
    return page(lang, p["name"], css_file, f'<div class="sheet"><div class="band"></div>{main}{aside_html(p, cv, lang, labels)}</div>')
