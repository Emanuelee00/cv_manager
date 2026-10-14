import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cvagents import render

LONG_BODY = "<p>riga</p>" * 400


def write_html(body):
    path = Path(tempfile.mkdtemp()) / "t.html"
    path.write_text(f"<!doctype html><meta charset=utf-8><body>{body}</body>", encoding="utf8")
    return path


class RenderUnit(unittest.TestCase):
    def test_page_count_parses_pdfinfo(self):
        out = mock.Mock(stdout="Title: x\nPages:           3\nPage size: A4\n")
        with mock.patch.object(render.subprocess, "run", return_value=out):
            self.assertEqual(render.page_count("x.pdf"), 3)

    def test_missing_browser_is_a_clear_error(self):
        with mock.patch.object(render.shutil, "which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                render.find_browser()


@unittest.skipUnless(shutil.which("chromium-browser") and shutil.which("pdfinfo"), "serve Chromium e pdfinfo")
class RenderReal(unittest.TestCase):
    def test_short_page_fits_and_long_page_does_not(self):
        self.assertEqual(render.fits_one_page(write_html("<p>ciao</p>")), (True, 1))
        ok, pages = render.fits_one_page(write_html(LONG_BODY))
        self.assertFalse(ok)
        self.assertGreater(pages, 1)


if __name__ == "__main__":
    unittest.main()
