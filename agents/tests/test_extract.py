import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from cvagents.db import connect, count_items
from cvagents.importer import add_entries
from cvagents.llm.base import LLMError
from cvagents.onboarding import cv_text, extract
from tests.helpers import FakeProvider

CV = "Ada Rossi\n\nEsperienza\nSviluppatrice web a Lione, 2022 – 2024, ha gestito 3 siti.\n\nFormazione\nMaster a Lione 2020"


def reply(*entries):
    return json.dumps({"entries": list(entries)})


class ReadCv(unittest.TestCase):
    def test_txt_and_docx(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "cv.txt").write_text(CV, encoding="utf8")
        self.assertEqual(cv_text.read_cv_text(folder / "cv.txt"), CV)
        with zipfile.ZipFile(folder / "cv.docx", "w") as z:
            z.writestr("word/document.xml", "<w:p><w:t>Ciao &amp; ciao</w:t></w:p><w:p><w:t>Due</w:t></w:p>")
        self.assertEqual(cv_text.read_cv_text(folder / "cv.docx"), "Ciao & ciao\nDue")

    def test_unsupported_format(self):
        with self.assertRaises(ValueError):
            cv_text.read_cv_text("cv.odt")


class Extract(unittest.TestCase):
    def test_split_keeps_paragraphs_together(self):
        chunks = extract.split_text("a\n\nb\n\nc", max_chars=4)
        self.assertEqual(chunks, ["a\n\nb", "c"])

    def test_parse_tolerates_text_around_json(self):
        raw = 'Ecco: ' + reply({"type": "experience", "title": "Dev"}) + ' fatto'
        self.assertEqual(extract.parse_entries(raw)[0]["title"], "Dev")

    def test_parse_drops_bad_type_and_garbage_is_an_error(self):
        self.assertEqual(extract.parse_entries(reply({"type": "boh", "title": "x"})), [])
        with self.assertRaises(LLMError):
            extract.parse_entries("nessun json")

    def test_invented_numbers_are_flagged_not_dropped(self):
        provider = FakeProvider(reply({"type": "experience", "title": "Dev", "description": "gestito 3 siti, 99 utenti"}))
        entry = extract.extract_entries(provider, CV)[0]
        self.assertIn("99", entry["note"])
        self.assertNotIn("3,", entry["note"])

    def test_add_entries_saves_to_database(self):
        conn = connect(":memory:")
        n = add_entries(conn, [{"type": "education", "title": "Master", "org": "Lione", "period": "2020"}])
        self.assertEqual((n, count_items(conn, "cv")), (1, 1))


if __name__ == "__main__":
    unittest.main()
