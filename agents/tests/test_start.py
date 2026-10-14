import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cvagents import github_public
from cvagents.db import connect, count_items, get_item
from cvagents.onboarding import ai_setup, start
from tests.helpers import FakeProvider, ScriptedPrompter

PROFILE_TEXTS = ["Ada Rossi", "Développeuse web", "Lyon, France", "ada@x.fr", "+33 6 00", "https://github.com/ada", "ada",
                 "", "italienne (UE)", "B", ""]
ENTRIES = json.dumps({"entries": [{"type": "experience", "title": "Dev web", "org": "Acme", "period": "2022 – 2024",
                                   "description": "Sites pour 3 clients"},
                                  {"type": "skill", "title": "Langages", "description": "Python, SQL"}]})


def cv_file(text="Dev web chez Acme 2022 – 2024, sites pour 3 clients. Python, SQL."):
    path = Path(tempfile.mkdtemp()) / "cv.txt"
    path.write_text(text, encoding="utf8")
    return str(path)


class Start(unittest.TestCase):
    def test_full_path_saves_profile_and_confirmed_entries(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS + [cv_file()], selects=["file"], confirms=[False], checks=[0])
        provider, summary = start.run_start(prompter, conn, FakeProvider(ENTRIES))
        self.assertIsNotNone(provider)
        self.assertIn("Ada Rossi", get_item(conn, "manual:profilo-candidato")["body"])
        self.assertEqual(count_items(conn, "cv"), 1)
        self.assertIn("1 voci dal CV", summary)

    def test_nothing_is_saved_if_user_unticks_everything(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS + [cv_file()], selects=["file"], confirms=[False], checks=[])
        start.run_start(prompter, conn, FakeProvider(ENTRIES))
        self.assertEqual(count_items(conn, "cv"), 0)

    def test_unreadable_cv_is_reported_and_start_continues(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS + ["/nope/cv.docx"], selects=["file"], confirms=[False])
        _, summary = start.run_start(prompter, conn, FakeProvider())
        self.assertTrue(any("Non ci sono riuscito" in m for m in prompter.said))
        self.assertIn("0 voci", summary)

    def test_skip_cv(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS, selects=["skip"], confirms=[False])
        self.assertIn("0 voci", start.run_start(prompter, conn, FakeProvider())[1])

    def test_ai_not_available_stops_cleanly(self):
        with mock.patch.object(start, "ensure_provider", side_effect=ai_setup.SetupIncomplete("manca")):
            provider, message = start.run_start(ScriptedPrompter(), connect(":memory:"))
        self.assertEqual((provider, message), (None, "manca"))


class EnsureProvider(unittest.TestCase):
    def test_picks_the_chosen_available_provider(self):
        found = [("api", "Claude (API Anthropic)", lambda: FakeProvider())]
        with mock.patch.object(ai_setup, "available", return_value=found):
            prompter = ScriptedPrompter(selects=["Claude (API Anthropic)"])
            self.assertEqual(ai_setup.ensure_provider(prompter).name, "Finto")

    def test_offers_local_setup_when_no_local_model(self):
        with mock.patch.object(ai_setup, "available", return_value=[]), \
             mock.patch.object(ai_setup, "setup_local", return_value="provider-locale") as setup:
            prompter = ScriptedPrompter(selects=[ai_setup.LOCAL])
            self.assertEqual(ai_setup.ensure_provider(prompter), "provider-locale")
            setup.assert_called_once()


class PublicGithub(unittest.TestCase):
    def test_saves_only_non_fork_repos(self):
        repos = [{"name": "a", "full_name": "u/a", "html_url": "http://x/a", "description": "app", "language": "Python"},
                 {"name": "b", "full_name": "u/b", "html_url": "http://x/b", "fork": True}]

        def fake_fetch(url, raw=False):
            return "README di prova" if raw else repos

        conn = connect(":memory:")
        with mock.patch.object(github_public, "fetch", fake_fetch):
            self.assertEqual(github_public.sync_public(conn, "u"), 1)
        self.assertIn("README di prova", get_item(conn, "gh:a")["body"])
        self.assertIsNone(get_item(conn, "gh:b"))


if __name__ == "__main__":
    unittest.main()
