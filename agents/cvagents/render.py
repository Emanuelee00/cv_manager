"""Da HTML a PDF con Chromium e controllo del numero di pagine (con pdfinfo)."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

BROWSERS = ("chromium-browser", "chromium", "google-chrome")


def find_browser():
    for name in BROWSERS:
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError("Nessun Chromium trovato (chromium-browser, chromium, google-chrome)")


def render_pdf(html, pdf):
    """Stampa l'HTML in PDF A4 con un profilo temporaneo, per non toccare quello dell'utente."""
    html = Path(html).resolve()
    with tempfile.TemporaryDirectory() as profile:
        cmd = [find_browser(), "--headless", "--disable-gpu", "--no-sandbox", f"--user-data-dir={profile}",
               "--no-pdf-header-footer", f"--print-to-pdf={Path(pdf).resolve()}", html.as_uri()]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    return Path(pdf)


def page_count(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, re.M).group(1))


def fits_one_page(html, pdf=None):
    """Ritorna (True/False, pagine). Il PDF resta sul disco se ne dai il percorso."""
    target = Path(pdf) if pdf else Path(tempfile.mkdtemp()) / "check.pdf"
    pages = page_count(render_pdf(html, target))
    return pages == 1, pages
