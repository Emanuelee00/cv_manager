"""Write the CV files: PDF fitted to one page and, if asked, Word with the same content; then the ATS check."""
from pathlib import Path

from cvagents import ats
from cvagents.cv_layout import parse_profile
from cvagents.pipeline.cv_html import fit_one_page
from cvagents.word import build_docx


def write_files(candidate, cv, lang, folder, formats):
    """Return (created files, PDF pages, entries removed to fit one page, ATS problems as (message key, values))."""
    folder, cv = Path(folder), ats.safe_cv(cv)
    _, pdf_path, cv, dropped, pages = fit_one_page(candidate, cv, lang, folder)
    profile = parse_profile(candidate)
    problems = ats.text_problems(ats.pdf_text(pdf_path), cv, lang, profile["name"], profile["email"])
    files = [pdf_path] if "pdf" in formats else []
    if "docx" in formats:
        files.append(build_docx(candidate, cv, lang, folder / "cv.docx"))
        problems += ats.docx_problems(files[-1])
    return files, pages, dropped, problems
