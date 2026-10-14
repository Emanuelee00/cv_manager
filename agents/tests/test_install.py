import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cvagents import doctor, ollama_install
from cvagents.cli import build_parser
from cvagents.commands import HANDLERS, SPEC


class PickAsset(unittest.TestCase):
    ASSETS = [{"name": "ollama-darwin.tgz"}, {"name": "ollama-linux-arm64.tgz"}, {"name": "ollama-linux-amd64.tar.zst"}]

    def test_chooses_by_architecture(self):
        self.assertEqual(ollama_install.pick_asset(self.ASSETS, "x86_64")["name"], "ollama-linux-amd64.tar.zst")
        self.assertEqual(ollama_install.pick_asset(self.ASSETS, "aarch64")["name"], "ollama-linux-arm64.tgz")

    def test_unknown_machine_is_a_clear_error(self):
        with self.assertRaises(RuntimeError):
            ollama_install.pick_asset(self.ASSETS, "riscv64")


class InstallLinux(unittest.TestCase):
    def test_extracts_binary_into_dest(self):
        dest = tempfile.mkdtemp()

        def fake_download(url, target, on_progress=None):
            with tarfile.open(target, "w:gz") as tar:
                data = b"#!/bin/sh\n"
                info = tarfile.TarInfo("bin/ollama")
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

        release = io.BytesIO(b'{"assets": [{"name": "ollama-linux-amd64.tgz", "browser_download_url": "http://x"}]}')
        with mock.patch.object(ollama_install.urllib.request, "urlopen", return_value=release), \
             mock.patch.object(ollama_install, "download", fake_download), \
             mock.patch.object(ollama_install.platform, "machine", return_value="x86_64"):
            binary = ollama_install.install_linux(dest)
        self.assertTrue(Path(binary).is_file())
        self.assertEqual(Path(binary), Path(dest) / "bin" / "ollama")


class Doctor(unittest.TestCase):
    def test_report_mentions_model_and_providers(self):
        text = "\n".join(doctor.report("http://127.0.0.1:1"))
        self.assertIn("Modello locale consigliato: qwen3:", text)
        self.assertIn("Utilizzabili ora:", text)


if __name__ == "__main__":
    unittest.main()


class CliWiring(unittest.TestCase):
    def test_every_command_has_a_handler_and_parses(self):
        self.assertEqual(set(HANDLERS), {name for name, *_ in SPEC})
        args = build_parser().parse_args(["search", "python", "--limit", "3"])
        self.assertEqual((args.cmd, args.limit), ("search", 3))
        self.assertTrue(build_parser().parse_args(["doctor", "--pull"]).pull)
