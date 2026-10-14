"""Vista dal vivo nel terminale (Rich): i passi degli agenti, il tempo, il testo che l'AI sta scrivendo."""
import threading
import time
from contextlib import contextmanager

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

TAIL = 220


class LiveBoard:
    """Tabella dei passi che si aggiorna da sola; si mette in pausa quando il programma fa una domanda."""

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
        return Panel(Group(table, stream), title=f"{self.title} · chiamate AI: {self.calls}", border_style="cyan")

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
        """Testo che l'AI sta scrivendo; `new_call` conta una nuova chiamata."""
        with self.lock:
            self.calls += new_call
            self.tail = (self.tail + token)[-TAIL * 2:]

    def pause(self):
        """Ferma il pannello (resta stampato) prima di una domanda; il passo successivo ne apre uno nuovo."""
        with self.lock:
            if self.live is not None:
                self.live.stop()
                self.live, self.first_visible = None, len(self.rows)
