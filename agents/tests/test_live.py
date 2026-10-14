import io
import unittest

from rich.console import Console

from cvagents.live import LiveBoard
from cvagents.live_wrappers import TrackedPrompter, TrackedProvider
from tests.helpers import FakeProvider, ScriptedPrompter


def board():
    return LiveBoard("Prova", Console(file=io.StringIO(), force_terminal=True, width=80))


class Board(unittest.TestCase):
    def test_steps_end_done_or_error(self):
        b = board()
        with b.step("Uno"):
            pass
        with self.assertRaises(ValueError):
            with b.step("Due"):
                raise ValueError("x")
        self.assertEqual([r["status"] for r in b.rows], ["done", "error"])
        b.pause()
        self.assertIn("Uno", b.console.file.getvalue())

    def test_pause_hides_finished_steps_from_next_panel(self):
        b = board()
        with b.step("Uno"):
            pass
        b.pause()
        with b.step("Due"):
            pass
        self.assertEqual(b.first_visible, 1)
        b.pause()


class Wrappers(unittest.TestCase):
    def test_provider_counts_calls_and_streams_text(self):
        b = board()
        provider = TrackedProvider(FakeProvider("ciao"), b)
        self.assertEqual(provider.chat([{"role": "user", "content": "x"}]), "ciao")
        self.assertEqual((b.calls, provider.local, provider.name), (1, True, "Finto"))

    def test_prompter_pauses_before_questions_but_not_for_messages(self):
        b = board()
        prompter = TrackedPrompter(ScriptedPrompter(texts=["risposta"]), b)
        with prompter.step("Lavoro"):
            prompter.say("messaggio")
            self.assertIsNotNone(b.live)
        self.assertEqual(prompter.text("Domanda?"), "risposta")
        self.assertIsNone(b.live)


if __name__ == "__main__":
    unittest.main()
