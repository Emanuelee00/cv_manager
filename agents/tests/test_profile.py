import unittest

from cvagents.db import connect, get_item
from cvagents.onboarding.ask_profile import ask_profile
from tests.helpers import ScriptedPrompter
from cvagents.onboarding.profile import preferences_body, profile_body, save_profile

DATA = {"name": "Ada Rossi", "headline": "Développeuse web", "city": "Lyon, France", "email": "ada@x.fr",
        "phones": "+33 6 00 00 00 00", "links": "https://github.com/ada", "github_login": "ada",
        "age": "", "citizenship": "italienne (UE)", "license": "B", "photo": ""}


class Profile(unittest.TestCase):
    def test_body_has_only_given_optional_fields(self):
        body = profile_body(DATA)
        self.assertIn("NOME: Ada Rossi", body)
        self.assertIn("PATENTE: B", body)
        self.assertNotIn("ETÀ", body)
        self.assertNotIn("FOTO", body)

    def test_preferences_list_what_to_show(self):
        self.assertIn("cittadinanza, patente", preferences_body(DATA))

    def test_save_writes_three_items(self):
        conn = connect(":memory:")
        self.assertEqual(save_profile(conn, DATA), "Ada Rossi")
        for item_id in ("manual:profilo-candidato", "manual:preferenze-candidato", "manual:profilo-telefoni"):
            self.assertIsNotNone(get_item(conn, item_id))

    def test_ask_profile_insists_on_name(self):
        answers = ["", "Dev", "Lyon", "a@b.c", "123", "", "", "Ada", "", "", "", ""]
        data = ask_profile(ScriptedPrompter(texts=answers))
        self.assertEqual(data["name"], "Ada")

    def test_ask_profile_uses_existing_as_default(self):
        data = ask_profile(ScriptedPrompter([]), existing=DATA)
        self.assertEqual(data["city"], "Lyon, France")


if __name__ == "__main__":
    unittest.main()
