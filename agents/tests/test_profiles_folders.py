import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cvagents import profile


class ProfileFoldersTest(unittest.TestCase):
    def names(self, folders, env=""):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(profile, "PROFILES", Path(tmp)):
            for f in folders:
                (Path(tmp) / f).mkdir()
            with mock.patch.dict(os.environ, {"CVAGENTS_PROFILE": env}):
                return profile.profile_name()

    def test_env_wins(self):
        self.assertEqual(self.names(["a", "b"], "b"), "b")

    def test_single_profile_is_used(self):
        self.assertEqual(self.names(["a"]), "a")

    def test_none_is_default(self):
        self.assertEqual(self.names([]), "default")

    def test_several_without_choice_stops(self):
        with self.assertRaises(SystemExit):
            self.names(["a", "b"])


if __name__ == "__main__":
    unittest.main()
