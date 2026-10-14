"""ATS checks on the produced CV: read it as plain text like an applicant tracking system, and avoid characters that confuse parsers."""
import re
import subprocess
import zipfile

from cvagents.cv_layout import LABELS, ORDER

RISKY = {"→": "->", "←": "<-", "➜": "->", "⇒": "->", "★": "", "☆": "", "✓": "", "✔": "", "✗": "", "•": "-", "▶": "-", "◆": "-", "■": "-"}


def make_safe(text):
    """Replace arrows, stars, check marks and similar symbols with plain characters."""
    for symbol, plain in RISKY.items():
        text = text.replace(symbol, plain)
    return re.sub(r"[\U0001F300-\U0001FAFF]", "", text)


def safe_cv(cv):
    items = [{**i, "title": make_safe(i["title"]), "text": make_safe(i["text"])} for i in cv["items"]]
    return {**cv, "headline": make_safe(cv.get("headline", "")), "profile": make_safe(cv["profile"]), "items": items}


def pdf_text(pdf):
    """Plain text of the PDF, as a parser would extract it (empty if pdftotext is missing)."""
    try:
        return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def text_problems(text, cv, lang, name, email):
    """Message keys (with values) for what an ATS would miss: no text, name, email, section titles (alone on their line) out of order."""
    if not text.strip():
        return [("ats.no_text", {})]
    flat = text.lower()
    problems = [(key, {}) for key, value in (("ats.missing_name", name), ("ats.missing_email", email)) if value and value.lower() not in flat]
    labels = LABELS.get(lang, LABELS["en"])
    titles = [labels["profile"]] + [labels[k] for k in ORDER if any(i["section"] == k for i in cv["items"])]
    lines = [line.strip().lower() for line in text.splitlines()]
    positions = [lines.index(title.lower()) if title.lower() in lines else -1 for title in titles]
    if -1 in positions or positions != sorted(positions):
        problems.append(("ats.headings", {"titles": ", ".join(titles)}))
    return problems


def docx_problems(path):
    """Tables and text boxes are often skipped or mixed up by ATS parsers."""
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml").decode("utf8")
    return [("ats.word_tables", {})] if "<w:tbl" in xml or "<w:txbxContent" in xml else []
