# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. These bias toward caution over speed; for trivial tasks, use judgment.

## Project

CV Base: personal archive of experiences for CVs. One Node service with two faces: a web page (`public/`) and an MCP server Claude connects to.

- Node >= 20, ES modules, Express 5, `@modelcontextprotocol/sdk`, `zod`.
- `server.js` HTTP + MCP, `store.js` persistence (`cvbase.json` in `DATA_DIR`), `seed.js` initial entries, `test.js` tests.
- Frontend is vanilla JS/CSS in `public/` (`app.js`, `index.html`, `style.css`, `sw.js` service worker). No build step.
- Run: `npm start` (needs `APP_PASSWORD` and `MCP_SECRET`). Test: `npm test`.
- User-facing text is in Italian.

## agents/ (CVs and cover letters)

Python (uv; external dependencies: `questionary`, `rich`, `pillow`, `rembg`) in `agents/cvagents/`. Guide for people who clone the repo: [agents/README.md](agents/README.md). Everything is in English; user-facing messages go through `i18n.t()` with the catalog in `messages.py` (en, fr, it, es).
- Archive: `db.py`, `search.py` (SQLite + FTS5), `importer.py`, GitHub (`github.py` with `gh`, `github_public.py` without keys).
- AI: `llm/` (local Ollama, Claude API, Claude Code via `claude -p`), `local_setup.py` and `ollama_install.py` (model by RAM, install without sudo).
- Offers: `linkedin.py` calls the original `agents/linkedin-search/` CLI (TypeScript on bun, MIT, copied from ai-job-search: do not edit it); `onboarding/job_search.py` asks what, where and how many days. `make install` (run by `make run`) installs uv and bun without sudo.
- Photo: `photo/camera.py` (local page in the browser, camera), `photo/retouch.py` (rembg + Pillow; run as `python -m cvagents.photo.retouch` so rembg stays out of the other commands; model in `data/models`), `onboarding/photo_step.py`.
- Path: `onboarding/` (`make run` the first time = `cvagents start`), `pipeline/` (full mode with Claude; lite mode for small models where code picks the entries and checks the facts), `word/` (hand-written .docx), `render.py` (PDF and pages), `checks.py` (deterministic checks), `ats.py` (ATS checks), `live.py` (Rich live view).
- Commands in `commands/` (one SPEC table per module). Tests: `cd agents && uv run python -m unittest discover -s tests -t .`.

Agents in `.claude/agents/` (generic: the candidate is read from `manual:candidate-profile`). Skills: `/cv-start` (everything inside Claude Code, with preview), `/cv-loop`, `/letter-flow`. The agent prompts are the single source: the CLI reuses them (`prompts.py`).

Learning rule: every correction the user gives about a CV, mail or letter is applied to the document and also written as a general rule in the agents' prompts (`.claude/agents/`, `.claude/skills/`, without personal data) and in the candidate's guides in the archive (`manual:candidate-voice`, `manual:candidate-learnings`), so the agents improve each time; when a new kind of check is needed, add an agent.

Profiles: one folder per person, `agents/data/profiles/<name>/` and `agents/output/<name>/`, chosen with `CVAGENTS_PROFILE=<name>` (`cvagents/profile.py`); data never mixes. `.claude/` (agents, skills) and the code are changed only by the owner.

Golden rules: facts come only from the archive; nothing is written without the user's OK; never invent numbers or results (code checks it); one agent = one job; personal data and keys never in git, keys never on disk.

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
