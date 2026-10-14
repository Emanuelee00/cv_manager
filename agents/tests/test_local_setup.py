import json
import unittest
from unittest import mock

from cvagents import local_setup, sysinfo
from cvagents.llm.ollama import OllamaProvider
from tests.test_llm import Fake, serve


class PickModel(unittest.TestCase):
    def test_tiers_follow_ram(self):
        self.assertEqual(local_setup.pick_model(0), "qwen3:1.7b")
        self.assertEqual(local_setup.pick_model(4), "qwen3:1.7b")
        self.assertEqual(local_setup.pick_model(7.6), "qwen3:4b")
        self.assertEqual(local_setup.pick_model(16), "qwen3:8b")
        self.assertEqual(local_setup.pick_model(64), "qwen3:14b")


class RamAndHints(unittest.TestCase):
    def test_ram_on_this_machine_is_positive_or_zero(self):
        self.assertGreaterEqual(sysinfo.total_ram_gb(), 0)

    def test_unknown_platform_gives_zero(self):
        with mock.patch.object(sysinfo.sys, "platform", "plan9"):
            self.assertEqual(sysinfo.total_ram_gb(), 0.0)

    def test_hints_per_platform(self):
        self.assertIn("installer", local_setup.install_hint("win32"))
        self.assertIn("brew", local_setup.install_hint("darwin"))
        self.assertIn("sudo", local_setup.install_hint("linux"))

    def test_find_ollama_returns_none_when_missing(self):
        with mock.patch.object(local_setup.shutil, "which", return_value=None), \
             mock.patch.object(local_setup.Path, "home", return_value=local_setup.Path("/nonexistent")):
            self.assertIsNone(local_setup.find_ollama())


class Pull(unittest.TestCase):
    def test_pull_reports_progress(self):
        server, host = serve()
        self.addCleanup(server.shutdown)
        seen = []

        def pull_post(handler):
            handler.rfile.read(int(handler.headers["Content-Length"]))
            handler.reply([{"status": "pulling", "total": 100, "completed": 50}, {"status": "success"}], lines=True)

        with mock.patch.object(Fake, "do_POST", pull_post):
            local_setup.pull_model("qwen3:4b", host, lambda status, frac: seen.append((status, frac)))
        self.assertEqual(seen, [("pulling", 0.5), ("success", None)])


class ThinkTags(unittest.TestCase):
    def test_think_blocks_are_removed(self):
        server, host = serve()
        self.addCleanup(server.shutdown)

        def chat_post(handler):
            handler.rfile.read(int(handler.headers["Content-Length"]))
            handler.reply([{"message": {"content": "<think>ragiono</think>Ciao"}}], lines=True)

        with mock.patch.object(Fake, "do_POST", chat_post):
            self.assertEqual(OllamaProvider("m", host).chat([{"role": "user", "content": "x"}]), "Ciao")


if __name__ == "__main__":
    unittest.main()
