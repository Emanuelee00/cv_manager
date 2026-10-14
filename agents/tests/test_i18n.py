import re
import string
import unittest
from pathlib import Path

from cvagents import i18n
from cvagents.messages import MESSAGES
from cvagents.onboarding.manual_entries import KINDS
from tests.helpers import ScriptedPrompter

SOURCE = Path(__file__).resolve().parents[1] / "cvagents"
DYNAMIC = {"profile.": ("name", "headline", "city", "email", "phones", "links", "github_login", "age", "citizenship", "license", "photo"),
           "ai.choice_": ("cli", "api", "local"), "settings.github_": ("gh", "public", "skip"),
           "style.": ("classic", "modern", "minimal"), "style.hint_": ("classic", "modern", "minimal"),
           "manual.kind_": KINDS, "manual.title_": KINDS,
           "manual.description_": ("experience", "education", "project", "skill", "language")}


def used_keys():
    text = "\n".join(p.read_text(encoding="utf8") for p in SOURCE.rglob("*.py"))
    keys = set(re.findall(r"""["']((?:common|start|ai|profile|cv|github|live|step|run|review|settings|cmd|doctor|ollama|llm|render|ats|style|styles|manual|jobs)\.[a-z_]+)["']""", text))
    keys |= {prefix + suffix for prefix, suffixes in DYNAMIC.items() for suffix in suffixes}
    files = {"css", "docx", "html", "pdf", "json", "txt", "md", "png", "db", "com", "xml"}
    return {k for k in keys if not k.endswith((".", "_")) and k.rsplit(".", 1)[-1] not in files}


def placeholders(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


class Catalog(unittest.TestCase):
    def test_every_used_key_exists_in_all_four_languages(self):
        for key in sorted(used_keys()):
            self.assertIn(key, MESSAGES, key)
            self.assertEqual(set(MESSAGES[key]), {"en", "fr", "it", "es"}, key)
            self.assertTrue(all(MESSAGES[key].values()), key)

    def test_placeholders_match_across_languages(self):
        for key, texts in MESSAGES.items():
            self.assertEqual(len({frozenset(placeholders(v)) for v in texts.values()}), 1, key)


class Language(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("en")

    def test_t_uses_current_language_and_fills_values(self):
        i18n.set_language("es")
        self.assertEqual(i18n.t("run.score", score=7), "Evaluación: 7/10")
        i18n.set_language("xx")
        self.assertEqual(i18n.language(), "en")

    def test_choose_language_is_asked_in_all_languages_with_saved_first(self):
        prompter = ScriptedPrompter(selects=["fr"])
        self.assertEqual(i18n.choose_language(prompter, saved="it"), "fr")
        self.assertIn("Langue", prompter.asked[0])
        self.assertEqual(i18n.t("common.none"), "aucun")


if __name__ == "__main__":
    unittest.main()
