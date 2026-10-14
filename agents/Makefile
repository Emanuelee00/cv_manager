# CV Agents: `make run` fa partire tutto.
# Prima volta: percorso guidato (start). Dopo: rilancia con le scelte salvate (run).
# OFFER=offerta.txt per usare un'altra offerta con le stesse scelte.

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
	@echo "Serve uv: curl -LsSf https://astral.sh/uv/install.sh | sh  (poi riapri il terminale)"
	@exit 1
endif
