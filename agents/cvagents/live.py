"""Live terminal view (Rich): the agents' steps, elapsed time, the text the AI is writing."""
import threading
import time
from contextlib import contextmanager

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from cvagents.i18n import t

TAIL = 220


class LiveBoard:
    """Self-refreshing table of steps; it pauses when the program asks a question."""

    def __init__(self, title, console=None):
        self.title, self.console, self.lock = title, console or Console(), threading.Lock()
        self.rows, self.tail, self.calls, self.first_visible, self.live = [], "", 0, 0, None

    def render(self):
        table = Table.grid(padding=(0, 2))
        for row in self.rows[self.first_visible:]:
            seconds = (row["end"] or time.monotonic()) - row["start"]
            icon = Spinner("dots", style="cyan") if row["status"] == "running" else Text("✔" if row["status"] == "done" else "✖",
                                                                                        style="green" if row["status"] == "done" else "red")
            table.add_row(icon, Text(row["name"], style="bold" if row["status"] == "running" else ""), Text(f"{seconds:5.1f} s", style="dim"))
        stream = Text(self.tail[-TAIL:].replace("\n", " "), style="dim italic") if self.tail else Text("")
        return Panel(Group(table, stream), title=f"{self.title} · {t('live.calls', calls=self.calls)}", border_style="cyan")

    @contextmanager
    def step(self, name):
        with self.lock:
            row = {"name": name, "start": time.monotonic(), "end": None, "status": "running"}
            self.rows.append(row)
            self.tail = ""
            if self.live is None:
                self.live = Live(get_renderable=self.render, console=self.console, refresh_per_second=8)
                self.live.start()
        try:
            yield
            row["status"] = "done"
        except BaseException:
            row["status"] = "error"
            raise
        finally:
            row["end"] = time.monotonic()

    def stream(self, token, new_call=False):
        """Text the AI is writing; `new_call` counts a new call."""
        with self.lock:
            self.calls += new_call
            self.tail = (self.tail + token)[-TAIL * 2:]

    def pause(self):
        """Stop the panel (it stays printed) before a question; the next step opens a new one."""
        with self.lock:
            if self.live is not None:
                self.live.stop()
                self.live, self.first_visible = None, len(self.rows)
