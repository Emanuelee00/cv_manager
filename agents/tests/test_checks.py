import unittest

from cvagents import checks


class Facts(unittest.TestCase):
    def test_extracts_numbers_urls_emails(self):
        facts = checks.extract_facts("30 des 46 commits, 0,34 s, https://github.com/x/y. mail a@b.it 2026")
        self.assertEqual(facts["numbers"], {"30", "46", "0.34", "2026"})
        self.assertEqual(facts["urls"], {"https://github.com/x/y"})
        self.assertEqual(facts["emails"], {"a@b.it"})

    def test_email_digits_and_url_digits_are_not_numbers(self):
        self.assertEqual(checks.extract_facts("a2@b.it https://x.com/1234")["numbers"], set())

    def test_compare_reports_added_and_removed(self):
        diff = checks.compare_facts("fatto in 3 mesi", "fatto in 4 mesi")
        self.assertEqual(diff, {"numbers": {"removed": ["3"], "added": ["4"]}})

    def test_identical_facts_give_empty_diff(self):
        self.assertEqual(checks.compare_facts("2 volte in 2026", "in 2026, due volte 2"), {})


class Invented(unittest.TestCase):
    def test_flags_numbers_missing_from_sources(self):
        self.assertEqual(checks.unsupported_numbers("12 progetti, 2025", ["2025 hackathon", "30 commit"]), ["12"])

    def test_no_sources_means_every_number_is_suspect(self):
        self.assertEqual(checks.unsupported_numbers("7", []), ["7"])


class Repeats(unittest.TestCase):
    def test_finds_repeated_significant_words_ignoring_accents_and_stopwords(self):
        found = checks.repeated_words("Docker et docker, Équipe équipe, avec avec, ok ok")
        self.assertEqual(found, {"docker": 2, "equipe": 2})

    def test_ignore_list(self):
        self.assertEqual(checks.repeated_words("Python et Python", ignore=["python"]), {})


class Sources(unittest.TestCase):
    def test_unknown_ids(self):
        self.assertEqual(checks.unknown_sources(["a", "b", "x"], ["a", "b"]), ["x"])


if __name__ == "__main__":
    unittest.main()
