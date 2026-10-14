# CV Agents: `make run` installs what is missing and starts everything.
# First time: guided path (language, AI, your details, CV, GitHub, offer). After that: runs again with the saved choices.
# OFFER=offer.txt uses another offer with the same choices.

UV := $(shell command -v uv 2>/dev/null || echo $(HOME)/.local/bin/uv)
SETTINGS := data/settings.json
OFFER ?=

.PHONY: install run start doctor test

install:
	@command -v uv >/dev/null 2>&1 || [ -x $(UV) ] || curl -LsSf https://astral.sh/uv/install.sh | sh
	@command -v bun >/dev/null 2>&1 || [ -x $(HOME)/.bun/bin/bun ] || curl -fsSL https://bun.sh/install | bash
	@$(UV) sync --quiet

run: install
	@if [ -f $(SETTINGS) ]; then $(UV) run cvagents run $(OFFER); else $(UV) run cvagents start; fi

start: install
	@$(UV) run cvagents start

doctor: install
	@$(UV) run cvagents doctor

test: install
	@$(UV) run python -m unittest discover -s tests -t .
