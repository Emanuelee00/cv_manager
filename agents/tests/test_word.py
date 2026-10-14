import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.dom import minidom

from cvagents.word import build_docx

PROFILE = "NOME: Ada Rossi\nCITTÀ: Lyon\nETÀ: 26 ans\nPATENTE: B\nLINK: https://github.com/ada · email ada@x.fr\nTELEFONI: +33 6 00 00 00 01"
CV = {"headline": "Alternance dev", "profile": "Développeuse web & data <à Lyon>.", "items": [
    {"section": "experience", "title": "Dev web", "period": "2022 – 2024", "text": "Sites pour 3 clients.", "source_id": "a"},
    {"section": "interest", "title": "Tir à l'arc", "text": "tir à l'arc", "source_id": "b"}]}
PNG_1X1 = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                        "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")


class Word(unittest.TestCase):
    def build(self, profile=PROFILE):
        path = Path(tempfile.mkdtemp()) / "cv.docx"
        build_docx(profile, CV, "fr", path)
        return zipfile.ZipFile(path)

    def test_package_is_valid_xml_with_escaped_text(self):
        docx = self.build()
        for name in ("word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml", "word/styles.xml"):
            minidom.parseString(docx.read(name))
        self.assertIn("&amp; data &lt;à Lyon&gt;", docx.read("word/document.xml").decode())

    def test_links_are_clickable(self):
        rels = self.build().read("word/_rels/document.xml.rels").decode()
        self.assertIn('Target="mailto:ada@x.fr" TargetMode="External"', rels)
        self.assertIn('Target="tel:+33600000001"', rels)

    def test_photo_is_embedded_when_present(self):
        photo = Path(tempfile.mkdtemp()) / "foto.png"
        photo.write_bytes(PNG_1X1)
        docx = self.build(PROFILE + f"\nFOTO: {photo}")
        self.assertIn("word/media/foto.png", docx.namelist())
        self.assertTrue(re.search(r'r:embed="rId\d+"', docx.read("word/document.xml").decode()))

    def test_no_photo_no_media(self):
        self.assertNotIn("word/media/foto.png", self.build().namelist())


if __name__ == "__main__":
    unittest.main()
