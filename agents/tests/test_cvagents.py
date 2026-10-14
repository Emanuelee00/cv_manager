import json
import subprocess
import tempfile
import unittest
from unittest import mock

from cvagents import github, importer
from cvagents.db import connect, count_items
from cvagents.search import build_match, search

ENTRY = {
    "id": "1", "type": "experience", "title": "Sviluppatore web", "org": "Green Village",
    "period": "2023", "description": "Sito WordPress e SEO per l'azienda", "result": "", "tags": ["WordPress"],
}


def seeded_conn():
    conn = connect(":memory:")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"entries": [ENTRY]}, f)
    importer.import_file(conn, f.name)
    return conn, f.name


class ImportAndSearch(unittest.TestCase):
    def test_import_is_idempotent(self):
        conn, path = seeded_conn()
        importer.import_file(conn, path)
        self.assertEqual(count_items(conn, "cv"), 1)

    def test_search_finds_by_word_and_prefix(self):
        conn, _ = seeded_conn()
        self.assertEqual(search(conn, "wordpress")[0]["title"], "Sviluppatore web")
        self.assertTrue(search(conn, "azienda SEO"))

    def test_search_ignores_accents_and_empty_query(self):
        conn = connect(":memory:")
        importer.add_manual(conn, "project", "Café", "Progetto per le città")
        self.assertTrue(search(conn, "cafe citta"))
        self.assertEqual(search(conn, "?!"), [])

    def test_source_filter(self):
        conn, _ = seeded_conn()
        importer.add_manual(conn, "project", "Altro", "WordPress per un amico")
        self.assertEqual({r["source"] for r in search(conn, "wordpress", source="manual")}, {"manual"})

    def test_build_match_quotes_words(self):
        self.assertEqual(build_match('a "bc" de-fg'), '"bc"* OR "de"* OR "fg"*')


def fake_gh(*args):
    if args[:2] == ("repo", "view"):
        return json.dumps({"name": "app", "description": "Un'app", "url": "u", "isFork": False})
    if args[:2] == ("api", "user"):
        return "emanuele\n"
    if args[0] == "repo":
        repos = [{"name": "app", "description": "Un'app", "url": "u", "isFork": False}, {"name": "fk", "url": "u", "isFork": True}]
        return json.dumps(repos)
    if args[1].endswith("/languages"):
        return json.dumps({"Python": 10})
    if args[1].endswith("/readme"):
        return "Questo README parla di rag"
    if "/branches" in args[1]:
        return "main\nemanuele\n"
    if "sha=emanuele" in args[1]:
        return "aaa fix bug\nbbb add hash HMAC"
    return "aaa fix bug"


class GithubSync(unittest.TestCase):
    def test_sync_skips_forks_and_is_searchable(self):
        conn = connect(":memory:")
        with mock.patch.object(github, "run_gh", fake_gh):
            self.assertEqual(github.sync_all(conn), 1)
        self.assertEqual(search(conn, "rag python")[0]["source"], "github")

    def test_default_sync_reads_only_main_branch(self):
        conn = connect(":memory:")
        with mock.patch.object(github, "run_gh", fake_gh):
            github.sync_all(conn)
        self.assertEqual(search(conn, "hmac"), [])

    def test_deep_reads_all_branches_and_stays_deep(self):
        conn = connect(":memory:")
        with mock.patch.object(github, "run_gh", fake_gh):
            github.sync_deep(conn, "app")
            github.sync_all(conn)
        body = search(conn, "hmac")[0]["body"]
        self.assertIn("[emanuele] add hash HMAC", body)
        self.assertEqual(body.count("fix bug"), 1)

    def test_missing_readme_still_saves_repo(self):
        conn = connect(":memory:")
        err = subprocess.CalledProcessError(1, "gh", stderr="404")
        def flaky(*args):
            if args[0] == "api" and args[1].endswith("/readme"):
                raise err
            return fake_gh(*args)
        with mock.patch.object(github, "run_gh", flaky):
            self.assertEqual(github.sync_all(conn), 1)


if __name__ == "__main__":
    unittest.main()
