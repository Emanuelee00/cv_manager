"""Scrive i file del CV: PDF adattato a una pagina e, se richiesto, Word con lo stesso contenuto."""
from pathlib import Path

from cvagents.pipeline.cv_html import fit_one_page
from cvagents.word import build_docx


def write_files(candidate, cv, lang, folder, formats):
    """Ritorna (file creati, pagine del PDF, voci tolte per stare in una pagina)."""
    folder = Path(folder)
    _, pdf_path, cv, dropped, pages = fit_one_page(candidate, cv, lang, folder)
    files = [pdf_path] if "pdf" in formats else []
    if "docx" in formats:
        files.append(build_docx(candidate, cv, lang, folder / "cv.docx"))
    return files, pages, dropped
