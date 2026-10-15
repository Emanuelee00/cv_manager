import unittest

from cvagents import ats_score
from cvagents.layouts import STYLES, reading_order, render_html, sidebar
from cvagents.layouts.common import linkify
from cvagents.layouts.text_parts import bullets, language_levels, skill_tags
from cvagents.onboarding.manual_entries import collect_entries
from tests.helpers import ScriptedPrompter

PROFILE = "NAME: Ada Rossi\nHEADLINE: Dev\nCITY: Lyon, France\nLINKS: https://github.com/ada https://linkedin.com/in/ada · email ada@x.fr"
CV = {"headline": "Alternance dev", "profile": "Développeuse web.", "items": [
    {"section": "experience", "title": "Dev", "period": "2023", "text": "Sites WordPress. Migration PHP 7 vers 8; SEO local.", "source_id": "a"},
    {"section": "skill", "title": "Skills", "text": "Python, SQL · Docker. Git", "source_id": "b"},
    {"section": "language", "title": "Langues", "text": "italien (langue maternelle) · anglais (courant, C1/C2) · russe (notions)", "source_id": "c"},
    {"section": "interest", "title": "Voyages", "text": "Voyages", "source_id": "d"}]}


class Links(unittest.TestCase):
    def test_web_addresses_in_texts_become_clickable_links(self):
        out = linkify("Code sur github.com/ada/app. Aussi https://ada.github.io/portfolio (voir BENCHMARK.md)")
        self.assertIn('<a href="https://github.com/ada/app">github.com/ada/app</a>.', out)
        self.assertIn('<a href="https://ada.github.io/portfolio">https://ada.github.io/portfolio</a>', out)
        self.assertNotIn("<a href=\"https://BENCHMARK", out)
        self.assertEqual(linkify("a < b & c"), "a &lt; b &amp; c")

    def test_an_entry_without_title_is_a_plain_line_without_bullet_or_bold(self):
        cv = {"headline": "Dev", "profile": "Ok.", "items": [{"section": "project", "title": "", "text": "Tout est sur mon GitHub", "source_id": "x"}]}
        html = render_html("classic", PROFILE, cv, "fr")
        self.assertIn('<li style="list-style:none;margin:7px 0 5px">Tout est sur mon GitHub</li>', html)


class ModernKeepsEverything(unittest.TestCase):
    def test_no_sentence_and_no_skill_is_cut_and_no_empty_bullet_is_drawn(self):
        text = " ".join(f"Phrase numéro {n} de la description." for n in range(1, 8))
        cv = {"headline": "Dev", "profile": "Ok.", "items": [
            {"section": "project", "title": "Gros projet", "text": text, "source_id": "a"},
            {"section": "education", "title": "Diplôme", "period": "2020", "text": "", "source_id": "b"},
            {"section": "skill", "title": "S", "text": ", ".join(f"Outil{n}" for n in range(30)), "source_id": "c"}]}
        page = render_html("modern", PROFILE, cv, "fr")
        self.assertIn("Phrase numéro 7 de la description.", page)
        self.assertIn("Outil29", page)
        self.assertNotIn("<li></li>", page)


class LinkedinLabel(unittest.TestCase):
    def test_the_automatic_code_is_hidden_in_the_label_but_kept_in_the_link(self):
        from cvagents.layouts.common import contacts
        p = {"phone": "", "email": "", "links": ["https://www.linkedin.com/in/ada-rossi-680a2b417", "https://www.linkedin.com/in/ada-rossi"]}
        self.assertEqual([(k, label, href) for k, label, href in contacts(p)],
                         [("linkedin", "linkedin.com/in/ada-rossi", "https://www.linkedin.com/in/ada-rossi-680a2b417"),
                          ("linkedin", "linkedin.com/in/ada-rossi", "https://www.linkedin.com/in/ada-rossi")])


class TextParts(unittest.TestCase):
    def test_bullets_skills_and_language_levels(self):
        self.assertEqual(bullets("Sites WordPress. Migration PHP 7 vers 8; SEO local."), ["Sites WordPress", "Migration PHP 7 vers 8", "SEO local"])
        self.assertEqual(skill_tags(["Python, SQL · Docker. Git", "python"]), ["Python", "SQL", "Docker", "Git"])
        self.assertEqual(language_levels(CV["items"][2]["text"]),
                         [("Italien", "langue maternelle", 100), ("Anglais", "C1/C2", 95), ("Russe", "notions", 20)])


class Modern(unittest.TestCase):
    def test_main_column_comes_before_the_sidebar_in_the_file(self):
        page = render_html("modern", PROFILE, CV, "fr")
        self.assertLess(page.index("<main>"), page.index("<aside>"))
        self.assertIn("Ada <b>ROSSI</b>", page)
        self.assertIn('style="width:100%"', page)
        self.assertIn('href="mailto:ada@x.fr"', page)
        self.assertIn("<svg", page)

    def test_reading_order_lists_main_then_sidebar_sections(self):
        self.assertEqual(reading_order("modern", CV), ["profile", "experience", "skill", "language", "interest"])
        self.assertEqual(reading_order("classic", CV), ["profile", "experience", "skill", "language", "interest"])
        self.assertEqual(sidebar.name_html("Cher"), "<b>CHER</b>")


class Score(unittest.TestCase):
    def test_best_possible_scores_rank_the_styles(self):
        best = {s: ats_score.best_possible(STYLES[s]) for s in STYLES}
        self.assertEqual(best, {"classic": 100, "minimal": 100, "modern": 70})
        self.assertEqual(ats_score.score([("ats.headings", {})], STYLES["modern"]), 50)


class FromScratch(unittest.TestCase):
    def test_entries_typed_by_hand_are_kept_only_after_confirmation(self):
        prompter = ScriptedPrompter(selects=["experience", "interest", "done"], texts=["Dev", "Acme, Lyon", "2023", "Sites", "Ski"],
                                    confirms=[True, False])
        entries = collect_entries(prompter)
        self.assertEqual(entries, [{"type": "experience", "title": "Dev", "org": "Acme, Lyon", "period": "2023", "description": "Sites"}])


if __name__ == "__main__":
    unittest.main()
