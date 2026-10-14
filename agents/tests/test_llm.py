import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from cvagents.llm import AnthropicProvider, ClaudeCliProvider, LLMError, OllamaProvider, available
from cvagents.llm import claude_cli, ollama
from cvagents.llm.anthropic import split_system

SEEN = {}


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, lines=False):
        data = ("\n".join(map(json.dumps, body)) if lines else json.dumps(body)).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.reply({"models": [{"name": "qwen3:4b"}]})

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN["payload"], SEEN["headers"] = payload, {k.lower(): v for k, v in self.headers.items()}
        if self.path == "/api/chat":
            self.reply([{"message": {"content": "Ci"}}, {"message": {"content": "ao"}, "done": True}], lines=True)
        else:
            self.reply({"content": [{"type": "text", "text": "ok da claude"}]})


class ClosingServer(HTTPServer):
    def shutdown(self):
        super().shutdown()
        self.server_close()


def serve():
    server = ClosingServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


class OllamaTests(unittest.TestCase):
    def setUp(self):
        self.server, self.host = serve()
        self.addCleanup(self.server.shutdown)

    def test_chat_streams_tokens_and_joins_them(self):
        tokens = []
        text = OllamaProvider("qwen3:4b", self.host).chat([{"role": "user", "content": "ciao"}], on_token=tokens.append)
        self.assertEqual((text, tokens), ("Ciao", ["Ci", "ao"]))
        self.assertEqual(SEEN["payload"]["options"]["temperature"], 0.2)

    def test_schema_goes_in_format(self):
        schema = {"type": "object"}
        OllamaProvider("m", self.host).chat([{"role": "user", "content": "x"}], schema=schema)
        self.assertEqual(SEEN["payload"]["format"], schema)

    def test_models_and_up(self):
        self.assertTrue(ollama.is_up(self.host))
        self.assertEqual(ollama.list_models(self.host), ["qwen3:4b"])

    def test_down_is_a_clear_error(self):
        with self.assertRaises(LLMError):
            OllamaProvider("m", "http://127.0.0.1:1").chat([{"role": "user", "content": "x"}])


class ClaudeTests(unittest.TestCase):
    def test_api_sends_key_and_separates_system(self):
        server, host = serve()
        self.addCleanup(server.shutdown)
        provider = AnthropicProvider("sk-test", url=host + "/v1/messages")
        text = provider.chat([{"role": "system", "content": "regole"}, {"role": "user", "content": "ciao"}])
        self.assertEqual(text, "ok da claude")
        self.assertEqual(SEEN["payload"]["system"], "regole")
        self.assertEqual(SEEN["headers"]["x-api-key"], "sk-test")

    def test_api_without_key_fails_clearly(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(LLMError):
                AnthropicProvider().chat([{"role": "user", "content": "x"}])

    def test_split_system(self):
        system, rest = split_system([{"role": "system", "content": "a"}, {"role": "user", "content": "b"}])
        self.assertEqual((system, len(rest)), ("a", 1))

    def test_cli_passes_script_on_stdin(self):
        done = mock.Mock(returncode=0, stdout="risposta", stderr="")
        with mock.patch.object(claude_cli.subprocess, "run", return_value=done) as run:
            text = ClaudeCliProvider().chat([{"role": "system", "content": "s"}, {"role": "user", "content": "u"}])
        self.assertEqual(text, "risposta")
        self.assertIn("[ISTRUZIONI]\ns", run.call_args.kwargs["input"])

    def test_cli_failure_is_an_error(self):
        with mock.patch.object(claude_cli.subprocess, "run", return_value=mock.Mock(returncode=1, stdout="", stderr="no")):
            with self.assertRaises(LLMError):
                ClaudeCliProvider().chat([{"role": "user", "content": "x"}])


class FindClaude(unittest.TestCase):
    def test_falls_back_to_vscode_extension(self):
        with mock.patch.object(claude_cli.shutil, "which", return_value=None), \
             mock.patch.object(claude_cli.glob, "glob", return_value=["/ext/a/claude", "/ext/b/claude"]):
            self.assertEqual(claude_cli.find_claude(), "/ext/b/claude")

    def test_none_when_nothing_found(self):
        with mock.patch.object(claude_cli.shutil, "which", return_value=None), \
             mock.patch.object(claude_cli.glob, "glob", return_value=[]):
            self.assertIsNone(claude_cli.find_claude())


class AvailableTests(unittest.TestCase):
    def test_lists_only_what_works(self):
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(claude_cli, "find_claude", return_value=None), \
             mock.patch.object(ollama, "is_up", return_value=False):
            self.assertEqual(available(), [])
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "k"}, clear=True), \
             mock.patch.object(claude_cli, "find_claude", return_value="/usr/bin/claude"), \
             mock.patch.object(ollama, "is_up", return_value=False):
            self.assertEqual([a[0] for a in available()], ["api", "cli"])


if __name__ == "__main__":
    unittest.main()
