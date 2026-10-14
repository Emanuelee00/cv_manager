# Dalla radice del progetto: `make run` fa partire il percorso dei CV (vedi agents/README.md).
.PHONY: run start doctor test

run start doctor test:
	@$(MAKE) --no-print-directory -C agents $@
