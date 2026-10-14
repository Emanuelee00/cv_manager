"""Read the text of a CV from .txt/.md, .pdf (with pdftotext) or .docx."""
import html
import re
import subprocess
import zipfile
from pathlib import Path

from cvagents.i18n import t


def read_docx(path):
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml").decode("utf8")
    paragraphs = (html.unescape("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p))) for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S))
    return "\n".join(p for p in paragraphs if p.strip())


def read_pdf(path):
    try:
        done = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as err:
        raise ValueError(t("cv.pdf_unreadable")) from err
    return done.stdout


def read_cv_text(path):
    path = Path(path).expanduser()
    readers = {".txt": lambda p: p.read_text(encoding="utf8"), ".md": lambda p: p.read_text(encoding="utf8"),
               ".docx": read_docx, ".pdf": read_pdf}
    if path.suffix.lower() not in readers:
        raise ValueError(t("cv.unsupported", suffix=path.suffix))
    return readers[path.suffix.lower()](path)
