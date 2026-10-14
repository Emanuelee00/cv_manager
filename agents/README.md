# CV Agents: a CV tailored to every job offer

Builds a CV for one specific job offer using **only true facts about you**, kept in a personal archive on your computer. It works with Claude (Claude Code or an API key) or with a free local model, without any key. The interface speaks English, French, Italian and Spanish.

## Quick start

You need [uv](https://docs.astral.sh/uv/) (it installs Python by itself) and `make`. For the PDF you need Chromium or Chrome; to read CVs in PDF you need `pdftotext` (poppler). Word needs nothing.

```sh
git clone https://github.com/Emanuelee00/cv_manager.git
cd cv_manager
make run
```

The first `make run` asks the **language** (English, Français, Italiano, Español) and then guides you step by step. After that, `make run` runs everything again with your saved choices. `make run OFFER=other.txt` uses another offer with the same choices. Other commands: `make doctor` (what you have and what is missing), `make start` (do the guided path again), `make test`.

### Do you have Claude Code? Do it all in the chat

Open the `cv_manager` folder in Claude Code (terminal or the VS Code panel) and type:

```
/cv-start
```

Claude asks the questions, reads your CV, connects GitHub, builds the CV for the offer, **shows you a preview** and, once you confirm, creates the **PDF or Word**. No key to configure.

### In the terminal: what `make run` asks the first time

1. **Language** of the interface.
2. **Which AI to use.** Three choices, always shown with their state:
   - **Claude Code**: uses your login, no key;
   - **Claude with an API key**: the key is typed hidden and never saved to disk;
   - **Free local model**: the program picks a Qwen3 model that fits your RAM, tells you its size and downloads it with Ollama. Your data stays on your computer.
3. **Your details**: name, title, city, contacts; age, citizenship, driving licence and photo are optional.
4. **Your CV** (PDF, Word, text or pasted): the AI extracts the entries and **you choose which to keep**. Nothing is saved without your OK.
5. **GitHub**: with the `gh` CLI (private repos too), public repos only, or not at all.
6. **The offer and the format**: PDF, Word or both.

While the agents work you see a **live panel** (steps, time, the text the AI is writing). Before the files are created you see a **preview** and confirm. At the end you get the saved choices and the command to run it all again.

## Claude or local model?

| | Local model (Ollama) | Claude |
|---|---|---|
| Cost | free | your subscription or pay per use |
| Privacy | everything stays on your computer | texts are sent to the service |
| Quality | safe on facts, simpler style | much better |
| Flow | **lite**: code picks the entries, the AI translates and writes the profile, code does the review | **full**: recruiter and manager separately, up to 3 improvement rounds, humanizer |

With the local model, sections, titles and dates come from your archive, and each translation is accepted only if numbers and links stay identical; machine-translated entries are marked in the preview so you can reread them. A bigger model (more RAM) writes better text.

## ATS (applicant tracking systems)

Many CVs are read by software first. The CV follows the rules sources agree on ([France Travail](https://www.francetravail.fr/candidat/vos-recherches/preparer-votre-candidature/cv-lettre-de-motivation-e-mail/logiciels-de-recrutement-ats-ada.html), [Jobseeker](https://www.jobseeker.com/fr/cv/conseils/cv-ats)): one column, no tables or text boxes, contacts in the body, standard section titles, common fonts, real text (not images), the offer's keywords with its exact wording, no arrows or special symbols. After every CV the program reads the PDF as plain text, like an ATS, and tells you whether name, email and section titles come out right.

## Without sudo (shared computers, schools)

When you choose the local model on Linux, the program can download Ollama into a folder of yours. By hand: `cd agents && uv run cvagents doctor --install-here ~/ollama --pull` (add `--models-dir /path/with/space` to keep models elsewhere). A model weighs between 1.4 and 9 GB.

## Commands (from `agents/`, with `uv run cvagents ...`)

| Command | What it does |
|---|---|
| `doctor` | RAM, suggested model, Ollama, Claude |
| `start` | guided path, saves the choices |
| `run [offer.txt]` | runs everything again with the saved choices |
| `cv <offer.txt> --format pdf docx` | CV choosing the AI now |
| `search "words"` / `show <id>` / `list --kind <kind>` | search and read your archive |
| `add <kind> <title> <text>` | add an entry by hand |
| `exclude <id>` (`--undo`) | never use an entry again (or allow it back) |
| `github-sync` / `github-public <user>` | read your repos |
| `build <cv.json> --format pdf docx` | files from a ready CV (used by `/cv-start`) |

## Privacy

Archive, choices, photo and created files live in `agents/data/` and `agents/output/`, which **never go to git**. API keys are never written to disk.

## Tests

```sh
make test
```
