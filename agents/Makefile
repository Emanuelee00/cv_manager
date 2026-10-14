# CV Agents: `make run` starts everything.
# First time: guided path (language, AI, your details, CV, GitHub, offer). After that: runs again with the saved choices.
# OFFER=offer.txt uses another offer with the same choices.

UV := $(shell command -v uv 2>/dev/null)
SETTINGS := data/settings.json
OFFER ?=

.PHONY: run start doctor test check-uv

run: check-uv
	@if [ -f $(SETTINGS) ]; then uv run cvagents run $(OFFER); else uv run cvagents start; fi

start: check-uv
	@uv run cvagents start

doctor: check-uv
	@uv run cvagents doctor

test: check-uv
	@uv run python -m unittest discover -s tests -t .

check-uv:
ifndef UV
	@echo "uv is needed: curl -LsSf https://astral.sh/uv/install.sh | sh  (then reopen the terminal)"
	@exit 1
endif
