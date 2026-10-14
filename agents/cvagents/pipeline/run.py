"""Il percorso `cvagents cv`: genera, controlla, valuta, migliora, rende naturale, PDF in una pagina."""
from cvagents.pipeline import context, generate, humanize, improve, review
from cvagents.pipeline.review import cv_as_text
from cvagents.pipeline.lang import detect_lang
from cvagents.pipeline.lite_run import build_lite, lite_loop
from cvagents.pipeline.output import write_files
from cvagents.prompts import load_agent_prompt

LITE_SECTIONS = ("Stile",)
GOOD_SCORE = 8


def build_cv(prompter, provider, system, offer, rows, candidate, lang):
    """Prima stesura, domande al candidato, correzione dei problemi trovati dal codice."""
    ctx = context.format_context(rows)
    with prompter.step("Generatore: prima stesura"):
        cv = generate.generate(provider, system, offer, ctx, candidate, lang)
    answers = "\n".join(f"- {q}: {prompter.text(q)}" for q in cv["questions"])
    if answers.replace("\n", "").strip("- "):
        with prompter.step("Generatore: stesura con le tue risposte"):
            cv = generate.generate(provider, system, offer, ctx, candidate, lang, answers)
    for _ in range(2):
        problems = generate.find_problems(cv, rows, candidate)
        if not problems:
            break
        with prompter.step(f"Correzione: {len(problems)} problemi trovati dal codice"):
            cv = generate.repair(provider, system, cv, problems, lang)
    return cv


def improve_loop(prompter, provider, system, offer, cv, lang):
    """Modo completo: HR e manager separati, fino a 3 giri; l'utente sceglie cosa migliorare."""
    for round_number in range(3):
        reviews = review.review_full(provider, offer, cv, prompter.step)
        with prompter.step("Sintesi dei pareri"):
            result = improve.merge_reviews(provider, reviews)
        prompter.say(f"\nValutazione: {result['score']}/10\n" + "\n".join(f"- {p}" for p in result["problems"]))
        if result["score"] >= GOOD_SCORE and not result["problems"]:
            break
        chosen = prompter.checkbox("Quali miglioramenti applico?", [(f, f) for f in result["fixes"]]) if result["fixes"] else []
        if not chosen:
            break
        with prompter.step(f"Riscrittura: {len(chosen)} miglioramenti"):
            cv = improve.apply_fixes(provider, system, cv, chosen, lang)
        if round_number < 2 and not prompter.confirm("Un altro giro di valutazione?"):
            break
    return cv


def natural_pass(prompter, provider, cv):
    """Passata di naturalezza: sempre su richiesta, con canale A (persona) o B (portale)."""
    if not prompter.confirm("Vuoi una passata per rendere il testo più naturale?", default=not provider.local):
        return cv
    channel = prompter.select("Chi leggerà il CV?", [("A", "Una persona (mail, contatto diretto)"), ("B", "Un portale o LinkedIn")])
    with prompter.step(f"Humanizer (modo {channel})"):
        new_cv, note = humanize.humanize_cv(provider, cv, channel)
    prompter.say(note)
    return new_cv


def produce(prompter, candidate, cv, lang, folder, formats):
    """Anteprima nel terminale, conferma, poi i file: PDF sempre adattato a una pagina, Word dallo stesso contenuto."""
    prompter.say("\nANTEPRIMA\n" + cv_as_text(cv))
    if not prompter.confirm("Creo il CV con questo contenuto?"):
        return []
    with prompter.step("File: PDF in una pagina" + (" e Word" if "docx" in formats else "")):
        files, pages, dropped = write_files(candidate, cv, lang, folder, formats)
    prompter.say(f"File: {', '.join(map(str, files))} (PDF: {pages} pagina/e)" + (f"\nTolte per stare in una pagina: {', '.join(dropped)}" if dropped else ""))
    return files


def run_cv(prompter, conn, provider, offer, lang=None, folder="output", formats=("pdf",)):
    """Ritorna (file creati, cv finale). Nessuna scrittura nel database."""
    lang = lang or detect_lang(offer)
    prompter.say(f"AI: {provider.describe()} · lingua del CV: {lang} · modo: {'lite' if provider.local else 'completo'}")
    system = load_agent_prompt("cv-generator", None if not provider.local else LITE_SECTIONS)
    candidate = context.candidate_text(conn)
    if provider.local:
        cv = lite_loop(prompter, conn, provider, offer, build_lite(prompter, provider, system, conn, offer, lang))
    else:
        with prompter.step("Ricerca nell'archivio"):
            rows = context.retrieve(conn, provider, offer)
        cv = improve_loop(prompter, provider, system, offer, build_cv(prompter, provider, system, offer, rows, candidate, lang), lang)
    cv = natural_pass(prompter, provider, cv)
    return produce(prompter, candidate, cv, lang, folder, formats), cv
