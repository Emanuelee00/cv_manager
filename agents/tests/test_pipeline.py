import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from cvagents import render
from cvagents.db import connect, upsert_item
from cvagents.pipeline import context, cv_html, generate, humanize, keywords, lite_items, lite_profile, lite_review, review, text_tools, translate
from cvagents.pipeline.lang import detect_lang
from cvagents.pipeline.run import run_cv
from tests.helpers import FakeProvider, ScriptedPrompter

PROFILE = "NAME: Ada Rossi\nHEADLINE: Dev\nCITY: Lyon, France\nAGE: 26 ans\nLICENSE: B\nLINKS: https://github.com/ada · email ada@x.fr"


def cv_json(profile="Développeuse web à Lyon.", text="Sites WordPress pour 3 clients.", extra=None):
    items = [{"section": "experience", "title": "Dev web", "period": "2022 – 2024", "text": text, "source_id": "cv:1"},
             {"section": "education", "title": "Master", "period": "2020", "text": "Études à Lyon.", "source_id": "cv:3"}]
    return json.dumps({"headline": "Alternance dev web", "profile": profile, "items": items + (extra or []), "questions": []})


def database():
    conn = connect(":memory:")
    upsert_item(conn, "cv:1", "cv", "experience", "Dev web", "Acme 2022 – 2024. Sites WordPress pour 3 clients.")
    upsert_item(conn, "cv:3", "cv", "education", "Master", "Lyon 2020")
    upsert_item(conn, "manual:candidate-profile", "manual", "profile", "Anagrafica", PROFILE)
    return conn


KEYWORDS = json.dumps({"keywords": ["WordPress"]})
REVIEW = json.dumps({"score": 6, "problems": ["Profilo generico"], "fixes": ["Precisare il profilo"]})


class Generate(unittest.TestCase):
    def test_problems_found_by_code(self):
        conn = database()
        rows = conn.execute("SELECT * FROM items WHERE id LIKE 'cv:%'").fetchall()
        bad = generate.parse_cv(cv_json(text="Sites WordPress pour 99 clients, WordPress.", extra=[
            {"section": "project", "title": "X", "text": "y", "source_id": "cv:404"}]))
        found = " ".join(generate.find_problems(bad, rows, PROFILE))
        self.assertIn("cv:404", found)
        self.assertIn("99", found)
        self.assertIn("wordpress", found)

    def test_clean_cv_has_no_problems(self):
        conn = database()
        rows = conn.execute("SELECT * FROM items WHERE id LIKE 'cv:%'").fetchall()
        self.assertEqual(generate.find_problems(generate.parse_cv(cv_json()), rows, PROFILE), [])


class Humanize(unittest.TestCase):
    def test_rejects_changed_facts(self):
        cv = generate.parse_cv(cv_json())
        texts = humanize.texts_of(cv)
        bad = FakeProvider(json.dumps({"texts": [t.replace("3", "9") for t in texts]}))
        same, changed = humanize.humanize_cv(bad, cv, "A")
        self.assertEqual((same, changed), (cv, False))

    def test_accepts_same_facts(self):
        cv = generate.parse_cv(cv_json())
        good = FakeProvider(json.dumps({"texts": ["Nuovo profilo.", "Siti WordPress per 3 clienti.", "Master a Lione."]}))
        new, changed = humanize.humanize_cv(good, cv, "B")
        self.assertEqual((new["profile"], changed), ("Nuovo profilo.", True))


class Html(unittest.TestCase):
    def test_profile_parse_and_clickable_links(self):
        p = cv_html.parse_profile(PROFILE + "\nPHONES: vedi manual:phones")
        self.assertEqual((p["name"], p["license"], p["email"]), ("Ada Rossi", "B", "ada@x.fr"))
        page = cv_html.build_html(PROFILE, generate.parse_cv(cv_json()), "fr")
        self.assertIn('href="mailto:ada@x.fr"', page)
        self.assertIn("FORMATION", page)
        self.assertLess(page.index("FORMATION"), page.index("EXPÉRIENCE"))

    def test_language_detection(self):
        self.assertEqual(detect_lang("Nous cherchons une personne pour le développement avec des outils"), "fr")
        self.assertEqual(detect_lang("We are looking for you to build our tools with the team"), "en")
        self.assertEqual(detect_lang("Cerchiamo una persona per lo sviluppo con il nostro team"), "it")


class Lite(unittest.TestCase):
    def test_items_come_from_database_not_from_ai(self):
        conn = connect(":memory:")
        upsert_item(conn, "cv:1", "cv", "experience", "Dev web", "Acme\n2022 – 2024\nSites WordPress pour 3 clients.\nTag: WordPress",
                    {"org": "Acme", "period": "2022 – 2024"})
        upsert_item(conn, "manual:x", "manual", "interest", "Tiro con l'arco", "Pratica il tiro con l'arco.")
        items = {i["source_id"]: i for i in lite_items.build_items(conn.execute("SELECT * FROM items").fetchall())}
        self.assertEqual(items["cv:1"], {"section": "experience", "title": "Dev web, Acme", "period": "2022 – 2024",
                                         "text": "Sites WordPress pour 3 clients.", "source_id": "cv:1"})
        self.assertEqual(items["manual:x"]["text"], "Tiro con l'arco")

    def test_translation_is_rejected_when_facts_change(self):
        original = "Sites WordPress pour 3 clients dans la région de Lyon."
        self.assertEqual(translate.translate_text(FakeProvider("Websites for 9 clients in the Lyon region."), original, "en"), original)
        good = "Websites for 3 clients in the Lyon region."
        self.assertEqual(translate.translate_text(FakeProvider(good), original, "en"), good)

    def test_translation_skipped_when_archive_already_in_language(self):
        provider = FakeProvider()
        items = [{"section": "project", "title": "A", "text": "Nous cherchons une personne pour le développement avec des outils.",
                  "period": "", "source_id": "x"}]
        self.assertEqual(translate.translate_items(provider, items, "fr"), items)
        self.assertEqual(provider.calls, [])

    def test_translation_applies_to_project_texts_only(self):
        provider = FakeProvider("Un site de commerce en ligne pour trois clients.")
        items = [{"section": "project", "title": "A", "period": "", "source_id": "x",
                  "text": "Un sito di commercio online per tre clienti della regione."},
                 {"section": "interest", "title": "Viaggi", "text": "Viaggi", "period": "", "source_id": "y"}]
        out = translate.translate_items(provider, items, "fr")
        self.assertEqual(out[0]["text"], "Un site de commerce en ligne pour trois clients.")
        self.assertEqual(out[1]["text"], "Viaggi")

    def test_list_like_profile_is_rejected_and_falls_back_to_base_title(self):
        junk = json.dumps({"headline": "Dev", "profile": "Python, SQL, Docker, RAG, agents, cyber, Git, Linux, React, Node, API."})
        _, profile = lite_profile.write_profile(FakeProvider(junk, junk), "sys", "offre", PROFILE, [], "fr")
        self.assertEqual(profile, "Dev")
        self.assertTrue(lite_profile.looks_like_list("Python, SQL, Docker, RAG, agents, cyber, Git."))
        self.assertFalse(lite_profile.looks_like_list("Étudiante à Lyon. Elle cherche une alternance en développement web."))

    def test_keyword_tokens_split_phrases_and_drop_generic_words(self):
        self.assertEqual(keywords.keyword_tokens(["technologie Python", "API MCP", "compétence full stack", "python"]),
                         ["Python", "API", "MCP"])

    def test_excluded_projects_never_enter_the_cv(self):
        conn = database()
        upsert_item(conn, "gh:secret", "github", "repo", "secret", "Application WordPress privée pour un client", {"link": ""})
        upsert_item(conn, "manual:candidate-preferences", "manual", "preferences", "Preferenze", "x", {"excluded_ids": ["gh:secret"]})
        ids = [r["id"] for r in context.retrieve(conn, FakeProvider(KEYWORDS), "WordPress")]
        self.assertNotIn("gh:secret", ids)
        proposed = [o["row"]["id"] for o in lite_review.suggestions(conn, ["WordPress"], set())]
        self.assertNotIn("gh:secret", proposed)

    def test_overclaiming_headline_and_third_person_are_removed(self):
        reply = json.dumps({"headline": "Experte en IA", "profile": "Ada Rossi est développeuse. Je construis des sites web à Lyon."})
        headline, profile = lite_profile.write_profile(FakeProvider(reply), "sys", "offre", PROFILE, [], "fr")
        self.assertEqual(headline, "Dev")
        self.assertEqual(profile, "Je construis des sites web à Lyon.")

    def test_education_is_sorted_most_recent_first(self):
        conn = connect(":memory:")
        for i, period in enumerate(("2015 – 2020", "in corso", "2025 – 2027 (previsto)", "2020 – 2024")):
            upsert_item(conn, f"cv:{i}", "cv", "education", f"Scuola {i}", f"Studi {i}", {"period": period})
        items = lite_items.build_items(conn.execute("SELECT * FROM items ORDER BY id").fetchall())
        self.assertEqual([i["period"] for i in items], ["2025 – 2027 (previsto)", "in corso", "2020 – 2024", "2015 – 2020"])

    def test_same_story_is_not_told_twice(self):
        laurea = {"section": "education", "title": "Laurea, Milano", "text": "Erasmus all'UCAM Murcia (2022).", "period": "", "source_id": "a"}
        erasmus = {"section": "education", "title": "Erasmus — UCAM Murcia", "text": "Erasmus a Murcia.", "period": "", "source_id": "b"}
        self.assertTrue(lite_items.already_told(erasmus, [laurea]))
        self.assertFalse(lite_items.already_told(laurea, [erasmus]))

    def test_curated_entries_outrank_repos(self):
        conn = connect(":memory:")
        upsert_item(conn, "gh:repo", "github", "repo", "repo", "Docker Docker Docker per una demo")
        upsert_item(conn, "cv:hack", "cv", "hackathon", "Hackathon", "Docker in produzione")
        ids = [r["id"] for r in context.retrieve(conn, FakeProvider(json.dumps({"keywords": ["Docker"]})), "Docker")]
        self.assertEqual(ids[0], "cv:hack")

    def test_translation_artifacts_are_removed_and_marked(self):
        items = [{"section": "project", "title": "A", "period": "", "source_id": "x", "text": "Un sito di commercio online per tre clienti della regione."}]
        out = translate.translate_items(FakeProvider("Un site de commerce en ligne pour trois clients. /no_translate"), items, "fr")
        self.assertEqual(out[0]["text"], "Un site de commerce en ligne pour trois clients.")
        self.assertTrue(out[0]["translated"])

    def test_repo_text_prefers_description_then_readme(self):
        self.assertEqual(text_tools.repo_text("Interface web pour suivre ses dépenses\nLinguaggi: JS"), "Interface web pour suivre ses dépenses")
        body = "\nLinguaggi: Python\nCommit:\nfix\nREADME:\n# Titre\n\nCe programme trie une pile de nombres entiers avec un jeu limité d'opérations."
        self.assertTrue(text_tools.repo_text(body).startswith("Ce programme trie"))

    def test_profile_drops_sentences_with_invented_numbers(self):
        reply = json.dumps({"headline": "Dev", "profile": "Développeuse à Lyon. Elle a géré 99 clients."})
        _, profile = lite_profile.write_profile(FakeProvider(reply), "sys", "offre", PROFILE, [], "fr")
        self.assertEqual(profile, "Développeuse à Lyon.")

    def test_review_is_done_by_code_and_suggests_real_entries(self):
        conn = database()
        upsert_item(conn, "cv:9", "cv", "project", "Robot Docker", "Conteneurs Docker pour un robot")
        cv = {"items": [lite_items.row_to_item(conn.execute("SELECT * FROM items WHERE id='cv:1'").fetchone())]}
        score, problems, options = lite_review.review(conn, FakeProvider(json.dumps({"keywords": ["WordPress", "Docker", "Kubernetes"]})),
                                                      "offre", review.cv_as_text({"profile": "", **cv}), {"cv:1"})
        self.assertEqual(score, 3)
        self.assertEqual([o["row"]["id"] for o in options], ["cv:9"])
        self.assertTrue(any("Kubernetes" in p and "nothing in your archive" in p for p in problems))
        self.assertEqual(lite_review.add_option(cv, options[0])["items"][-1]["source_id"], "cv:9")


@unittest.skipUnless(shutil.which("chromium-browser") and shutil.which("pdfinfo"), "serve Chromium e pdfinfo")
class EndToEnd(unittest.TestCase):
    def test_user_can_refuse_file_creation_after_preview(self):
        conn = database()
        provider = FakeProvider(KEYWORDS, json.dumps({"headline": "Dev", "profile": "Développeuse web à Lyon."}), KEYWORDS)
        prompter = ScriptedPrompter(confirms=[False, False])
        files, _ = run_cv(prompter, conn, provider, "WordPress", folder=tempfile.mkdtemp())
        self.assertEqual(files, [])
        preview = next(m for m in prompter.said if "PREVIEW" in m)
        self.assertIn("check that every sentence is true", preview)

    def test_lite_run_produces_one_page_pdf_without_touching_database(self):
        conn = database()
        before = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        replies = [KEYWORDS, json.dumps({"headline": "Alternance dev web", "profile": "Développeuse web à Lyon."}), KEYWORDS]
        provider = FakeProvider(*replies)
        folder = tempfile.mkdtemp()
        files, cv = run_cv(ScriptedPrompter(confirms=[False]), conn, provider, "Cerchiamo un développeur WordPress",
                           folder=folder, formats=("pdf", "docx"))
        self.assertEqual(render.page_count(files[0]), 1)
        self.assertTrue(zipfile.is_zipfile(files[1]))
        self.assertEqual(cv["profile"], "Développeuse web à Lyon.")
        self.assertEqual(cv["headline"], "Alternance dev web")
        self.assertEqual({i["section"] for i in cv["items"]}, {"experience", "education"})
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], before)

    def test_long_cv_is_trimmed_to_one_page(self):
        extra = [{"section": "project", "title": f"Projet {i}", "text": "Texte " * 120, "source_id": "cv:1"} for i in range(12)]
        cv = generate.parse_cv(cv_json(extra=extra))
        _, pdf, kept, dropped, pages = cv_html.fit_one_page(PROFILE, cv, "fr", tempfile.mkdtemp())
        self.assertEqual(pages, 1)
        self.assertTrue(dropped)


if __name__ == "__main__":
    unittest.main()
