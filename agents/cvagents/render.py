"""HTML to PDF with Chromium, and page count with pdfinfo."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from cvagents.i18n import t

BROWSERS = ("chromium-browser", "chromium", "google-chrome")


def find_browser():
    for name in BROWSERS:
        path = shutil.which(name)
        if path:
            return path
    raise FileNotFoundError(t("render.no_browser"))


def render_pdf(html, pdf):
    """Print the HTML to an A4 PDF with a temporary browser profile, so the user's profile is untouched."""
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
    """Return (fits, pages). The PDF stays on disk if you give its path."""
    target = Path(pdf) if pdf else Path(tempfile.mkdtemp()) / "check.pdf"
    pages = page_count(render_pdf(html, target))
    return pages == 1, pages
