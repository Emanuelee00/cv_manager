# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. These bias toward caution over speed; for trivial tasks, use judgment.

## Project

CV Base: personal archive of experiences for CVs. One Node service with two faces: a web page (`public/`) and an MCP server Claude connects to.

- Node >= 20, ES modules, Express 5, `@modelcontextprotocol/sdk`, `zod`.
- `server.js` HTTP + MCP, `store.js` persistence (`cvbase.json` in `DATA_DIR`), `seed.js` initial entries, `test.js` tests.
- Frontend is vanilla JS/CSS in `public/` (`app.js`, `index.html`, `style.css`, `sw.js` service worker). No build step.
- Run: `npm start` (needs `APP_PASSWORD` and `MCP_SECRET`). Test: `npm test`.
- User-facing text is in Italian.

## agents/ (CV e lettere)

Python (uv, solo libreria standard) in `agents/cvagents/`: base dati personale SQLite con ricerca FTS5 (`db.py`, `search.py`), import del CV (`importer.py`), lettura GitHub con `gh` (`github.py`, `repo_content.py`), render PDF e controllo pagine (`render.py`). Comandi: `cd agents && uv run python -m cvagents <import|add|github-sync|github-deep|search|show|stats|render>`. Test: `cd agents && uv run python -m unittest discover -s tests -t .`.

Agenti in `.claude/agents/` (si caricano riaprendo Claude Code): `cv-generator`, `hr-reviewer`, `manager`, `humanizer`, `letter-writer`, `humanizer-letter`, `style-copier`. Orchestratori come skill in `.claude/skills/`: `/cv-loop` e `/letter-flow` (una skill, non un agente, perché un agente non può chiamare altri agenti né fare domande all'utente).

Regole d'oro: i fatti vengono solo dal database; nessuna scrittura nel database senza ok dell'utente; mai inventare numeri o risultati; i punti incerti diventano domande; un agente = un compito; dati personali (foto, `agents/data/`, `agents/output/`) mai in git.

## 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what's confusing, ask.

## 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it. Would a senior engineer call it overcomplicated? Simplify.
- Max 5 functions per file/page. Aim for 25 lines per function (30 max).
  The principle behind the number: a function does ONE thing, fits on one screen, and stays at one level of abstraction. If far over, split by responsibility, never just to hit the number.
- Before adding a library (zod is already in use), ask the user first. Prefer reliable, well-known libraries over hand-rolled code once approved.

## 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

- Don't "improve" adjacent code, comments, or formatting. Don't refactor what isn't broken.
- Match existing style, even if you'd do it differently.
- Unrelated dead code: mention it, don't delete it.
- Remove imports/variables/functions that YOUR changes made unused; nothing pre-existing.
- Every changed line must trace directly to the user's request.
- If something you want to write is deprecated (check the console), rethink and use the current API.
- With multiple problems, make a plan and fix them step by step, not all at once.

## 4. Goal-Driven Execution

Define success criteria. Loop until verified.

- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Refactor X" → tests pass before and after.

For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]

## 5. Structure & Tooling

Organize by responsibility. Keep it flat until size demands otherwise.

- Group modules into a folder only when it grows past a few files or a clear responsibility emerges. Never create a folder to hit a number.
- Imports at the top of each file. Remove unused ones. No imports inside functions unless avoiding a genuine circular dependency.
- A folder with 2+ modules gets an `index.js` re-exporting ONLY what other folders import. From outside, import via `index.js`; inside, modules import each other directly.
- No import cycles. If two packages depend on each other, first move the misplaced module; otherwise keep the one offending import direct and say why.
- Never hardcode a route string at more than one call site: define it once as a named constant. A route with a dynamic segment gets one builder function (e.g. `entryRoute(id)`) next to its constant.
- Tests import files directly.
- If Python is ever added: use `uv`, and each package gets an `__init__.py` (minimal, public API only).
