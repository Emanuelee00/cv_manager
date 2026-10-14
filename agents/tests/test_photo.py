import io
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from PIL import Image

from cvagents.onboarding import photo_step
from cvagents.photo import camera, retouch
from tests.helpers import ScriptedPrompter


def png(size=(64, 48), colour=(200, 180, 160)):
    buffer = io.BytesIO()
    Image.new("RGB", size, colour).save(buffer, "PNG")
    return buffer.getvalue()


def browser_sending(data, pages):
    """A fake browser: reads the page, then posts `data` as the photo."""
    def open_url(url):
        def run():
            pages.append(urllib.request.urlopen(url).read().decode("utf8"))
            try:
                urllib.request.urlopen(urllib.request.Request(url + "photo", data=data, method="POST"))
            except urllib.error.HTTPError:
                pass
        threading.Thread(target=run).start()
    return open_url


class Camera(unittest.TestCase):
    def test_the_photo_from_the_page_is_saved(self):
        dest, pages = Path(tempfile.mkdtemp()) / "camera.png", []
        with mock.patch("webbrowser.open", browser_sending(png(), pages)):
            self.assertEqual(camera.capture(dest, lambda url: None, timeout=10), str(dest))
        self.assertEqual(dest.read_bytes(), png())
        self.assertIn("<title>Photo for your CV</title>", pages[0])
        self.assertNotIn("$take", pages[0])

    def test_something_that_is_not_a_png_is_refused(self):
        dest = Path(tempfile.mkdtemp()) / "camera.png"
        with mock.patch("webbrowser.open", browser_sending(b"<script>", [])):
            self.assertEqual(camera.capture(dest, lambda url: None, timeout=1), "")
        self.assertFalse(dest.exists())


class Retouch(unittest.TestCase):
    def test_crop_is_square_on_the_head_and_inside_the_picture(self):
        mask = Image.new("L", (1280, 720))
        mask.paste(255, (500, 100, 780, 400))
        mask.paste(255, (300, 400, 980, 720))
        x0, y0, x1, y1 = retouch.head_and_shoulders(mask)
        self.assertEqual(x1 - x0, y1 - y0)
        self.assertTrue(0 <= x0 and 0 <= y0 and x1 <= 1280 and y1 <= 720)
        self.assertAlmostEqual((x0 + x1) / 2, 640, delta=2)

    def test_professional_writes_a_square_photo_on_neutral_background(self):
        folder = Path(tempfile.mkdtemp())
        Image.new("RGB", (320, 240), (40, 160, 40)).save(folder / "raw.png")
        person = Image.new("RGBA", (320, 240), (0, 0, 0, 0))
        person.paste((150, 120, 100, 255), (110, 40, 210, 240))
        with mock.patch.object(retouch, "remove", return_value=person), mock.patch.object(retouch, "new_session"):
            out = Image.open(retouch.professional(folder / "raw.png", folder / "pro.png"))
        self.assertEqual(out.size, (retouch.SIZE, retouch.SIZE))
        self.assertEqual(out.getpixel((2, 2)), retouch.BACKGROUND)


class Step(unittest.TestCase):
    def test_a_given_photo_is_kept_and_the_camera_is_not_offered(self):
        prompter = ScriptedPrompter()
        self.assertEqual(photo_step.ask_photo(prompter, ""), "")
        self.assertEqual(photo_step.ask_photo(prompter, "/no/photo.png"), "/no/photo.png")
        self.assertEqual(len(prompter.asked), 1)

    def test_camera_then_choice_of_the_version(self):
        folder = Path(tempfile.mkdtemp())
        prompter = ScriptedPrompter(selects=["again", "pro"], confirms=[True])
        with mock.patch.object(photo_step, "capture", return_value=str(folder / "camera.png")) as capture, \
                mock.patch.object(photo_step, "retouch", return_value=(str(folder / "photo.png"), "")), mock.patch("webbrowser.open"):
            self.assertEqual(photo_step.ask_photo(prompter, "", folder), str(folder / "photo.png"))
        self.assertEqual(capture.call_count, 2)


if __name__ == "__main__":
    unittest.main()
