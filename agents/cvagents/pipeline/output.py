"""Write the CV files: PDF in the chosen style fitted to one page, Word if asked; then the ATS check and score."""
from pathlib import Path

from cvagents import ats, ats_score
from cvagents.cv_layout import parse_profile
from cvagents.layouts import STYLES, reading_order
from cvagents.pipeline.cv_html import fit_one_page
from cvagents.word import build_docx


def write_files(candidate, cv, lang, folder, formats, style="classic"):
    """Return a dict: files, pages, dropped (entries removed to fit one page), problems (message key, values), score (ATS %)."""
    folder, cv = Path(folder), ats.safe_cv(cv)
    _, pdf_path, cv, dropped, pages = fit_one_page(candidate, cv, lang, folder, style)
    profile = parse_profile(candidate)
    problems = ats.text_problems(ats.pdf_text(pdf_path), cv, lang, profile["name"], profile["email"], reading_order(style, cv))
    files = [pdf_path] if "pdf" in formats else []
    if "docx" in formats:
        files.append(build_docx(candidate, cv, lang, folder / "cv.docx"))
        problems += ats.docx_problems(files[-1])
    return {"files": files, "pages": pages, "dropped": dropped, "problems": problems, "score": ats_score.score(problems, STYLES[style])}
