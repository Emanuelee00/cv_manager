import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cvagents import github_public, settings
from cvagents.db import connect, count_items, get_item
from cvagents.onboarding import ai_setup, set_excluded, start
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
    def setUp(self):
        self.settings_path = Path(tempfile.mkdtemp()) / "settings.json"
        patcher = mock.patch.object(start, "choose_github", return_value=("skip", ""))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_choices_are_saved_and_command_is_shown(self):
        conn = connect(":memory:")
        offer = cv_file("offre")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS + [offer], selects=["en", "skip"], checks=["pdf", "docx"])
        _, chosen, summary = start.run_start(prompter, conn, FakeProvider(), self.settings_path)
        saved = settings.load(self.settings_path)
        self.assertEqual((saved["offer"], saved["formats"], saved["ai"]), (offer, ["pdf", "docx"], "local"))
        self.assertIn(settings.RUN_COMMAND, summary)
        self.assertNotIn("api_key", self.settings_path.read_text())

    def test_exclusions_survive_a_new_start(self):
        conn = connect(":memory:")
        set_excluded(conn, "gh:segreto")
        start.run_start(ScriptedPrompter(texts=PROFILE_TEXTS, selects=["en", "skip"]), conn, FakeProvider(), self.settings_path)
        self.assertEqual(set_excluded(conn, "gh:altro"), ["gh:altro", "gh:segreto"])
        self.assertEqual(set_excluded(conn, "gh:altro", False), ["gh:segreto"])
    def test_full_path_saves_profile_and_confirmed_entries(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS + [cv_file()], selects=["en", "file"], confirms=[False], checks=[0])
        provider, chosen, summary = start.run_start(prompter, conn, FakeProvider(ENTRIES), self.settings_path)
        self.assertIsNotNone(provider)
        self.assertIn("Ada Rossi", get_item(conn, "manual:candidate-profile")["body"])
        self.assertEqual(count_items(conn, "cv"), 1)
        self.assertIn("1 entries from your CV", summary)

    def test_nothing_is_saved_if_user_unticks_everything(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS + [cv_file()], selects=["en", "file"], confirms=[False], checks=[])
        start.run_start(prompter, conn, FakeProvider(ENTRIES), self.settings_path)
        self.assertEqual(count_items(conn, "cv"), 0)

    def test_unreadable_cv_is_reported_and_start_continues(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS + ["/nope/cv.docx"], selects=["en", "file"], confirms=[False])
        _, _, summary = start.run_start(prompter, conn, FakeProvider(), self.settings_path)
        self.assertTrue(any("I could not do it" in m for m in prompter.said))
        self.assertIn("0 entries", summary)

    def test_skip_cv(self):
        conn = connect(":memory:")
        prompter = ScriptedPrompter(texts=PROFILE_TEXTS, selects=["en", "skip"], confirms=[False])
        self.assertIn("0 entries", start.run_start(prompter, conn, FakeProvider(), self.settings_path)[2])

    def test_ai_not_available_stops_cleanly(self):
        with mock.patch.object(start, "ensure_provider", side_effect=ai_setup.SetupIncomplete("manca")):
            provider, chosen, message = start.run_start(ScriptedPrompter(), connect(":memory:"), None, self.settings_path)
        self.assertEqual((provider, message), (None, "manca"))


class EnsureProvider(unittest.TestCase):
    def test_three_choices_are_always_shown(self):
        with mock.patch.object(ai_setup.claude_cli, "installed", return_value=False), \
             mock.patch.object(ai_setup.ollama, "is_up", return_value=False), \
             mock.patch.object(ai_setup, "make_provider", return_value=FakeProvider()):
            prompter = ScriptedPrompter(selects=["local"])
            provider, choice, _ = ai_setup.ensure_provider(prompter)
        self.assertEqual((provider.name, choice), ("Finto", "local"))

    def test_claude_code_missing_explains_and_lets_choose_again(self):
        with mock.patch.object(ai_setup.claude_cli, "installed", return_value=False), \
             mock.patch.object(ai_setup.ollama, "is_up", return_value=False), \
             mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-x"}):
            prompter = ScriptedPrompter(selects=["cli", "api"])
            provider, choice, _ = ai_setup.ensure_provider(prompter)
        self.assertEqual(choice, "api")
        self.assertTrue(any("Claude Code not found" in m for m in prompter.said))

    def test_api_key_is_asked_hidden_and_not_saved(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            provider = ai_setup.make_provider(ScriptedPrompter(texts=["sk-test"]), "api")
        self.assertEqual(provider.api_key, "sk-test")

    def test_local_setup_is_used_for_local_choice(self):
        with mock.patch.object(ai_setup, "setup_local", return_value="provider-locale") as setup:
            self.assertEqual(ai_setup.make_provider(ScriptedPrompter(), "local"), "provider-locale")
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
