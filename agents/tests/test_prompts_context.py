import json
import unittest

from cvagents import prompts
from cvagents.db import connect, upsert_item
from cvagents.pipeline import context, keywords
from tests.helpers import FakeProvider


class Prompts(unittest.TestCase):
    def test_agent_prompt_has_no_frontmatter_and_starts_with_no_tools_notice(self):
        text = prompts.load_agent_prompt("cv-generator")
        self.assertTrue(text.startswith("MODALITÀ SENZA STRUMENTI"))
        self.assertNotIn("tools: Bash", text)

    def test_sections_filter_by_prefix(self):
        text = prompts.load_agent_prompt("cv-generator", sections=("Stile", "Se non sei sicuro"))
        self.assertIn("## Stile", text)
        self.assertIn("## Se non sei sicuro", text)
        self.assertNotIn("## Standard francesi", text)

    def test_split_sections(self):
        parts = prompts.split_sections("intro\n## A\nuno\n## B\ndue")
        self.assertEqual([t for t, _ in parts], ["", "A", "B"])


class Context(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        upsert_item(self.conn, "cv:1", "cv", "experience", "Dev WordPress", "Siti WordPress e SEO")
        upsert_item(self.conn, "cv:2", "cv", "project", "Robot", "Progetto di robotica")
        upsert_item(self.conn, "cv:3", "cv", "education", "Master", "Lione 2020")
        upsert_item(self.conn, "manual:lettera", "manual", "cover_letter", "Lettera WordPress", "WordPress")

    def test_keywords_fallback_when_ai_fails(self):
        words = keywords.keywords(FakeProvider("non json"), "Cerchiamo esperienza con WordPress e Docker")
        self.assertIn("WordPress", words)

    def test_retrieve_ranks_by_keywords_skips_letters_and_adds_fixed(self):
        provider = FakeProvider(json.dumps({"keywords": ["WordPress", "SEO"]}))
        ids = [r["id"] for r in context.retrieve(self.conn, provider, "offerta")]
        self.assertEqual(ids[0], "cv:1")
        self.assertNotIn("manual:lettera", ids)
        self.assertIn("cv:3", ids)
        self.assertNotIn("cv:2", ids)

    def test_candidate_text_and_format(self):
        upsert_item(self.conn, "manual:profilo-candidato", "manual", "profile", "Anagrafica", "NOME: Ada")
        self.assertEqual(context.candidate_text(self.conn), "NOME: Ada")
        rows = self.conn.execute("SELECT * FROM items WHERE id='cv:1'").fetchall()
        self.assertIn("[cv:1] (experience) Dev WordPress", context.format_context(rows))


if __name__ == "__main__":
    unittest.main()
