import shutil
import tempfile
import unittest
from pathlib import Path

from cvagents import ats
from cvagents.pipeline.output import write_files
from cvagents.word import build_docx

PROFILE = "NAME: Ada Rossi\nHEADLINE: Dev\nCITY: Lyon, France\nLINKS: https://github.com/ada · email ada@x.fr\nPHONES: +33 6 00 00 00 01"
KINDS = ["profile", "education", "project"]
CV = {"headline": "Alternance dev", "profile": "Développeuse web à Lyon.", "items": [
    {"section": "education", "title": "Master", "period": "2024", "text": "Études à Lyon.", "source_id": "a"},
    {"section": "project", "title": "Site", "period": "", "text": "Migration Django 4.2 → 5.2 ✔", "source_id": "b"}]}


class Characters(unittest.TestCase):
    def test_risky_symbols_become_plain(self):
        self.assertEqual(ats.make_safe("Django 4.2 → 5.2 ✔ ★ • ok 🚀"), "Django 4.2 -> 5.2   - ok ")
        self.assertEqual(ats.safe_cv(CV)["items"][1]["text"], "Migration Django 4.2 -> 5.2 ")


class TextChecks(unittest.TestCase):
    def test_clean_text_has_no_problems(self):
        text = "ADA ROSSI\nada@x.fr\nPROFIL\n...\nFORMATION\n...\nPROJETS\n..."
        self.assertEqual(ats.text_problems(text, CV, "fr", "Ada Rossi", "ada@x.fr", KINDS), [])

    def test_missing_contacts_and_wrong_order_are_reported(self):
        keys = [k for k, _ in ats.text_problems("PROJETS\nFORMATION\nPROFIL", CV, "fr", "Ada Rossi", "ada@x.fr", KINDS)]
        self.assertEqual(keys, ["ats.missing_name", "ats.missing_email", "ats.headings"])
        self.assertEqual(ats.text_problems("   ", CV, "fr", "Ada", "", KINDS), [("ats.no_text", {})])

    def test_a_section_word_inside_a_sentence_is_not_a_title(self):
        text = "ADA ROSSI\nada@x.fr\nPROFIL\nJ'aime les projets sociaux et la formation.\nFORMATION\nPROJETS"
        self.assertEqual(ats.text_problems(text, CV, "fr", "Ada Rossi", "ada@x.fr", KINDS), [])

    def test_our_word_file_has_no_tables_or_text_boxes(self):
        path = build_docx(PROFILE, CV, "fr", Path(tempfile.mkdtemp()) / "cv.docx")
        self.assertEqual(ats.docx_problems(path), [])


@unittest.skipUnless(shutil.which("chromium-browser") and shutil.which("pdftotext"), "needs Chromium and pdftotext")
class EndToEnd(unittest.TestCase):
    def test_generated_pdf_and_word_pass_the_ats_check(self):
        done = write_files(PROFILE, CV, "fr", tempfile.mkdtemp(), ("pdf", "docx"))
        self.assertEqual((done["pages"], done["problems"], done["score"]), (1, [], 100))
        self.assertIn("->", ats.pdf_text(done["files"][0]))

    def test_each_style_fits_one_page_and_modern_scores_lower(self):
        scores = {style: write_files(PROFILE, CV, "fr", tempfile.mkdtemp(), ["pdf"], style) for style in ("classic", "minimal", "modern")}
        self.assertTrue(all(d["pages"] == 1 for d in scores.values()))
        self.assertEqual((scores["classic"]["score"], scores["minimal"]["score"]), (100, 100))
        self.assertLessEqual(scores["modern"]["score"], 70)


if __name__ == "__main__":
    unittest.main()
