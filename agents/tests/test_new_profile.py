import tempfile
import unittest
from pathlib import Path

from cvagents.new_profile import find_or_create


class NewProfileTest(unittest.TestCase):
    def test_creates_then_finds_ignoring_accents_and_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(find_or_create("Chloé Duguy", tmp), "chloe")
            self.assertEqual(find_or_create("CHLOE duguy", tmp), "chloe")
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)

    def test_same_first_name_other_person_gets_own_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            find_or_create("Chloé Duguy", tmp)
            self.assertEqual(find_or_create("Chloé Martin", tmp), "chloe_martin")


if __name__ == "__main__":
    unittest.main()
