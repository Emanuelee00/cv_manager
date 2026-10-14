"""Take a photo with the computer's camera: a page on this computer only (127.0.0.1) opens in the browser and sends the picture back."""
import http.server
import threading
import webbrowser
from pathlib import Path
from string import Template

from cvagents.i18n import t

PAGE = Path(__file__).resolve().parents[2] / "templates" / "camera.html"
TEXTS = ("title", "hint", "take", "retake", "use", "done", "denied")
MAX_BYTES = 20_000_000


class CameraPage(http.server.BaseHTTPRequestHandler):
    """GET: the camera page in the interface language. POST /photo: the PNG, saved to `server.dest`."""

    def do_GET(self):
        body = Template(PAGE.read_text(encoding="utf8")).safe_substitute({k: t(f"camera.{k}") for k in TEXTS}).encode("utf8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(size) if self.path == "/photo" and 0 < size <= MAX_BYTES else b""
        self.send_response(200 if data.startswith(b"\x89PNG") else 400)
        self.end_headers()
        if data.startswith(b"\x89PNG"):
            self.server.dest.write_bytes(data)
            self.server.got.set()

    def log_message(self, *args):
        pass


def capture(dest, show, timeout=600):
    """Open the camera page, wait for the photo; `show(url)` tells the user the address. Returns the path, or "" if none came."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CameraPage)
    server.dest, server.got = dest, threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/"
    show(url)
    webbrowser.open(url)
    got = server.got.wait(timeout)
    server.shutdown()
    server.server_close()
    return str(dest) if got else ""
