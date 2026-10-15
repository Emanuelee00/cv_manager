"""From the structured CV to HTML in the chosen style, fitted to one page."""
from pathlib import Path

from cvagents import render
from cvagents.layouts import render_html

DROP_ORDER = ("interest", "certification", "project", "experience")
SCALES = (1.12, 1.08, 1.04, 1.0, 0.96, 0.92)


def fit_one_page(profile_text, cv, lang, folder, style="classic"):
    """Write HTML and PDF in `folder`. The modern style uses the biggest type that fits (tries 12% bigger down to 8% smaller); if even that is too long, (all styles) the
    least important entries are dropped one by one (never the side column of the modern style: it would not free space)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path, dropped = folder / "cv.html", folder / "cv.pdf", []
    order = DROP_ORDER if style != "modern" else ("project", "experience")
    while True:
        for scale in SCALES if style == "modern" else (1.0,):
            html_path.write_text(render_html(style, profile_text, cv, lang, scale), encoding="utf8")
            ok, pages = render.fits_one_page(html_path, pdf_path)
            if ok:
                return html_path, pdf_path, cv, dropped, pages
        victim = next((i for kind in order for i in reversed(cv["items"]) if i["section"] == kind), None)
        if victim is None:
            return html_path, pdf_path, cv, dropped, pages
        dropped.append(victim["title"])
        cv = {**cv, "items": [i for i in cv["items"] if i is not victim]}
