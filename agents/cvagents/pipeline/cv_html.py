"""From the structured CV to HTML in the chosen style, fitted to one page."""
from pathlib import Path

from cvagents import render
from cvagents.layouts import render_html

DROP_ORDER = ("interest", "certification", "project", "experience")


def fit_one_page(profile_text, cv, lang, folder, style="classic"):
    """Write HTML and PDF in `folder`; if the PDF is longer than one page, drop the least important entries one by one."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path, dropped = folder / "cv.html", folder / "cv.pdf", []
    while True:
        html_path.write_text(render_html(style, profile_text, cv, lang), encoding="utf8")
        ok, pages = render.fits_one_page(html_path, pdf_path)
        victim = next((i for kind in DROP_ORDER for i in reversed(cv["items"]) if i["section"] == kind), None)
        if ok or victim is None:
            return html_path, pdf_path, cv, dropped, pages
        dropped.append(victim["title"])
        cv = {**cv, "items": [i for i in cv["items"] if i is not victim]}
