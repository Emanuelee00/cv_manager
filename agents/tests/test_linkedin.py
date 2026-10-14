import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cvagents import linkedin
from cvagents.onboarding import job_search
from tests.helpers import ScriptedPrompter

JOBS = [{"id": "111", "title": "Dev full stack", "company": "Acme", "location": "Marseille, France", "date": "2026-10-12"},
        {"id": "222", "title": "Dev Python", "company": "Beta", "location": "Aix-en-Provence, France", "date": "2026-10-13"}]
DETAIL = {"id": "111", "title": "Dev full stack", "company": "Acme", "location": "Marseille, France", "seniority": "Entry level",
          "employmentType": None, "industries": None, "url": "https://www.linkedin.com/jobs/view/111", "description": "Python, SQL."}


class Cli(unittest.TestCase):
    def test_search_passes_what_where_and_days(self):
        with mock.patch.object(linkedin, "run_cli", return_value={"results": JOBS}) as run:
            self.assertEqual(linkedin.search("dev", "Marseille, France", 3), JOBS)
        self.assertEqual(run.call_args.args, ("search", "--location", "Marseille, France", "--jobage", "3", "--limit", "10", "--query", "dev"))

    def test_offer_text_has_header_and_description(self):
        with mock.patch.object(linkedin, "run_cli", return_value=DETAIL):
            text = linkedin.offer_text("111")
        self.assertEqual(text.splitlines()[:3], ["Dev full stack", "Acme · Marseille, France", "Seniority: Entry level"])
        self.assertTrue(text.endswith("Python, SQL."))

    def test_cli_error_becomes_a_readable_message(self):
        failed = subprocess.CompletedProcess([], 1, "", json.dumps({"error": "no location", "code": "NO_LOCATION"}))
        with mock.patch.object(linkedin, "bun", return_value="bun"), mock.patch("subprocess.run", return_value=failed):
            with self.assertRaisesRegex(linkedin.LinkedInError, "no location"):
                linkedin.search("dev", "", 3)

    def test_without_bun_it_says_how_to_install(self):
        with mock.patch.object(linkedin, "bun", return_value=None):
            with self.assertRaisesRegex(linkedin.LinkedInError, "make install"):
                linkedin.search("dev", "Marseille", 3)

    @unittest.skipUnless(linkedin.bun(), "needs bun")
    def test_real_cli_rejects_a_search_without_place(self):
        with self.assertRaisesRegex(linkedin.LinkedInError, "location"):
            linkedin.run_cli("search", "--query", "dev")


class OfferStep(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.profile = {"headline": "Dev", "city": "Marseille, France"}

    def test_chosen_linkedin_offer_is_saved_as_the_offer(self):
        prompter = ScriptedPrompter(texts=["Dev", "Marseille, France", "3"], selects=["linkedin", "222"])
        with mock.patch.object(linkedin, "search", return_value=JOBS) as search, \
                mock.patch.object(linkedin, "offer_text", return_value="Dev Python\nBeta"):
            path = job_search.ask_offer(prompter, self.profile, folder=self.folder)
        self.assertEqual(search.call_args.args, ("Dev", "Marseille, France", 3))
        self.assertEqual(Path(path).read_text(encoding="utf8"), "Dev Python\nBeta")

    def test_failure_or_no_choice_falls_back_to_a_file(self):
        prompter = ScriptedPrompter(texts=["", "", "abc", "offer.txt"], selects=["linkedin"])
        with mock.patch.object(linkedin, "search", side_effect=linkedin.LinkedInError("down")):
            self.assertEqual(job_search.ask_offer(prompter, self.profile, folder=self.folder), "offer.txt")
        self.assertTrue(any("down" in m for m in prompter.said))
        prompter = ScriptedPrompter(texts=["", "", "", "other.txt"], selects=["linkedin", "none"])
        with mock.patch.object(linkedin, "search", return_value=JOBS):
            self.assertEqual(job_search.ask_offer(prompter, self.profile, folder=self.folder), "other.txt")


if __name__ == "__main__":
    unittest.main()
